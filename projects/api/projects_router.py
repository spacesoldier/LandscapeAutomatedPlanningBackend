
from fastapi import APIRouter
from starlette.responses import JSONResponse

from db import mongo
from projects.entities.develop_project import DevelopProject
from projects.entities.update_project import ProjectUpdate
from projects.util.util import find_items_by_list

projects_router = APIRouter()


@projects_router.get("/areas/{project_id}")
async def get_all_areas_in_project(project_id: str):

    response_data = {
        "status": "ok"
    }

    projects_collection = mongo.db.get_collection("all_projects")
    project_by_id_rs = await projects_collection.find_one({"project_id": project_id}, {"_id": 0})

    areas_id_list = []
    if project_by_id_rs is not None:
        areas_id_list = list(project_by_id_rs["develop_areas"].keys())
    else:
        response_data["status"] = "project_not_found"

    areas_collection = mongo.db.get_collection("territory_cards")
    get_areas_cursor = areas_collection.find({}, {"_id": 0})
    project_areas_rs = await get_areas_cursor.to_list(length=10000)
    project_areas = find_items_by_list(areas_id_list, project_areas_rs, "terr_id")

    print(f"found {len(areas_id_list)} areas for project_id {project_id}")

    focuses_collection = mongo.db.get_collection("area_focus")
    area_focuses_cursor = focuses_collection.find({}, {"_id":0})
    area_focuses_rs = await area_focuses_cursor.to_list(length=10000)
    project_focuses = find_items_by_list(areas_id_list, area_focuses_rs, "terr_id")

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

    inner_areas = find_items_by_list(inner_areas_ids, project_areas_rs, "terr_id")
    inner_project_focuses = find_items_by_list(inner_areas_ids, area_focuses_rs, "terr_id")
    for focus_point in inner_project_focuses:
        for f_area in inner_areas:
            if f_area["terr_id"] == focus_point["terr_id"]:
                f_area["focus"] = focus_point

    print(f"found {len(inner_areas)} inner areas for project_id {project_id}")

    for inner_area in inner_areas:
        response_data["areas"].append(inner_area)

    response_data["clusters"] = []

    return JSONResponse(status_code=200, content=response_data)


@projects_router.get("/details/{project_id}")
async def get_project_by_id(project_id: str):

    projects_collection = mongo.db.get_collection("all_projects")

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
            "develop_areas": {},
            "develop_clusters": {}
        }

    return JSONResponse(status_code=200, content=response_data)


@projects_router.post("/update")
async def update_project_status(project: ProjectUpdate):

    projects_collection = mongo.db.get_collection("all_projects")

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
                                                                        "develop_clusters": project.develop_clusters,
                                                                        "status": project.status
                                                                    }
                                                                }
                                                    )
    else:
        response_data["status"] = "not_found"
        response_data["project_id"] = project.project_id

    return JSONResponse(status_code=200, content=response_data)


@projects_router.post("/new")
async def post_new_project(project: DevelopProject):

    projects_collection = mongo.db.get_collection("all_projects")

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


@projects_router.get("/by-owner/{owner}")
async def get_projects_by_user(owner: str):
    projects_collection = mongo.db.get_collection("all_projects")

    projects_by_user_cursor = projects_collection.find({"owner": owner}, {"_id" : 0})
    projects_by_user = await projects_by_user_cursor.to_list(length=10000)

    print(f"found {len(projects_by_user)} projects owned by {owner}")

    response_data = {
        "owner": owner,
        "projects": projects_by_user
    }

    return JSONResponse(status_code=200, content=response_data)


