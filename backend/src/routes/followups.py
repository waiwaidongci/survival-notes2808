from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session
from ..config.database import get_db
from ..controllers.dependencies import roles
from ..constants.roles import Role
from ..schemas.followup import FollowupAnnotation
from ..services.followup_service import annotate_followup
router=APIRouter(prefix="/followups",tags=["followups"])
@router.patch("/{eid}")
def annotate(eid:int,data:FollowupAnnotation,db:Session=Depends(get_db),user=Depends(roles(Role.ADMIN,Role.ANALYST))):return annotate_followup(db,eid,data,user)
