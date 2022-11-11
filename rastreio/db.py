from time import time
from pymongo import ASCENDING, MongoClient


client = MongoClient()
db = client.rastreiobot


def metric_increase_package_counter():
    return db.metrics.update_one(
        {"metric": "total_packages"},
        {"$inc": {"value": 1}},
        upsert=True,
    )


def all_packages():
    return db.rastreiobot.find()


def search_package(code):
    return db.rastreiobot.find_one({"code": code})


def search_packages_per_user(user_id):
    user_id = str(user_id)
    return db.rastreiobot.find({"users": user_id}).sort(user_id, ASCENDING)


def package_status(code):
    return db.rastreiobot.find_one({"code": code})["stat"]


def get_package_desc(code, user):
    return db.rastreiobot.find_one({"code": str(code)})[str(user)]


def package_has_user(code, user_id):
    return db.rastreiobot.find_one({
        "code": code.upper(),
        "users": user_id,
    })


def add_package(code, users, stat):
    users = users if isinstance(users, (list, tuple)) else [users]
    package = db.rastreiobot.insert_one({
        "code": code.upper(),
        "users": users,
        "stat": stat,
        "time": time(),
    })
    metric_increase_package_counter()
    return package


def add_user_to_package(code, user):
    return db.rastreiobot.update_one(
        {"code": code.upper()},
        {"$push": {"users": user}},
    )


def update_package(code, **kwargs):
    code = str(code).upper()
    return db.rastreiobot.update_one(
        {"code": code},
        {"$set": kwargs},
    )


def remove_user_from_package(code, user_id):
    print(code)
    print(user_id)
    package = search_package(code)
    print(package)
    users = package["users"]
    users.remove(str(user_id))
    return update_package(code, users=users)


def set_package_description(code, user_id, description=None):
    user_id = str(user_id)
    code = str(code).upper()
    description = description or code
    return db.rastreiobot.update_one(
        {"code": code},
        {"$set": {user_id: description}},
    )


def delete_package(code):
    return db.rastreiobot.delete_one({"code": code})


class User:

    @staticmethod
    def update(telegram_id, upsert=False, **kwargs):
        """Update an User in the database

        Args:
            telegram_id (str): Telegram User ID. It's casts to string to keep
                compatibility with current data.
            upsert (bool): Create if the user doesn't exist

        Kwargs:
            All keyword arguments will be sent as fields and its values to
            update the user data. The following example will update the user,
            which ID is 123, with `lang` field equals to `"pt_BR"`.


            >>> User.update(123, lang="pt_BR")

        Returns:
            An dict with User data.
        """

        telegram_id = str(telegram_id)
        kwargs["id"] = telegram_id  # Don't miss `id` if creating a new User

        return db.users.update(
            {"id": telegram_id},
            {"$set": kwargs},
            upsert=upsert,
        )
