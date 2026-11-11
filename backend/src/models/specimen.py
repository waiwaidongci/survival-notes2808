from sqlalchemy import String,ForeignKey
from sqlalchemy.orm import Mapped,mapped_column
from ..config.database import Base
class Specimen(Base):
    __tablename__="specimens"
    id:Mapped[int]=mapped_column(primary_key=True)
    code:Mapped[str]=mapped_column(String(80),unique=True)
    cohort_id:Mapped[int]=mapped_column(ForeignKey("test_cohorts.id"))
    material:Mapped[str]=mapped_column(String(120))
    enrolled_at:Mapped[str]=mapped_column(String(64))
