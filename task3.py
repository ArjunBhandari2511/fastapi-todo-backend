from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from bson import ObjectId
from typing import List
from pydantic import BaseModel

# MongoDB Connection
# Replace with your MongoDB URI
client = MongoClient("mongodb+srv://arjun2511:arjun%402511@cluster0.ef5g7.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client.todo_db
tasks_collection = db.tasks

# FastAPI app instance
app = FastAPI()

@app.get("/")
def read_root():
    return {"message" : "Hello world!"}

# Middleware
app.add_middleware(
    CORSMiddleware,
    # Allow all origins, you can restrict this to specific domains in production
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods like GET, POST, PUT, DELETE
    allow_headers=["*"],  # Allow all headers
)

# Pydantic Model for Request Validation


class Task(BaseModel):
    title: str
    description: str
    completed: bool = False

# Response model that does not need ObjectId serialization


class TaskResponse(Task):
    id: str  # This represents the 'id' as a string

# Function to convert ObjectId to string before returning


def task_serializer(task):
    # Convert ObjectId to string and assign it to 'id'
    task["id"] = str(task["_id"])
    del task["_id"]  # Remove '_id' from the task as we are using 'id'
    return task

# POST: Add a new task


@app.post("/tasks", response_model=TaskResponse)
async def add_task(task: Task):
    new_task = task.dict()
    result = tasks_collection.insert_one(new_task)
    # Convert inserted ObjectId to string
    new_task["id"] = str(result.inserted_id)
    return new_task

# GET: Get all tasks


@app.get("/tasks", response_model=List[TaskResponse])
async def get_tasks():
    tasks = list(tasks_collection.find())
    return [task_serializer(task) for task in tasks]

# PUT: Update a task


@app.put("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(task_id: str, updated_task: Task):
    if not ObjectId.is_valid(task_id):
        raise HTTPException(status_code=400, detail="Invalid task ID")

    result = tasks_collection.find_one_and_update(
        {"_id": ObjectId(task_id)},
        {"$set": updated_task.dict()},
        return_document=True
    )

    if not result:
        raise HTTPException(status_code=404, detail="Task not found")

    return task_serializer(result)

# DELETE: Delete a task


@app.delete("/tasks/{task_id}", response_model=dict)
async def delete_task(task_id: str):
    if not ObjectId.is_valid(task_id):
        raise HTTPException(status_code=400, detail="Invalid task ID")

    result = tasks_collection.find_one_and_delete({"_id": ObjectId(task_id)})

    if not result:
        raise HTTPException(status_code=404, detail="Task not found")

    return {"message": "Task deleted successfully", "deleted_task": task_serializer(result)}
