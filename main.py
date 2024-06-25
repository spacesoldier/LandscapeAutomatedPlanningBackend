import json
import uuid

import geopandas
from fastapi import FastAPI
from starlette.responses import JSONResponse

from models.project.develop_project import DevelopProject
from models.project.update_project import ProjectUpdate
from models.user_tasks.user_task_state import UserTaskState

app = FastAPI()
from decouple import config
from motor.motor_asyncio import AsyncIOMotorClient

from fastapi.middleware.cors import CORSMiddleware

origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:3000",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/maf/area/all")
async def list_territories():
    projects_collection = app.planner_db.get_collection("territory_cards")
    all_areas_cursor = projects_collection.find(
                                                    {"area_class": "super_area"},
                                                    {"_id": 0}
                                                )

    all_areas = await all_areas_cursor.to_list(length=10000)

    response_data = {
        "status": "ok",
        "areas": all_areas
    }

    return JSONResponse(status_code=200, content=response_data)


@app.get("/maf/area/details/{area_id}")
async def get_area_details(area_id: str):

    response_data = {
        "status": "ok"
    }

    areas_collection = app.planner_db.get_collection("territory_cards")
    area_rs = await areas_collection.find_one(
                                                {"terr_id": area_id},
                                                {"_id": 0}
                                            )

    if area_rs is None:
        response_data["status"] = "not_found",
        response_data["area"] = {}
    else:
        response_data["area"] = area_rs

    return JSONResponse(status_code=200, content=response_data)





@app.get("/maf/area/backup/all")
async def backup_all_area_data():
    response_data = {
        "status": "ok"
    }

    areas_collection = app.planner_db.get_collection("territory_cards")
    get_areas_cursor = areas_collection.find({}, {"_id": 0})

    all_areas = await get_areas_cursor.to_list(length=10000)

    areas_collection_bckup = app.planner_db.get_collection("territory_cards_bckup2")
    bckup_rs = await areas_collection_bckup.insert_many(all_areas)

    return JSONResponse(status_code=200, content=response_data)


from shapely import Polygon
@app.get("/maf/area/calc/focuses")
async def calc_contour_focuses():
    response_data = {
        "status": "ok"
    }

    areas_collection = app.planner_db.get_collection("territory_cards")
    get_areas_cursor = areas_collection.find({}, {"_id": 0})

    all_areas = await get_areas_cursor.to_list(length=10000)

    area_centroids = []

    for area in all_areas:
        if len(area["contour"]["coordinates"]) > 0:
            contour_points = area["contour"]["coordinates"][0]
            if len(contour_points) > 0:
                pds = geopandas.GeoSeries([Polygon(contour_points)])
                centroid = {
                    "focus_id": str(uuid.uuid4()),
                    "terr_id": area["terr_id"],
                    "focus": {
                        "type": "Point",
                        "coordinates": [pds.centroid.geometry.x.values[0],pds.centroid.geometry.y.values[0]]
                    }
                }
                area_centroids.append(centroid)

    if len(area_centroids) > 0:
        areas_collection = app.planner_db.get_collection("area_focus")
        save_rs = await areas_collection.insert_many(area_centroids)

    return JSONResponse(status_code=200, content=response_data)




async def findItemsByList(item_ids: list, areas_collection):

    output = []

    if len(item_ids) > 0:

        get_areas_cursor = areas_collection.find({}, {"_id": 0})

        project_areas_rs = await get_areas_cursor.to_list(length=10000)

        for area in project_areas_rs:
            if area["terr_id"] in item_ids:
                output.append(area)

    return output


