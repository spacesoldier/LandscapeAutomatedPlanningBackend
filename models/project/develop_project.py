from pydantic import BaseModel


class DevelopProject(BaseModel):
    project_id: str
    project_name: str
    owner: str
    develop_areas: dict
