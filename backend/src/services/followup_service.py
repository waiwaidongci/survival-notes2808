from fastapi import HTTPException
from ..models import FollowupEvent
from ..utils.serialize import record
from .audit_service import log

def annotate_followup(db,eid,data,user):
    event=db.get(FollowupEvent,eid)
    if not event:raise HTTPException(404,"随访记录不存在")
    event.note=data.note;log(db,user.email,"followup.annotate",event.id);db.commit();return record(event)
