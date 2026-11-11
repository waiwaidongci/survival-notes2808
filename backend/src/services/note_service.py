from fastapi import HTTPException
from ..models import SurvivalRun,MaintenanceNote
from ..utils.clock import now
from ..utils.serialize import record
from .audit_service import log

def list_notes(db):return [record(x) for x in db.query(MaintenanceNote).order_by(MaintenanceNote.id.desc())]
def create_note(db,data,user):
    run=db.get(SurvivalRun,data.run_id)
    if not run or run.status!="completed":raise HTTPException(409,"只能为已完成研究提交维护建议")
    row=MaintenanceNote(**data.model_dump(),owner=user.name,status="submitted")
    db.add(row);db.flush();log(db,user.email,"maintenance.submit",row.id);db.commit();return record(row)
def review_note(db,nid,data,user):
    row=db.get(MaintenanceNote,nid)
    if not row:raise HTTPException(404,"维护建议不存在")
    if row.status!="submitted":raise HTTPException(409,"已复核记录不可重复审批")
    row.status=data.status;row.review_note=data.review_note;row.reviewer=user.name;row.reviewed_at=now()
    log(db,user.email,"maintenance."+data.status,row.id);db.commit();return record(row)
