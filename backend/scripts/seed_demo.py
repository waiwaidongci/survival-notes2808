import json,random
from src.config.database import Base,engine,SessionLocal
from src.models import User,TestCohort,Specimen,FollowupEvent,SurvivalRun,MaintenanceNote
from src.utils.security import hash_password
from src.services.specimen_service import specimen_rows
from src.services.run_snapshot import build_snapshot,snapshot_hash
from src.services.survival_algorithm import analyze_snapshot
from src.services.artifact_service import dump_archive,artifact_path

def seed():
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        for role,name in [("admin","阮青 · 材料负责人"),("analyst","江栩 · 耐久研究员"),("viewer","林舟 · 维护阅读者")]:
            email=role+"@zhihe.demo"
            if not db.query(User).filter_by(email=email).first():db.add(User(email=email,name=name,role=role,password_hash=hash_password("Zhihe2026!")))
        cohorts=[]
        for code,name,process,scale,seed_value in [("ZH-A","常规封装批","常规硅胶封装",900.,73),("ZH-B","改进封装批","低应力复合封装",1200.,74)]:
            c=db.query(TestCohort).filter_by(code=code).first()
            if not c:
                c=TestCohort(code=code,name=name,process=process,description="独立灯带试件恒定环境耐久观察；右删失表示观察截止仍工作，不能当作失效。")
                db.add(c);db.flush()
            rng=random.Random(seed_value)
            for i in range(1,181):
                key=f"{code}-{i:04}";lifetime=rng.weibullvariate(scale,1.8);censor=rng.uniform(900,1450);observed=lifetime<=censor;duration=max(25.,round(min(lifetime,censor)/25)*25.)
                s=db.query(Specimen).filter_by(code=key).first()
                if not s:s=Specimen(code=key,cohort_id=c.id,material="24V展陈柔性灯带 · 500mm",enrolled_at="2026-08-01T00:00:00+00:00");db.add(s);db.flush()
                if not db.query(FollowupEvent).filter_by(specimen_id=s.id).first():db.add(FollowupEvent(specimen_id=s.id,duration_hours=duration,event_observed=observed,note="观察到光通量降至阈值，记为耐久事件。" if observed else "试验观察截止，灯带仍工作，记为右删失。"))
            db.flush();cohorts.append(c)
        if not db.query(SurvivalRun).filter_by(name="两批封装耐久 · 基准比较").first():
            a,b=cohorts
            snapshot=build_snapshot(db,a,b,.95)
            result=analyze_snapshot(snapshot)
            run=SurvivalRun(name="两批封装耐久 · 基准比较",cohort_a_id=a.id,cohort_b_id=b.id,confidence=.95,status="completed",result=result,owner="江栩 · 耐久研究员",input_snapshot=snapshot,input_hash=snapshot_hash(snapshot),artifact_path=str(artifact_path(0)));db.add(run);db.flush()
            run.artifact_path=str(artifact_path(run.id));run.artifact_hash=dump_archive(run)
            db.add(MaintenanceNote(run_id=run.id,title="基准维护观察说明",interpretation="已分开事件和删失，比较结果只反映当前试验条件，不作工艺因果保证。",recommendation="优先保留尾部在险样本观察，结合环境应力记录讨论维护窗口。",status="approved",owner="江栩 · 耐久研究员",reviewer="阮青 · 材料负责人",review_note="批准研究底稿归档；维护周期仍需现场条件复核。",reviewed_at="2026-11-01T00:00:00+00:00"))
        db.commit();print(json.dumps({m.__tablename__:db.query(m).count() for m in [User,TestCohort,Specimen,FollowupEvent,SurvivalRun,MaintenanceNote]},ensure_ascii=False))
if __name__=="__main__":seed()
