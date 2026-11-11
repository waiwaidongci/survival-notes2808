import math
from .km_algorithm import validate_observations

def logrank(group_a,group_b):
    validate_observations(group_a);validate_observations(group_b)
    event_times=sorted(set(t for t,e in group_a+group_b if e))
    observed=expected=variance=0.;table=[]
    for time in event_times:
        na=sum(t>=time for t,e in group_a);nb=sum(t>=time for t,e in group_b);n=na+nb
        da=sum(t==time and e for t,e in group_a);db=sum(t==time and e for t,e in group_b);d=da+db
        exp=d*na/n
        var=d*(na/n)*(nb/n)*(n-d)/(n-1) if n>1 else 0.
        observed+=da;expected+=exp;variance+=var
        table.append({"time":time,"risk_a":na,"risk_b":nb,"events_a":da,"events_b":db,"expected_a":exp,"variance":var})
    if variance<=1e-15:return {"estimable":False,"chi_square":None,"p_value":None,"observed_a":observed,"expected_a":expected,"variance":variance,"reason":"没有可比较事件或风险集方差为零，不能估计log-rank显著性。","event_table":table}
    chi=(observed-expected)**2/variance
    return {"estimable":True,"chi_square":chi,"p_value":math.erfc(math.sqrt(chi/2)),"observed_a":observed,"expected_a":expected,"variance":variance,"reason":"两侧log-rank；chi-square自由度1，非因果结论。","event_table":table}
