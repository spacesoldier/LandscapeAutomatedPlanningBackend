from functools import reduce

import geopandas
from fastapi import APIRouter
from shapely import Polygon
from starlette.responses import JSONResponse

from areas.logic.centroids import calc_centroids
from areas.logic.clustering import find_clusters_of_points
from db import mongo

areas_router = APIRouter()


@areas_router.get("/calc/focuses")
async def calc_contour_focuses():
    response_data = {
        "status": "ok"
    }

    areas_collection = mongo.db.get_collection("territory_cards")
    get_areas_cursor = areas_collection.find({}, {"_id": 0})

    all_areas = await get_areas_cursor.to_list(length=10000)

    contours = list(map(lambda area: {"item_id": area["terr_id"], "contour": area["contour"]}, all_areas))

    area_centroids = calc_centroids(contours)

    if len(area_centroids) > 0:
        areas_collection = mongo.db.get_collection("area_focus")
        save_rs = await areas_collection.insert_many(area_centroids)

    return JSONResponse(status_code=200, content=response_data)


@areas_router.get("/calc/clusters")
async def calc_areas_clusters():
    areas_collection = mongo.db.get_collection("territory_cards")
    get_areas_cursor = areas_collection.find({"area_class": "super_area"}, {"_id": 0, "terr_id": 1})
    super_areas = await get_areas_cursor.to_list(length=10000)

    super_areas_id_list = list(map(lambda ar: ar["terr_id"], super_areas))

    focuses_collection = mongo.db.get_collection("area_focus")
    all_focuses_cursor = focuses_collection.find({"terr_id": {"$in": super_areas_id_list}}, {"_id": 0})
    all_focuses = await all_focuses_cursor.to_list(length=10000)

    found_clusters = find_clusters_of_points(all_focuses, "terr_id", 1200.00)

    clusters = []

    clustered_areas_cursor = areas_collection.find({"terr_id": {"$in": super_areas_id_list}}, {"_id": 0})
    super_areas_list = await clustered_areas_cursor.to_list(length=10000)
    super_areas_dict = {}
    for area in super_areas_list:
        super_areas_dict[area["terr_id"]] = area

    focus_dict = {}
    for focus in all_focuses:
        focus_dict[focus["terr_id"]] = focus["focus"]["coordinates"]

    for cluster in found_clusters:
        new_cluster = {
            "cluster_id": cluster["cluster_id"],
            "cluster_areas": []
        }
        for point in cluster["cluster_points"]:
            new_cluster_area = {
                "terr_id": point,
                "ods_sys_id": super_areas_dict[point]["ods_sys_id"],
                "address": super_areas_dict[point]["address"],
                "focus": focus_dict[point]
            }
            new_cluster["cluster_areas"].append(new_cluster_area)
        if len(new_cluster["cluster_areas"]) == 1 or len(new_cluster["cluster_areas"]) == 2:
            new_cluster["center"] = {
                "type": "Point",
                "coordinates": new_cluster["cluster_areas"][0]["focus"]
            }
        else:
            if len(new_cluster["cluster_areas"]) > 2:
                poly_coords = []
                for terr in new_cluster["cluster_areas"]:
                    poly_coords.append(terr["focus"])
                poly_coords.append(new_cluster["cluster_areas"][0]["focus"])
                pds = geopandas.GeoSeries([Polygon(poly_coords)])
                new_cluster["center"] = {
                    "type": "Point",
                    "coordinates": [
                        pds.centroid.geometry.x.values[0].item(),
                        pds.centroid.geometry.y.values[0].item()
                    ]
                }
        clusters.append(new_cluster)

    clusters_collection = mongo.db.get_collection("area_clusters")
    clusters_save_rs = await clusters_collection.insert_many(clusters)

    response_data = {
        "status": "ok"
    }

    return JSONResponse(status_code=200, content=response_data)


@areas_router.get("/clusters/all")
async def list_area_clusters():
    clusters_collection = mongo.db.get_collection("area_clusters")
    all_clusters_cursor = clusters_collection.find({}, {"_id": 0})
    all_clusters = await all_clusters_cursor.to_list(length=10000)

    response_data = {
        "status": "ok",
        "clusters": all_clusters
    }

    return JSONResponse(status_code=200, content=response_data)


@areas_router.get("/by-cluster/{cluster_id}")
async def get_areas_by_cluster(cluster_id: str):
    clusters_collection = mongo.db.get_collection("area_clusters")
    cluster = await clusters_collection.find_one({"cluster_id": cluster_id}, {"_id": 0})

    area_ids = list(map(lambda ar: ar["terr_id"], cluster["cluster_areas"]))

    areas_collection = mongo.db.get_collection("territory_cards")
    cluster_super_areas_cursor = areas_collection.find({"terr_id": {"$in": area_ids}}, {"_id": 0})

    cluster_super_areas = await cluster_super_areas_cursor.to_list(length=10000)

    cluster_inner_areas_ids = []

    for sup_area in cluster_super_areas:
        cluster_inner_areas_ids.extend(sup_area["contain_areas"])

    cluster_inner_areas_cursor = areas_collection.find({"terr_id": {"$in": cluster_inner_areas_ids}}, {"_id": 0})
    cluster_inner_areas = await cluster_inner_areas_cursor.to_list(length=10000)

    output_areas = []
    output_areas.extend(cluster_super_areas)
    output_areas.extend(cluster_inner_areas)

    response_data = {
        "status": "ok",
        "areas": output_areas
    }

    return JSONResponse(status_code=200, content=response_data)


@areas_router.get("/all")
async def list_territories():
    areas_collection = mongo.db.get_collection("territory_cards")
    all_areas_cursor = areas_collection.find(
                                                    {"area_class": "super_area"},
                                                    {"_id": 0}
                                                )

    all_areas = await all_areas_cursor.to_list(length=10000)

    response_data = {
        "status": "ok",
        "areas": all_areas
    }

    return JSONResponse(status_code=200, content=response_data)


@areas_router.get("/details/{area_id}")
async def get_area_details(area_id: str):

    response_data = {
        "status": "ok"
    }

    areas_collection = mongo.db.get_collection("territory_cards")
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


@areas_router.get("/backup/all")
async def backup_all_area_data():
    response_data = {
        "status": "ok"
    }

    areas_collection = mongo.db.get_collection("territory_cards")
    get_areas_cursor = areas_collection.find({}, {"_id": 0})

    all_areas = await get_areas_cursor.to_list(length=10000)

    areas_collection_bckup = mongo.db.get_collection("territory_cards_bckup2")
    bckup_rs = await areas_collection_bckup.insert_many(all_areas)

    return JSONResponse(status_code=200, content=response_data)


