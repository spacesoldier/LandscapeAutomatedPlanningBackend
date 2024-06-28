import decouple
from fastapi import FastAPI
from starlette.responses import JSONResponse
from decouple import config
from fastapi.middleware.cors import CORSMiddleware

from areas.api.areas_router import areas_router
from db import mongo
from equipment.api.equimpent_router import equipment_router
from projects.api.projects_router import projects_router
from users.api.users_router import users_router

app = FastAPI()

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

app.include_router(areas_router, prefix='/maf/area')

app.include_router(projects_router, prefix='/maf/projects')

app.include_router(users_router, prefix='/maf/users')

app.include_router(equipment_router, prefix='/maf/equipment')


PLANNER_DB = "landscape_planner_data"


@app.on_event("startup")
async def connect_to_mongo():
    DB_URL = config('MONGO_URL', cast=str)
    # app.mongodb_client = AsyncIOMotorClient(DB_URL)
    # app.planner_db = app.mongodb_client[PLANNER_DB]
    mongo.connect_to_mongo(DB_URL, PLANNER_DB)


@app.on_event("shutdown")
async def disconnect_from_mongo():
    mongo.disconnect_from_mongo()


