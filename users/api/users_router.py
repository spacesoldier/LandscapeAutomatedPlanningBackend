
from fastapi import APIRouter
from starlette.responses import JSONResponse

from db import mongo
from users.entities.user_task_state import UserTaskState

users_router = APIRouter()


@users_router.get("/tasks/status/{username}")
async def get_current_task_by_user(username: str):

    no_task = {
        "owner_id": username,
        "has_task": 0,
        "current_task_id": "",
        "current_task_status": ""
    }

    response_data = {}

    pj_owners_collection = mongo.db.get_collection("project_owners")
    project_owner_job = await pj_owners_collection.find_one({"owner_id": username}, {"_id": 0})

    if project_owner_job is not None:
        response_data = UserTaskState(**project_owner_job).model_dump()
    else:
        response_data = no_task

    return JSONResponse(status_code=200, content=response_data)


@users_router.post("/tasks/current")
async def update_user_task_details(task_state: UserTaskState):

    response_data = {
        "status": "ok",
    }

    update_result = {}

    pj_owners_collection = mongo.db.get_collection("project_owners")
    project_by_owner = await pj_owners_collection.find_one({"owner_id": task_state.owner_id})
    if project_by_owner is not None:
        update_result = await pj_owners_collection.update_one(
                                                            {"owner_id": task_state.owner_id},
                                                            {"$set": {
                                                                "has_task": task_state.has_task,
                                                                "current_task_id": task_state.current_task_id,
                                                                "current_task_status": task_state.current_task_status
                                                                }
                                                            }
                                                    )
        response_data["status"] = "updated"
    else:
        update_result = await pj_owners_collection.insert_one(task_state.model_dump())
        response_data["status"] = "new record"

    return JSONResponse(status_code=200, content=response_data)