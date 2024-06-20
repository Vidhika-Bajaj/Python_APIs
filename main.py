from fastapi import FastAPI, HTTPException, Depends
from pymongo import MongoClient
from models import User
from schemas import UserCreate, UserLogin, UserLinkID
from utils import hash_password, verify_password
import os

app = FastAPI()

# MongoDB configuration
MONGO_DETAILS = os.getenv("MONGO_DETAILS", "mongodb://localhost:27017")
client = MongoClient(MONGO_DETAILS)
db = client.user_db
users_collection = db.get_collection("users")

@app.on_event("startup")
def startup_db_client():
    print("Connecting to the MongoDB database...")

@app.on_event("shutdown")
def shutdown_db_client():
    client.close()
    print("Disconnected from the MongoDB database.")

@app.post("/register", response_description="Register a new user")
async def register_user(user: UserCreate):
    user_data = user.dict()
    user_data['hashed_password'] = hash_password(user_data.pop('password'))

    if users_collection.find_one({"email": user_data["email"]}):
        raise HTTPException(status_code=400, detail="Email already registered")

    users_collection.insert_one(user_data)
    return {"message": "User registered successfully"}

@app.post("/login", response_description="Login an existing user")
async def login_user(user: UserLogin):
    user_data = users_collection.find_one({"email": user.email})

    if not user_data or not verify_password(user.password, user_data["hashed_password"]):
        raise HTTPException(status_code=400, detail="Invalid email or password")

    return {"message": "Login successful"}

@app.post("/link_id", response_description="Link an ID to a user")
async def link_id(user: UserLinkID):
    user_data = users_collection.find_one({"email": user.email})

    if not user_data:
        raise HTTPException(status_code=400, detail="User not found")

    users_collection.update_one(
        {"email": user.email},
        {"$set": {"linked_id": user.linked_id}}
    )

    return {"message": "ID linked successfully"}

@app.get("/users_with_items", response_description="Get users with their items")
async def get_users_with_items():
    users_with_items = users_collection.aggregate([
        {
            "$lookup": {
                "from": "items",
                "localField": "linked_id",
                "foreignField": "user_id",
                "as": "user_items"
            }
        }
    ])
    return list(users_with_items)

@app.delete("/delete_user/{email}", response_description="Delete a user and associated data")
async def delete_user(email: str):
    user = users_collection.find_one({"email": email})

    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    users_collection.delete_one({"email": email})
    db.items.delete_many({"user_id": user.get("linked_id")})

    return {"message": "User and associated data deleted successfully"}
