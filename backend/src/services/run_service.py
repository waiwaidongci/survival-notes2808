import csv,io
from redis import Redis
from fastapi import HTTPException
from ..models import SurvivalRun,TestCohort,MaintenanceNote
from ..config.settings import REDIS_URL
from ..utils.serialize import record
from .audit_service import log
queue=Redis.from_url(REDIS_URL,decode_responses=True)
def list_runs(db):return [record(x) for x in db.query(SurvivalRun).order_by(SurvivalRun.id.desc())]
def get_run(db,rid):
    row=db.get(SurvivalRun,rid)
    if not row:raise HTTPException(404,"耐久研究不存在")
    return row

def create_run(db,data,user):
    if data.cohort_a_id==data.cohort_b_id:raise HTTPException(422,"必须选择两批不同工艺")
    if not db.get(TestCohort,data.cohort_a_id) or not db.get(TestCohort,data.cohort_b_id):raise HTTPException(404,"工艺批次不存在")
    row=SurvivalRun(**data.model_dump(),owner=user.name)
    db.add(row);db.flush();log(db,user.email,"survival.enqueue",row.id);db.commit()
    try:queue.rpush("survival:jobs",row.id)
    except Exception:
        row.status="failed";row.error="队列不可用，请重新提交";db.commit();raise HTTPException(503,row.error)
    return record(row)
def export_run(db,rid):
    row=get_run(db,rid)
    if row.status!="completed":raise HTTPException(409,"研究尚未完成")
    if not db.query(MaintenanceNote).filter_by(run_id=rid,status="approved").first():raise HTTPException(403,"维护建议尚未经负责人确认，不能导出")
    out=io.StringIO();w=csv.writer(out);w.writerow(['cohort','time_hours','at_risk','events','censored','survival','lower','upper','input_hash'])
    for group in row.result['groups']:
        for p in group['curve']:w.writerow([group['cohort']['code']]+[p[k] for k in ['time','at_risk','events','censored','survival','lower','upper']]+[row.result['input_hash']])
    return out.getvalue()
