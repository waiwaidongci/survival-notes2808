import json
from fastapi import APIRouter,Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session
from ..config.database import get_db
from ..controllers.dependencies import current_user,roles
from ..constants.roles import Role
from ..schemas.run import RunInput
from ..services.run_service import list_runs,get_run,create_run,export_run,export_archive,run_snapshot_view,run_record
router=APIRouter(prefix="/runs",tags=["runs"])
@router.get("")
def index(db:Session=Depends(get_db),user=Depends(current_user)):return list_runs(db)
@router.get("/{rid}")
def show(rid:int,db:Session=Depends(get_db),user=Depends(current_user)):return run_record(get_run(db,rid))
@router.post("",status_code=202)
def create(data:RunInput,db:Session=Depends(get_db),user=Depends(roles(Role.ADMIN,Role.ANALYST))):return create_run(db,data,user)
@router.get("/{rid}/snapshot")
def snapshot(rid:int,db:Session=Depends(get_db),user=Depends(current_user)):return run_snapshot_view(db,rid)
@router.get("/{rid}/export")
def export(rid:int,db:Session=Depends(get_db),user=Depends(current_user)):return Response(content='﻿'+export_run(db,rid),media_type="text/csv",headers={"Content-Disposition":f'attachment; filename="survival-run-{rid}.csv"'})
@router.get("/{rid}/archive")
def archive(rid:int,db:Session=Depends(get_db),user=Depends(current_user)):
    payload=export_archive(db,rid)
    body=json.dumps(payload,ensure_ascii=False,allow_nan=False).encode("utf-8")
    return Response(content=body,media_type="application/json",headers={"Content-Disposition":f'attachment; filename="survival-run-{rid}-archive.json"'})
