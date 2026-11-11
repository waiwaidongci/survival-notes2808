from sqlalchemy import String,Text
from sqlalchemy.orm import Mapped,mapped_column
from ..config.database import Base
class TestCohort(Base):
    __tablename__="test_cohorts"
    id:Mapped[int]=mapped_column(primary_key=True)
    code:Mapped[str]=mapped_column(String(40),unique=True)
    name:Mapped[str]=mapped_column(String(100))
    process:Mapped[str]=mapped_column(String(120))
    description:Mapped[str]=mapped_column(Text)
