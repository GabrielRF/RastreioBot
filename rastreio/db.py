from time import time
from pymongo import ASCENDING
from config.mongo_connector import MongoConnector

class PackagesRepository:
    
    def __init__(self):
        self.db = MongoConnector.get_context()        

    def metric_increase_package_counter(self):
        return self.db.metrics.update_one(
            {"metric": "total_packages"},
            {"$inc": {"value": 1}},
            upsert=True,
        )

    def all_packages(self):
        return self.db.rastreiobot.find()


    def search_package(self, code):
        return self.db.rastreiobot.find_one({"code": code})


    def search_packages_per_user(self, user_id):
        user_id = str(user_id)
        return self.db.rastreiobot.find({"users": user_id}).sort(user_id, ASCENDING)


    def package_status(self, code):
        return self.db.rastreiobot.find_one({"code": code})["stat"]


    def package_has_user(self, code, user_id):
        return self.db.rastreiobot.find_one({
            "code": code.upper(),
            "users": user_id,
        })


    def add_package(self, code, users, stat):
        users = users if isinstance(users, (list, tuple)) else [users]
        package = self.db.rastreiobot.insert_one({
            "code": code.upper(),
            "users": users,
            "stat": stat,
            "time": time(),
        })
        self.metric_increase_package_counter()
        return package


    def add_user_to_package(self, code, user):
        return self.db.rastreiobot.update_one(
            {"code": code.upper()},
            {"$push": {"users": user}},
        )


    def update_package(self, code, **kwargs):
        code = str(code).upper()
        return self.db.rastreiobot.update_one(
            {"code": code},
            {"$set": kwargs},
        )


    def remove_user_from_package(self, code, user_id):
        print(code)
        print(user_id)
        package = self.search_package(code)
        print(package)
        users = package["users"]
        users.remove(str(user_id))
        return self.update_package(code, users=users)


    def set_package_description(self, code, user_id, description=None):
        user_id = str(user_id)
        code = str(code).upper()
        description = description or code
        return self.db.rastreiobot.update_one(
            {"code": code},
            {"$set": {user_id: description}},
        )


    def delete_package(self,  code):
        return self.db.rastreiobot.delete_one({"code": code})
