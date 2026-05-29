from pydantic import BaseModel, Field


class TaskEnvelope(BaseModel):
    action: str
    params: dict = Field(default_factory=dict)
