from pydantic import BaseModel,Field
class RunInput(BaseModel):
    name:str=Field(min_length=2,max_length=120)
    cohort_a_id:int
    cohort_b_id:int
    confidence:float=Field(default=.95,ge=.8,le=.99,allow_inf_nan=False)
