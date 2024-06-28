
calc_area_by_people_count = {
    "area_types": [
        {
            "area_type": "playground",
            "area_type_name": "Детская площадка",
            "categories": [
                            {
                                "cat_type": "kids03",
                                "cat_name": "Дети 0-3 года",
                                "separate": True,
                                "calc_area": lambda total_people: total_people*0.5,
                                "min_area": 50
                            },
                            {
                                "cat_type": "kids37",
                                "cat_name": "Дети 3-7 лет",
                                "separate": False,
                                "calc_area": lambda total_people: total_people*0.5,
                                "min_area": 100
                            },
                            {
                                "cat_type": "kids714",
                                "cat_name": "Дети 7-14 лет",
                                "separate": False,
                                "calc_area": lambda total_people: total_people * 0.5,
                                "min_area": 200
                            },

                        ]
        },
        {
            "area_type": "workout",
            "area_type_name": "Спорт",
            "categories": [
                                {
                                    "cat_type": "teens_1518",
                                    "cat_name": "Подростки",
                                    "separate": False,
                                    "calc_area": lambda total_people: total_people*0.7,
                                    "min_area": 100
                                },
                                {
                                    "cat_type": "adults",
                                    "cat_name": "Взрослые",
                                    "separate": False,
                                    "calc_area": lambda total_people: total_people*0.7,
                                    "min_area": 100
                                }
                            ]
        },
        {
            "area_type": "rest",
            "area_type_name": "Тихий отдых",
            "categories": [
                                {
                                    "cat_type": "adults",
                                    "cat_name": "Взрослые",
                                    "separate": False,
                                    "calc_area": lambda total_people: total_people*0.3,
                                    "min_area": 50
                                }
                            ]
        }
    ]

}

calc_area_by_surface = {
    "area_types": [
        {
            "area_type": "playground",
            "area_type_name": "Детская площадка",
            "categories": [
                            {
                                "cat_type": "kids03",
                                "cat_name": "Дети 0-3 года",
                                "age_from": 0,
                                "age_to": 3,
                                "separate": True,
                                "calc_area": lambda surface: surface * 0.25 * 0.2,
                                "min_area": 50
                            },
                            {
                                "cat_type": "kids37",
                                "cat_name": "Дети 3-7 лет",
                                "age_from": 4,
                                "age_to": 7,
                                "separate": False,
                                "calc_area": lambda surface: surface * 0.25 * 0.2,
                                "min_area": 100
                            },
                            {
                                "cat_type": "kids714",
                                "cat_name": "Дети 7-14 лет",
                                "separate": False,
                                "calc_area": lambda surface: surface * 0.25 * 0.2,
                                "min_area": 200
                            },

                        ]
        },
        {
            "area_type": "workout",
            "area_type_name": "Спорт",
            "categories": [
                                {
                                    "cat_type": "teens_1518",
                                    "cat_name": "Подростки",
                                    "separate": False,
                                    "calc_area": lambda surface: surface * 0.25 * 0.2,
                                    "min_area": 100
                                },
                                {
                                    "cat_type": "adults",
                                    "cat_name": "Взрослые",
                                    "separate": False,
                                    "calc_area": lambda surface: surface*0.1,
                                    "min_area": 100
                                }
                            ]
        },
        {
            "area_type": "rest",
            "area_type_name": "Тихий отдых",
            "categories": [
                                {
                                    "cat_type": "adults",
                                    "cat_name": "Взрослые",
                                    "separate": False,
                                    "calc_area": lambda surface: surface*0.1,
                                    "min_area": 50
                                }
                            ]
        }
    ]

}

calc_method = {
    "people_count": calc_area_by_people_count,
    "auto_estimate": calc_area_by_surface
}


def calc_areas_count(parameter, mode):

    requirements = []

    requirements_estimation_method = calc_method[mode]

    for area_type in requirements_estimation_method["area_types"]:
        area_type_req = {
            "area_type":  area_type["area_type"],
            "area_type_name": area_type["area_type_name"],
            "categories": []
        }
        for area_cat in area_type["categories"]:
            area_cat_req = {
                "cat_type": area_cat["cat_type"],
                "cat_name": area_cat["cat_name"],
                "separate": area_cat["separate"]
            }
            surface_req = area_cat["calc_area"](parameter)
            if surface_req < area_cat["min_area"]:
                surface_req = area_cat["min_area"]
            area_cat_req["surface_req"] = surface_req
            area_type_req["categories"].append(area_cat_req)

        requirements.append(area_type_req)

    return requirements



