import time,json,traceback
from pathlib import Path
from .config.database import Base,engine,SessionLocal
from .models import SurvivalRun,TestCohort
from .constants.status import RunStatus
from .services.run_service import queue
from .services.specimen_service import specimen_rows
from .services.survival_algorithm import analyze_survival
from .services.audit_service import log
Base.metadata.create_all(engine);Path("/artifacts").mkdir(exist_ok=True)
while True:
    Path("/artifacts/heartbeat").write_text(str(time.time()))
    job=queue.blpop("survival:jobs",timeout=2)
    if not job:continue
    with SessionLocal() as db:
        run=db.get(SurvivalRun,int(job[1]))
        if not run or run.status!=RunStatus.QUEUED:continue
        run.status=RunStatus.RUNNING;db.commit()
        try:
            a,b=db.get(TestCohort,run.cohort_a_id),db.get(TestCohort,run.cohort_b_id)
            run.result=analyze_survival(a,b,specimen_rows(db,a.id),specimen_rows(db,b.id),run.confidence);run.status=RunStatus.COMPLETED
            Path(f"/artifacts/run-{run.id}.json").write_text(json.dumps(run.result,ensure_ascii=False));log(db,"worker","survival.completed",run.id)
        except Exception as e:run.status=RunStatus.FAILED;run.error=str(e);traceback.print_exc()
        db.commit()
