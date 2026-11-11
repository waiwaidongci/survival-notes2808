import time,traceback
from pathlib import Path
from .config.database import Base,engine,SessionLocal
from .config.settings import ARTIFACT_DIR
from .models import SurvivalRun
from .constants.status import RunStatus
from .services.job_queue import queue,JOB_QUEUE
from .services.survival_algorithm import analyze_snapshot
from .services.run_snapshot import snapshot_hash
from .services.artifact_service import dump_archive,artifact_path
from .services.recovery_service import reenqueue_stale,backfill_legacy_runs,reconcile_artifacts
from .services.audit_service import log
from .utils.clock import now
SWEEP_INTERVAL=30  # 每 30 个轮询周期做一次中断恢复与档案对账

def startup_recovery(db):
    backfilled=backfill_legacy_runs(db)
    recovered=reenqueue_stale(db)
    fixed=reconcile_artifacts(db)
    print(f"[worker] recovery: backfill={backfilled} reenqueue={recovered} reconcile={fixed}",flush=True)

def process_job(db,rid:int):
    run=db.get(SurvivalRun,rid)
    # 状态校验：只认领排队中的研究，重复消息不会重复生成结果
    if not run or run.status!=RunStatus.QUEUED:return
    if not run.input_snapshot:
        run.status=RunStatus.FAILED;run.error="研究缺少固化输入快照，无法计算";db.commit();return
    run.status=RunStatus.RUNNING;run.running_at=now();db.commit()
    try:
        # 只依据入队时冻结的快照计算，不读活数据表
        result=analyze_snapshot(run.input_snapshot)
        # 结果必须与冻结快照同一份输入（input_hash 列在旧档案回填时可能带 #legacy 后缀）
        if result["input_hash"]!=snapshot_hash(run.input_snapshot):
            raise ValueError("计算输入哈希与固化快照不一致，拒绝写入结果")
        run.result=result;run.status=RunStatus.COMPLETED;run.running_at=""
        db.flush()
        run.artifact_hash=dump_archive(run)  # 原子写入归档（快照+结果+双哈希）
        run.artifact_path=str(artifact_path(run.id))
        log(db,"worker","survival.completed",run.id);db.commit()
    except Exception as e:
        db.rollback()
        run=db.get(SurvivalRun,rid)
        if run:run.status=RunStatus.FAILED;run.error=str(e);run.running_at="";db.commit()
        traceback.print_exc()

def main():
    Base.metadata.create_all(engine);Path(ARTIFACT_DIR).mkdir(parents=True,exist_ok=True)
    with SessionLocal() as db:
        try:startup_recovery(db)
        except Exception:traceback.print_exc()
    ticks=0
    while True:
        Path(ARTIFACT_DIR,"heartbeat").write_text(str(time.time()))
        job=queue.blpop(JOB_QUEUE,timeout=2)
        if job:
            with SessionLocal() as db:
                try:process_job(db,int(job[1]))
                except Exception:traceback.print_exc()
        ticks+=1
        if ticks>=SWEEP_INTERVAL:
            ticks=0
            with SessionLocal() as db:
                try:
                    reenqueue_stale(db)
                    reconcile_artifacts(db)
                except Exception:traceback.print_exc()

if __name__=="__main__":
    main()
