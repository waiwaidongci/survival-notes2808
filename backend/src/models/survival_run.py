from sqlalchemy import ForeignKey,String,JSON,Text,Double
from sqlalchemy.orm import Mapped,mapped_column
from ..config.database import Base
from ..utils.clock import now
class SurvivalRun(Base):
    __tablename__="survival_runs"
    id:Mapped[int]=mapped_column(primary_key=True)
    name:Mapped[str]=mapped_column(String(120))
    cohort_a_id:Mapped[int]=mapped_column(ForeignKey("test_cohorts.id"))
    cohort_b_id:Mapped[int]=mapped_column(ForeignKey("test_cohorts.id"))
    confidence:Mapped[float]=mapped_column(Double,default=.95)
    status:Mapped[str]=mapped_column(String(24),default="queued")
    result:Mapped[dict]=mapped_column(JSON,default=dict)
    error:Mapped[str]=mapped_column(Text,default="")
    owner:Mapped[str]=mapped_column(String(100))
    created_at:Mapped[str]=mapped_column(String(64),default=now)
    # 入队瞬间固化的两批试件、随访与分析口径；计算只依据该快照
    input_snapshot:Mapped[dict]=mapped_column(JSON,default=dict)
    # 快照口径的稳定 SHA256，同输入重复投递复用同一份研究；
    # 可空且唯一：未回填的旧研究为 NULL（唯一索引允许多个 NULL），新研究必有哈希
    input_hash:Mapped[str|None]=mapped_column(String(64),unique=True,nullable=True,default=None)
    # /artifacts 下归档文件名与文件内容 SHA256，保证记录与文件同输入同结果
    artifact_path:Mapped[str]=mapped_column(String(255),default="")
    artifact_hash:Mapped[str]=mapped_column(String(64),default="")
    # running 状态心跳，用于中断研究的自动恢复
    running_at:Mapped[str]=mapped_column(String(64),default="")
