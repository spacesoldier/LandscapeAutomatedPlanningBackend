import uuid

import geopandas as gpd
from shapely.geometry import Point


def find_clusters_of_points(labeled_points: list, id_field: str, max_radius: float):

    clusters = []

    for current_point in labeled_points:

        distances = []

        id_from = current_point[id_field]

        curp_lat = current_point["focus"]["coordinates"][0]
        curp_lon = current_point["focus"]["coordinates"][1]

        point_from = Point(curp_lat,curp_lon)

        for point_to_check in labeled_points:
            ptc_lat = point_to_check["focus"]["coordinates"][0]
            ptc_lon = point_to_check["focus"]["coordinates"][1]

            id_to = point_to_check[id_field]

            if id_to != id_from:
                point_to = Point(ptc_lat,ptc_lon)

                points_df = gpd.GeoDataFrame({'geometry': [point_from, point_to]}, crs='EPSG:4326')
                points_df = points_df.to_crs("EPSG:20932")
                points_df_shft = points_df.shift()

                distance_meters = points_df.distance(points_df_shft).iloc[1]

                # print(f"distance from {id_from} to {id_to} is {distance_meters} meters")

                distances.append({
                    "from": id_from,
                    "to": id_to,
                    "distance": distance_meters
                })
        all_distances = sorted(distances, key=lambda dist: dist["distance"])

        clustered_distances = []

        for dst in all_distances:
            if dst["distance"] <= max_radius:
                clustered_distances.append(dst)
            else:
                break

        if len(clustered_distances) > 0:
            new_cluster = {
                "cluster_id": str(uuid.uuid4()),
                "cluster_points": {id_from}
            }

            for cls_dst in clustered_distances:
                new_cluster["cluster_points"].add(cls_dst["to"])
            # print(f"found {len(clustered_distances)} neighbours within {max_radius} for point {id_from}")

            found_cluster_to_join = False
            for cluster in clusters:
                if len(new_cluster["cluster_points"] & cluster["cluster_points"]) > 0:
                    cluster["cluster_points"].update(new_cluster["cluster_points"])
                    found_cluster_to_join = True
                    print(f"merged found points into cluster {cluster['cluster_id']}")
                    break

            if not found_cluster_to_join:
                clusters.append(new_cluster)

    print(f"found total {len(clusters)} clusters")

    single_points = []

    for point in labeled_points:
        point_id = point[id_field]

        point_already_in_cluster = False
        for cluster in clusters:
            if point_id in cluster["cluster_points"]:
                point_already_in_cluster = True
                break
        if not point_already_in_cluster:
            single_points.append(point_id)

    for single_point in single_points:
        clusters.append(
            {
                "cluster_id": str(uuid.uuid4()),
                "cluster_points": {single_point}
            }
        )
    return clusters


