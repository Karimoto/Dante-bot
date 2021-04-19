import pymongo
import sys
import os
if not os.path.isfile("settings.py"):
	sys.exit("'settings.py' not found!")
else:
	from settings import DB_CLIENT, DB_NAME

# TODO async database connection with motor

class Database(object):

    DATABASE = None

    @staticmethod
    def initialize():
        client = pymongo.MongoClient(DB_CLIENT)
        Database.DATABASE = client[DB_NAME]
        print('DB initialization completed')
    
    @staticmethod
    def find_one(collection,query):
        return Database.DATABASE[collection].find_one(query)

    @staticmethod
    def find(collection,query):
        return Database.DATABASE[collection].find(query)

    @staticmethod
    def remove_one(collection,query):
        return Database.DATABASE[collection].remove_one(query)

    @staticmethod
    def remove_many(collection,query):
        return Database.DATABASE[collection].remove_many(query)

    @staticmethod
    def insert_one(collection,query):
        return Database.DATABASE[collection].insert_one(query)

    @staticmethod
    def update_one(collection, filter, values, upsert=True):
        return Database.DATABASE[collection].update_one(filter,values,upsert=upsert)

    @staticmethod
    def update_many(collection,query):
        return Database.DATABASE[collection].update_many(query)


if __name__=='__main__':
    
    Database.initialize()
    a = Database.find_one('guild', {})
    tmp = Database.find_one('members',filter)
    print(tmp['gxp'])
