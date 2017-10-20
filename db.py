# coding:utf-8

from urllib import quote
from pymongo import MongoClient

DEBUG = False


NEW_USER = "spider"
NEW_PASSWORD = quote("")
if DEBUG:
    NEW_HOST_PORT = "公网IP"
else:
    NEW_HOST_PORT = "内网IP:27017"
NEW_DATABASE = "patianxia"
NEW_MONGO_URL = "mongodb://{0}:{1}@{2}/{3}".format(NEW_USER, NEW_PASSWORD, NEW_HOST_PORT, NEW_DATABASE)
MONGO_URL = NEW_MONGO_URL

client = MongoClient(host=MONGO_URL, maxPoolSize=1, minPoolSize=1)

