from config.mongo_connector import MongoConnector


class User:
    
    def __init__(self):
        self.db = MongoConnector.get_context()  
        
    @staticmethod
    def update(self, telegram_id, upsert=False, **kwargs):
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

        return self.db.users.update(
            {"id": telegram_id},
            {"$set": kwargs},
            upsert=upsert,
        )
        