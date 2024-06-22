import json

from fastapi import FastAPI
from starlette.responses import JSONResponse

from models.project.develop_project import DevelopProject

app = FastAPI()
from decouple import config
from motor.motor_asyncio import AsyncIOMotorClient


@app.get("/maf/territories/list")
async def list_territories():
    return {"message": "Hello World"}


@app.get("/maf/territories/details/{name}")
async def get_area_details(name: str):
    return {"message": f"Hello {name}"}


@app.get("/maf/projects/{owner}")
async def get_projects_by_user(owner: str):
    projects_collection = app.planner_db.get_collection("all_projects")

    projects_by_user_cursor = projects_collection.find({"owner": owner}, {"_id" : 0})
    projects_by_user = await projects_by_user_cursor.to_list(length=10000)

    print(f"found {len(projects_by_user)} projects owned by {owner}")

    response_data = {
        "owner": owner,
        "projects": projects_by_user
    }

    return JSONResponse(status_code=200, content=response_data)


@app.post("/maf/projects/new")
async def post_new_project(project: DevelopProject):

    projects_collection = app.planner_db.get_collection("all_projects")

    project_by_id = await projects_collection.find_one({"project_id": project.project_id})

    if project_by_id is not None:
        print(f"project {project.model_dump()} already exists")
    else:
        project_data = project.model_dump()
        project_data["status"] = "INIT"
        res = await projects_collection.insert_one(project_data)

    response_data = {
        "status": "ok"
    }

    return JSONResponse(status_code=200, content=response_data)

PLANNER_DB = "landscape_planner_data"


@app.on_event("startup")
async def connect_to_mongo():
    DB_URL = config('MONGO_URL', cast=str)
    app.mongodb_client = AsyncIOMotorClient(DB_URL)
    app.planner_db = app.mongodb_client[PLANNER_DB]


@app.on_event("shutdown")
async def disconnect_from_mongo():
    app.mongodb_client.close()


