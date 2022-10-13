from pymongo import MongoClient


class MongoConnector:

    def get_context(self):
        return MongoClient().rastreiobot
    