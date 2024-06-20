# Python_APIs

To achieve the outlined objectives using FastAPI and MongoDB with PyMongo, you can follow these steps. The instructions cover setting up the environment, creating the required endpoints, and implementing the specified functionalities.

Step 1: Environment Setup
1.1 Install Required Libraries
First, ensure you have Python installed. Then, create a virtual environment and install the necessary libraries.

bash
Copy code
# Create and activate a virtual environment
python -m venv env
source env/bin/activate  # On Windows, use env\Scripts\activate

# Install required libraries
pip install fastapi uvicorn pymongo bcrypt

Step 2: Setting Up FastAPI and PyMongo

2.1 Create a FastAPI Application
Create a directory structure for your project:

css
Copy code
fastapi_mongo_project/
│
├── main.py
├── models.py
├── schemas.py
└── utils.py
2.2 Configure PyMongo
In main.py, set up the FastAPI application and configure the connection to MongoDB.

python
Copy code
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
Step 3: Create Models and Schemas
3.1 Models
In models.py, define the user model.

python
Copy code
from typing import Optional
from pydantic import BaseModel, EmailStr, Field

class User(BaseModel):
    username: str
    email: EmailStr
    hashed_password: str
    linked_id: Optional[str] = None
3.2 Schemas
In schemas.py, define the Pydantic schemas for request validation.

python
Copy code
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserLinkID(BaseModel):
    email: EmailStr
    linked_id: str
Step 4: Utility Functions
In utils.py, add functions to hash and verify passwords.

python
Copy code
import bcrypt

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
Step 5: Implement API Endpoints
5.1 Registration API
In main.py, implement the registration endpoint.

python
Copy code
@app.post("/register", response_description="Register a new user")
async def register_user(user: UserCreate):
    user_data = user.dict()
    user_data['hashed_password'] = hash_password(user_data.pop('password'))

    if users_collection.find_one({"email": user_data["email"]}):
        raise HTTPException(status_code=400, detail="Email already registered")

    users_collection.insert_one(user_data)
    return {"message": "User registered successfully"}
5.2 Login API
Implement the login endpoint.

python
Copy code
@app.post("/login", response_description="Login an existing user")
async def login_user(user: UserLogin):
    user_data = users_collection.find_one({"email": user.email})

    if not user_data or not verify_password(user.password, user_data["hashed_password"]):
        raise HTTPException(status_code=400, detail="Invalid email or password")

    return {"message": "Login successful"}
5.3 Linking ID API
Implement the linking ID endpoint.

python
Copy code
@app.post("/link_id", response_description="Link an ID to a user")
async def link_id(user: UserLinkID):
    user_data = users_collection.find_one({"email": user.email})

    if not user_data:
        raise HTTPException(status_code=400, detail="User not found")

    users_collection.update_one(
        {"email": user.email},
        {"set": {"linked_id": user.linked_id}}
    )

    return {"message": "ID linked successfully"}
5.4 Implement Joins
You can use MongoDB's $lookup for joining data from multiple collections. For this example, let's assume there's another collection named items and we want to join user data with their items.

python
Copy code
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
5.5 Chain Delete
Implement the chain delete functionality to remove a user and associated data.

python
Copy code
@app.delete("/delete_user/{email}", response_description="Delete a user and associated data")
async def delete_user(email: str):
    user = users_collection.find_one({"email": email})

    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    users_collection.delete_one({"email": email})
    db.items.delete_many({"user_id": user.get("linked_id")})

    return {"message": "User and associated data deleted successfully"}
Step 6: Running the Application
Run the FastAPI application using Uvicorn.

bash
Copy code
uvicorn main:app --reload
Your FastAPI application should now be running, and you can test the endpoints using a tool like Postman or through a web browser at http://127.0.0.1:8000.

This setup provides a comprehensive structure for a FastAPI application interacting with MongoDB, including user registration, login, linking IDs, joins, and chain delete functionality.
