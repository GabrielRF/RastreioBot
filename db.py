from time import time
from pymongo import ASCENDING, MongoClient


client = MongoClient()
db = client.rastreiobot


def all_packages():
    return db.rastreiobot.find()


def search_package(code):
    return db.rastreiobot.find({"code": code})


def search_packages_per_user(user_id):
    user_id = str(user_id)
    return db.rastreiobot.find({"users": user_id}).sort(user_id, ASCENDING)


def package_status(code):
    return db.rastreiobot.find({"code": code})["stat"]


def package_has_user(code, user_id):
    return db.rastreiobot.find_one({
        "code": code.upper(),
        "users": user_id,
    })


def add_package(code, users, stat):
    users = users if isinstance(users, (list, tuple)) else [users]
    return db.rastreiobot.insert_one({
        "code": code.upper(),
        "users": users,
        "stat": stat,
        "time": time(),
    })


def add_user_to_package(code, user):
    return db.rastreiobot.update_one({
        "code": code.upper(),
        "$push": {"users": user,},
    })


def update_package(code, **kwargs):
    code = str(code).upper()
    return db.rastreiobot.update_one({
        "code": code,
        "$set": kwargs,
    })


def remove_user_from_package(code, user_id):
    package = search_package(code)
    users = package["users"]
    users.remove(str(user_id))
    return update_package(code, users=users)


def set_package_description(code, user_id, description=None):
    user_id = str(user_id)
    code = str(code).upper()
    description = description or code
    return db.rastreiobot.update_one({
        "code": code,
        "$set": {user_id: description},
    })


def delete_package(code):
    return db.rastreiobot.delete_one({"code": code})
