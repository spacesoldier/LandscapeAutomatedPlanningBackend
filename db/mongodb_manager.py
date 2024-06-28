from motor.motor_asyncio import AsyncIOMotorClient


class MongoDBManager:

    mongodb_client: AsyncIOMotorClient
    db: {}

    def connect_to_mongo(self, db_url, db_name):
        self.mongodb_client = AsyncIOMotorClient(db_url)
        self.db = self.mongodb_client[db_name]

    def disconnect_from_mongo(self):
        self.mongodb_client.close()


