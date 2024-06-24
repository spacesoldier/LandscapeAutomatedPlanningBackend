from pydantic import BaseModel


class UserTaskState(BaseModel):
    owner_id: str
    has_task: int
    current_task_id: str
    current_task_status: str
