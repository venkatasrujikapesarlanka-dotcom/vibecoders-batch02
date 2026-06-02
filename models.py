from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")

db = client["flight_ai_project"]

users_collection = db["users"]
passengers_collection = db["passengers"]