@app.get("/maf/area/by-project/{project_id}")
async def get_projects_by_user(project_id: str):

    response_data = {
        "status": "ok"
    }

    projects_collection = app.planner_db.get_collection("all_projects")
    project_by_id_rs = await projects_collection.find_one({"project_id": project_id}, {"_id": 0})

    areas_id_list = []
    if project_by_id_rs is not None:
        areas_id_list = list(project_by_id_rs["develop_areas"].keys())
    else:
        response_data["status"] = "project_not_found"

    areas_collection = app.planner_db.get_collection("territory_cards")
    project_areas = await findItemsByList(areas_id_list, areas_collection)

    print(f"found {len(areas_id_list)} areas for project_id {project_id}")

    focuses_collection = app.planner_db.get_collection("area_focus")
    project_focuses = await findItemsByList(areas_id_list, focuses_collection)

    for focus_point in project_focuses:
        for f_area in project_areas:
            if f_area["terr_id"] == focus_point["terr_id"]:
                f_area["focus"] = focus_point

    response_data["areas"] = project_areas

    # find inner areas by id
    inner_areas_ids = []
    for area in project_areas:
        if len(area["contain_areas"]) > 0:
            for inner_area in area["contain_areas"]:
                inner_areas_ids.append(inner_area)

    inner_areas = await findItemsByList(inner_areas_ids, areas_collection)
    inner_project_focuses = await findItemsByList(inner_areas_ids, focuses_collection)
    for focus_point in inner_project_focuses:
        for f_area in inner_areas:
            if f_area["terr_id"] == focus_point["terr_id"]:
                f_area["focus"] = focus_point

    print(f"found {len(inner_areas)} inner areas for project_id {project_id}")

    for inner_area in inner_areas:
        response_data["areas"].append(inner_area)

    return JSONResponse(status_code=200, content=response_data)


@app.get("/maf/user/projects/{owner}")
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

    response_data = {
        "status": "ok"
    }

    if project_by_id is not None:
        print(f"project {project.model_dump()} already exists")
        response_data["project_id"] = project.project_id
        response_data["status"] = project_by_id["status"]
    else:
        project_data = project.model_dump()
        project_data["status"] = "INIT"
        res = await projects_collection.insert_one(project_data)
        response_data["project_id"] = project.project_id
        response_data["status"] = "INIT"

    return JSONResponse(status_code=200, content=response_data)


@app.post("/maf/projects/update")
async def update_project_status(project: ProjectUpdate):

    projects_collection = app.planner_db.get_collection("all_projects")

    project_by_id = await projects_collection.find_one({"project_id": project.project_id})

    response_data = {
        "status": "ok"
    }

    if project_by_id is not None:
        print(f"update project {project.project_id} in status {project.status}")

        project_update_result = projects_collection.update_one(
                                                                {"project_id": project.project_id},
                                                                {
                                                                    "$set": {
                                                                        "develop_areas": project.develop_areas,
                                                                        "status": project.status
                                                                    }
                                                                }
                                                    )
    else:
        response_data["status"] = "not_found"
        response_data["project_id"] = project.project_id

    return JSONResponse(status_code=200, content=response_data)


@app.get("/maf/projects/{project_id}")
async def get_project_status_by_id(project_id: str):

    projects_collection = app.planner_db.get_collection("all_projects")

    response_data = {
        "status": "ok"
    }

    project_by_id = await projects_collection.find_one({"project_id": project_id}, {"_id": 0})

    if project_by_id is not None:
        response_data["project"] = project_by_id
    else:
        response_data["status"] = "not_found"
        response_data["project"] = {
            "project_id": "",
            "project_name": "",
            "owner": "",
            "develop_areas": {}
        }

    return JSONResponse(status_code=200, content=response_data)


@app.post("/maf/tasks/current")
async def assign_task_to_user(task_state: UserTaskState):

    response_data = {
        "status": "ok",
    }

    update_result = {}

    pj_owners_collection = app.planner_db.get_collection("project_owners")
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


@app.get("/maf/tasks/status/{username}")
async def get_current_task_by_user(username: str):

    no_task = {
        "owner_id": username,
        "has_task": 0,
        "current_task_id": "",
        "current_task_status": ""
    }

    response_data = {}

    pj_owners_collection = app.planner_db.get_collection("project_owners")
    project_owner_job = await pj_owners_collection.find_one({"owner_id": username}, {"_id": 0})

    if project_owner_job is not None:
        response_data = UserTaskState(**project_owner_job).model_dump()
    else:
        response_data = no_task

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


