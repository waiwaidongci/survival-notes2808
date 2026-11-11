"""研究恢复与档案对账。

- worker 启动/周期扫描：running 超时（中断）的研究重新入队自动恢复；
- 快照功能上线前的旧研究：按当前活数据回填快照与输入哈希（一次性兜底）；
- 已完成研究的归档文件缺失或哈希不符：按数据库结果重建，保证记录与文件一致。
"""
import logging
from datetime import datetime,timezone
from ..models import SurvivalRun,TestCohort
from .run_snapshot import build_snapshot,snapshot_hash,STALE_RUNNING_SECONDS
from .job_queue import enqueue_job
from .artifact_service import ensure_artifact,artifact_path,verify_artifact
logger=logging.getLogger("survival.recovery")


def _parse_ts(value:str):
    try:return datetime.fromisoformat(value)
    except (TypeError,ValueError):return None


def reenqueue_stale(db)->list[int]:
    """把中断在 running 的研究重置为 queued 并重新投递。"""
    recovered=[]
    current=datetime.now(timezone.utc)
    for run in db.query(SurvivalRun).filter(SurvivalRun.status=="running").all():
        started=_parse_ts(run.running_at)
        if started is None or (current-started).total_seconds()>STALE_RUNNING_SECONDS:
            run.status="queued";run.running_at="";run.error=""
            try:
                enqueue_job(run.id);recovered.append(run.id)
            except Exception:logger.exception("重新投递研究 %s 失败",run.id)
    if recovered:db.commit()
    return recovered


def backfill_legacy_runs(db)->list[int]:
    """为没有快照的旧研究补冻结输入；已完成的同时重建归档。

    旧研究可能输入完全相同，而 input_hash 有唯一约束：最早一条保留规范哈希，
    其余追加 #legacy-{id} 后缀，历史档案全部可查，新研究仍对规范哈希去重。
    """
    backfilled=[];used_hashes={h for (h,) in db.query(SurvivalRun.input_hash).all() if h}
    for run in db.query(SurvivalRun).order_by(SurvivalRun.id).all():
        if run.input_snapshot:continue
        a=db.get(TestCohort,run.cohort_a_id);b=db.get(TestCohort,run.cohort_b_id)
        if not a or not b:
            logger.warning("研究 %s 的批次已不存在，无法回填快照",run.id);continue
        snapshot=build_snapshot(db,a,b,run.confidence)
        canonical=snapshot_hash(snapshot)
        digest=canonical
        if digest in used_hashes:digest=f"{canonical}#legacy-{run.id}"
        used_hashes.add(digest)
        run.input_snapshot=snapshot
        run.input_hash=digest
        if run.status=="completed" and run.result:
            # 归档记录规范哈希，保持与结果内 input_hash 一致、历史可复核
            run.result["input_hash"]=canonical
            ensure_artifact(run)  # 按数据库结果原子重建归档并回写 artifact_hash/path
        backfilled.append(run.id)
    if backfilled:db.commit()
    return backfilled


def reconcile_artifacts(db)->list[int]:
    """已完成研究归档文件与数据库对账，缺失/不符即按数据库结果重建。"""
    fixed=[]
    for run in db.query(SurvivalRun).filter(SurvivalRun.status=="completed").all():
        if not run.input_snapshot:continue
        if not verify_artifact(run):  # 文件缺失或内容哈希不符
            ensure_artifact(run)
            run.artifact_path=str(artifact_path(run.id));fixed.append(run.id)
    if fixed:db.commit()
    return fixed
