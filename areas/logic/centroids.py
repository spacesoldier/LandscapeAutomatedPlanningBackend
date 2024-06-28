import uuid

import geopandas
from shapely import Polygon


def calc_centroids(labeled_items: list):

    centroids = []

    for area in labeled_items:
        if len(area["contour"]["coordinates"]) > 0:
            contour_points = area["contour"]["coordinates"][0]
            if len(contour_points) > 0:
                pds = geopandas.GeoSeries([Polygon(contour_points)])
                centroid = {
                    "focus_id": str(uuid.uuid4()),
                    "terr_id": area["item_id"],
                    "focus": {
                        "type": "Point",
                        "coordinates": [
                                            pds.centroid.geometry.x.values[0].item(),
                                            pds.centroid.geometry.y.values[0].item()
                                        ]
                    }
                }
                centroids.append(centroid)

    return centroids


