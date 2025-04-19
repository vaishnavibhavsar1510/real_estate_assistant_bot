from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader
import cloudinary.api
import faiss
import numpy as np

load_dotenv()

# MongoDB Configuration
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
client = MongoClient(MONGO_URL)
db = client.real_estate

# Async MongoDB client for FastAPI
async_client = AsyncIOMotorClient(MONGO_URL)
async_db = async_client.real_estate

# Cloudinary Configuration
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

# FAISS Vector Store Configuration
DIMENSION = 512  # CLIP embedding dimension
vector_store = faiss.IndexFlatL2(DIMENSION)

def get_vector_store():
    return vector_store

def get_db():
    return db

def get_async_db():
    return async_db 