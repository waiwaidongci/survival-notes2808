from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session
from ..config.database import get_db
from ..controllers.dependencies import current_user
from ..schemas.cohort import CohortOutput
from ..schemas.specimen import SpecimenOutput
from ..services.cohort_service import list_cohorts
from ..services.specimen_service import specimen_rows
router=APIRouter(prefix="/cohorts",tags=["cohorts"])
@router.get("",response_model=list[CohortOutput])
def index(db:Session=Depends(get_db),user=Depends(current_user)):return list_cohorts(db)
@router.get("/{cid}/specimens",response_model=list[SpecimenOutput])
def specimens(cid:int,db:Session=Depends(get_db),user=Depends(current_user)):return specimen_rows(db,cid)
