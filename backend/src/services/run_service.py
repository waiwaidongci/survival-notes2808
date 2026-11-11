import csv,io
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from ..models import SurvivalRun,TestCohort,MaintenanceNote
from ..utils.serialize import record
from .audit_service import log
from .job_queue import queue,ENQUEUE_LOCK,enqueue_job
from .run_snapshot import build_snapshot,snapshot_hash,snapshot_summary
from .artifact_service import read_archive,verify_artifact

def run_record(row,*,with_snapshot=False):
    data=record(row)
    if not with_snapshot:data["input_snapshot"]={}  # 列表不携带完整快照，需要时走 /runs/{id}/snapshot
    return data

def list_runs(db):
    return [run_record(x) for x in db.query(SurvivalRun).order_by(SurvivalRun.id.desc())]

def get_run(db,rid):
    row=db.get(SurvivalRun,rid)
    if not row:raise HTTPException(404,"耐久研究不存在")
    return row

def _reuse(db,row,user,action):
    """复用既有研究记录：排队中的补一次幂等投递，失败的重置后重投。"""
    if row.status=="failed":
        row.status="queued";row.error="";row.running_at="";action="survival.retry"
    if row.status=="queued":
        try:enqueue_job(row.id)
        except Exception:raise HTTPException(503,"队列不可用，请重新提交")
    log(db,user.email,action,row.id);db.commit()
    return run_record(row)

def create_run(db,data,user):
    if data.cohort_a_id==data.cohort_b_id:raise HTTPException(422,"必须选择两批不同工艺")
    a=db.get(TestCohort,data.cohort_a_id);b=db.get(TestCohort,data.cohort_b_id)
    if not a or not b:raise HTTPException(404,"工艺批次不存在")
    # 排队瞬间固化两批试件、随访（含备注）与分析口径
    snapshot=build_snapshot(db,a,b,data.confidence)
    input_hash=snapshot_hash(snapshot)
    lock=queue.lock(ENQUEUE_LOCK,timeout=10,blocking_timeout=10)
    try:acquired=lock.acquire(blocking=True)
    except Exception:acquired=False
    try:
        if acquired:
            # 同输入的研究直接复用：重复投递不重复生成结果，失败研究则重置重跑
            existing=db.query(SurvivalRun).filter_by(input_hash=input_hash).order_by(SurvivalRun.id.desc()).first()
            if existing:return _reuse(db,existing,user,"survival.deduplicated")
        row=SurvivalRun(name=data.name,cohort_a_id=a.id,cohort_b_id=b.id,confidence=data.confidence,owner=user.name,input_snapshot=snapshot,input_hash=input_hash)
        try:
            db.add(row);db.flush();db.commit()
        except IntegrityError:
            # 并发下唯一索引兜底：回滚后取已存在的同输入研究复用/重试
            db.rollback()
            existing=db.query(SurvivalRun).filter_by(input_hash=input_hash).order_by(SurvivalRun.id.desc()).first()
            if existing:return _reuse(db,existing,user,"survival.deduplicated")
            raise HTTPException(409,"研究正在创建中，请稍后重试")
        log(db,user.email,"survival.enqueue",row.id)
        try:
            db.commit();enqueue_job(row.id)
        except Exception:
            row.status="failed";row.error="队列不可用，请重新提交";db.commit();raise HTTPException(503,row.error)
        return run_record(row)
    finally:
        if acquired:
            try:lock.release()
            except Exception:pass

def _approved(db,rid):
    return db.query(MaintenanceNote).filter_by(run_id=rid,status="approved").first()

def export_run(db,rid):
    row=get_run(db,rid)
    if row.status!="completed":raise HTTPException(409,"研究尚未完成")
    if not _approved(db,rid):raise HTTPException(403,"维护建议尚未经负责人确认，不能导出")
    out=io.StringIO();w=csv.writer(out);w.writerow(['cohort','time_hours','at_risk','events','censored','survival','lower','upper','input_hash'])
    for group in row.result['groups']:
        for p in group['curve']:w.writerow([group['cohort']['code']]+[p[k] for k in ['time','at_risk','events','censored','survival','lower','upper']]+[row.result['input_hash']])
    return out.getvalue()

def export_archive(db,rid):
    """下载完整归档（固化输入+结果+双哈希），同样要求研究已获批。"""
    row=get_run(db,rid)
    if row.status!="completed":raise HTTPException(409,"研究尚未完成")
    if not _approved(db,rid):raise HTTPException(403,"维护建议尚未经负责人确认，不能导出")
    return read_archive(row)

def run_snapshot_view(db,rid):
    row=get_run(db,rid)
    if not row.input_snapshot:raise HTTPException(409,"该研究创建于快照功能上线前，暂无可还原输入")
    return {"run_id":row.id,"input_hash":row.input_hash,"artifact_path":row.artifact_path,"artifact_verified":verify_artifact(row) if row.status=="completed" else None,"snapshot":snapshot_summary(row.input_snapshot)}
