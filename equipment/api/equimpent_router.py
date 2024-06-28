import uuid

from fastapi import APIRouter
from starlette.responses import JSONResponse

from db import mongo
from equipment.logic.calc_surface_reqs import calc_areas_count
equipment_router = APIRouter()


@equipment_router.get("/surface/required/{area_id}")
async def get_surface_reqs_by_area_id(area_id: str):
    equipment_collection = mongo.db.get_collection("area_surface_requirements")
    equipment_data_cursor = equipment_collection.find({"terr_id": area_id},{"_id":0})

    surface_requirements = await equipment_data_cursor.to_list(length=10000)

    response_data = {
        "status": "ok",
        "requirements": surface_requirements
    }

    return JSONResponse(status_code=200, content=response_data)


@equipment_router.get("/surface/calc/required")
async def calc_areas_equipment():
    areas_collection = mongo.db.get_collection("territory_cards")

    all_areas_cursor = areas_collection.find({}, {"_id": 0})

    all_areas = await all_areas_cursor.to_list(length=10000)

    dem_addresses = []

    surface_requirements = []
    calc_id = str(uuid.uuid4())

    for area in all_areas:

        if "demography" in area.keys():
            dem_addresses.append(
                {
                    "terr_id": area["terr_id"],
                    "ods_sys_id": area["ods_sys_id"],
                    "area_class": area["area_class"],
                    "address": area["address"]
                }

            )

        if area["area_class"] == "super_area":
            surface_claim = {
                "terr_id": area["terr_id"],
                "requirement_id": str(uuid.uuid4()),

                "calc_id": calc_id,
                "total_surface": area['surface'],
            }

            if "demography" in area.keys():
                surface_claim["requirement_source"] = "people_count"

                people_in_area = 0
                for record in area['demography']:
                    people_in_area += record['total_people']

                surface_claim["requirements"] = calc_areas_count(people_in_area, "people_count")

            else:
                surface_claim["requirement_source"] = "auto_estimate"
                surface_claim["requirements"] = calc_areas_count(area['surface'], "auto_estimate")

            surface_requirements.append(surface_claim)

    for addr in dem_addresses:
        print(addr)

    areas_collection = mongo.db.get_collection("area_surface_requirements")
    insert_reqs_rs = await areas_collection.insert_many(surface_requirements)

    response_data = {
        "status": "ok"
    }

    return JSONResponse(status_code=200, content=response_data)


