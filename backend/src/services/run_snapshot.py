"""研究入队时的输入固化。

研究排队瞬间把两批试件、终态随访（含当时备注）与分析口径整体冻结为快照，
后续随访补备注只改活数据表，不影响已固化研究；worker 只读取快照计算。
"""
from ..models import TestCohort
from ..config.settings import ARTIFACT_DIR
from ..utils.fingerprint import fingerprint
from .specimen_service import specimen_rows

METHOD_VERSION = "km-loglog-logrank-v1"
RISK_TIMES = [400, 800, 1200]
TIME_UNIT = "hours"
# 单 worker 顺序消费；超过此时长仍 running 的研究视为中断，需要重新入队。
STALE_RUNNING_SECONDS = 600


def cohort_info(cohort: TestCohort) -> dict:
    return {"id": cohort.id, "code": cohort.code, "name": cohort.name, "process": cohort.process}


def build_snapshot(db, cohort_a: TestCohort, cohort_b: TestCohort, confidence: float) -> dict:
    """排队时点的完整输入快照，按试件 code 稳定排序后冻结。"""
    return {
        "method_version": METHOD_VERSION,
        "confidence": confidence,
        "time_unit": TIME_UNIT,
        "risk_times": list(RISK_TIMES),
        "captured_at_note": "研究入队时冻结；之后随访备注与档案修订不改变本快照。",
        "groups": [
            {"cohort": cohort_info(cohort_a), "rows": specimen_rows(db, cohort_a.id)},
            {"cohort": cohort_info(cohort_b), "rows": specimen_rows(db, cohort_b.id)},
        ],
    }


def canonical_payload(snapshot: dict) -> dict:
    """去掉运行期元数据（如冻结时间说明），保证同输入恒同哈希。"""
    return {
        "method": snapshot["method_version"],
        "groups": snapshot["groups"],
        "confidence": snapshot["confidence"],
        "risk_times": snapshot["risk_times"],
        "time_unit": snapshot["time_unit"],
    }


def snapshot_hash(snapshot: dict) -> str:
    return fingerprint(canonical_payload(snapshot))


def snapshot_summary(snapshot: dict) -> dict:
    return {
        "method_version": snapshot["method_version"],
        "confidence": snapshot["confidence"],
        "time_unit": snapshot["time_unit"],
        "risk_times": list(snapshot["risk_times"]),
        "groups": [
            {
                "cohort": g["cohort"],
                "specimens": len(g["rows"]),
                "events": sum(1 for r in g["rows"] if r["event_observed"]),
                "censored": sum(1 for r in g["rows"] if not r["event_observed"]),
            }
            for g in snapshot["groups"]
        ],
    }
