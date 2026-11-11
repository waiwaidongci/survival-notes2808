from ..models import TestCohort,Specimen,FollowupEvent
from ..utils.serialize import record

def list_cohorts(db):
    result=[]
    for c in db.query(TestCohort).order_by(TestCohort.code):
        events=db.query(FollowupEvent).join(Specimen).filter(Specimen.cohort_id==c.id).all()
        result.append(dict(record(c),specimen_count=len(events),events=sum(x.event_observed for x in events),censored=sum(not x.event_observed for x in events)))
    return result
