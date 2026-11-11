from .km_algorithm import kaplan_meier
from .logrank_algorithm import logrank
from ..utils.fingerprint import fingerprint
from .run_snapshot import canonical_payload

def analyze_snapshot(snapshot):
    """完全基于入队时冻结的快照计算，不访问活数据表。

    补写的随访备注只影响之后新建的研究，不改变本研究的输入与结果。
    """
    groups_frozen=snapshot["groups"];confidence=snapshot["confidence"]
    if groups_frozen[0]["cohort"]["id"]==groups_frozen[1]["cohort"]["id"]:
        raise ValueError("必须选择两批不同工艺")
    groups=[];observations=[]
    for frozen in groups_frozen:
        rows=sorted(frozen["rows"],key=lambda x:x["code"])
        if len({r["code"] for r in rows})!=len(rows):raise ValueError("同组试件编号重复")
        obs=[(r["duration_hours"],r["event_observed"]) for r in rows]
        observations.append(obs)
        groups.append({"cohort":frozen["cohort"],**kaplan_meier(obs,confidence)})
    comparison=logrank(observations[0],observations[1])
    input_hash=fingerprint(canonical_payload(snapshot))
    return {"groups":groups,"logrank":comparison,"confidence":confidence,"time_unit":"小时","input_hash":input_hash,"method_version":snapshot["method_version"],"interpretation":"两批耐久分布存在统计差异；结合删失与工艺条件审阅" if comparison['estimable'] and comparison['p_value']<.05 else "尚无足够差异证据；不能据此认定两批等效" if comparison['estimable'] else "事件信息不足，log-rank不可估计","assumptions":"独立试件、非信息性右删失；同一时点事件先计入风险集，再移除事件与删失。区间是逐点区间，不是同时置信带；比较为关联研究，不自动决定维护周期。"}

def analyze_survival(cohort_a,cohort_b,rows_a,rows_b,confidence=.95):
    """保留给 seed/旧调用的便捷封装：先组快照再走同一条计算路径。"""
    snapshot={"method_version":"km-loglog-logrank-v1","confidence":confidence,"time_unit":"hours","risk_times":[400,800,1200],"groups":[{"cohort":{"id":cohort_a.id,"code":cohort_a.code,"name":cohort_a.name,"process":cohort_a.process},"rows":rows_a},{"cohort":{"id":cohort_b.id,"code":cohort_b.code,"name":cohort_b.name,"process":cohort_b.process},"rows":rows_b}]}
    return analyze_snapshot(snapshot)
