from sqlalchemy import ForeignKey,Text,Double
from sqlalchemy.orm import Mapped,mapped_column
from ..config.database import Base
class FollowupEvent(Base):
    __tablename__="followup_events"
    id:Mapped[int]=mapped_column(primary_key=True)
    specimen_id:Mapped[int]=mapped_column(ForeignKey("specimens.id"),unique=True)
    duration_hours:Mapped[float]=mapped_column(Double)
    event_observed:Mapped[bool]
    note:Mapped[str]=mapped_column(Text)
