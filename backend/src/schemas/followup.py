from pydantic import BaseModel,Field
class FollowupAnnotation(BaseModel):
    note:str=Field(min_length=8,max_length=1500)
