from pydantic import BaseModel
class CohortOutput(BaseModel):
    id:int
    code:str
    name:str
    process:str
    description:str
    specimen_count:int
    events:int
    censored:int
