from pydantic import BaseModel


class ProjectBase(BaseModel):
    pass


class ProjectTraining(ProjectBase):
    id: str

    class Config:
        orm_mode = True
