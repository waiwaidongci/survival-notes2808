from sqlalchemy import ForeignKey,String,Text
from sqlalchemy.orm import Mapped,mapped_column
from ..config.database import Base
from ..utils.clock import now
class MaintenanceNote(Base):
    __tablename__="maintenance_notes"
    id:Mapped[int]=mapped_column(primary_key=True)
    run_id:Mapped[int]=mapped_column(ForeignKey("survival_runs.id"))
    title:Mapped[str]=mapped_column(String(120))
    interpretation:Mapped[str]=mapped_column(Text)
    recommendation:Mapped[str]=mapped_column(Text)
    status:Mapped[str]=mapped_column(String(24),default="submitted")
    owner:Mapped[str]=mapped_column(String(100))
    reviewer:Mapped[str]=mapped_column(String(100),default="")
    review_note:Mapped[str]=mapped_column(Text,default="")
    created_at:Mapped[str]=mapped_column(String(64),default=now)
    reviewed_at:Mapped[str]=mapped_column(String(64),default="")
