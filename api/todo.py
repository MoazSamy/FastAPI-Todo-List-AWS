import os
import time
from uuid import uuid4
from typing import Optional

from fastapi import FastAPI, HTTPException
# Mangum is the bridge that makes AWS Lambda understand FastAPIs
from mangum import Mangum
from pydantic import BaseModel

# Already exists on AWS Lambda
import boto3
from boto3.dynamodb.conditions import Key


app = FastAPI()
handler = Mangum(app)

# The data model
class PutTaskRequest(BaseModel):
    content: str
    user_id: Optional[str] = None
    task_id: Optional[str] = None
    is_done: bool = False

class UpdateTaskRequest(BaseModel):
    content: Optional[str] = None
    task_id: str
    is_done: Optional[bool] = None

# Intializing the fastAPI app
@app.get("/")
def root():
    return {"message":"Hello World from Todo API"}

# Creating task endpoint
@app.put("/create-task")
async def create_task(put_task_request: PutTaskRequest):
    created_time = int(time.time())
    # Initialize the new item object
    item ={
        "user_id": put_task_request.user_id,
        "content": put_task_request.content,
        "is_done": False,
        "created_time": created_time,
        "task_id": f"task_{uuid4().hex}",
        "ttl": int(created_time + 86400), # Task to expire after 24 hours.
    }

    
    # Put into the table
    table = _get_table()
    table.put_item(Item=item)
    return {"task": item}

# Getting a task using the task id
@app.get("/get-task/{task_id}")
async def get_task(task_id:str):
    # Get the task from the table
    table = _get_table()
    response = table.get_item(Key={"task_id": task_id})
    item = response.get("Item")
    if not item:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found.")
    return item

# Retrieving list of tasks related to a specific user_id
@app.get("/list-tasks/{user_id}")
async def list_tasks(user_id: str):
    table = _get_table()
    response = table.query(
        IndexName="user-index",
        KeyConditionExpression=Key("user_id").eq(user_id),
        # DESC = False, ASC = True
        ScanIndexForward=False,
        Limit=10,
    )
    tasks = response.get("Items")
    return {"tasks": tasks}

# Updating a task
@app.put("/update-task")
async def update_task(update_task_request: UpdateTaskRequest):
    table = _get_table()
    if (update_task_request.content is not None) and (update_task_request.is_done is not None):
        table.update_item(
            Key={"task_id": update_task_request.task_id},
            UpdateExpression="SET content = :content, is_done = :is_done",
            ExpressionAttributeValues={
                ":content": update_task_request.content,
                ":is_done": update_task_request.is_done,
            },
            ReturnValues="ALL_NEW",
        )
    elif (update_task_request.content is not None) and (update_task_request.is_done is None):
        table.update_item(
            Key={"task_id": update_task_request.task_id},
            UpdateExpression="SET content = :content",
            ExpressionAttributeValues={
                ":content": update_task_request.content,
            },
            ReturnValues="ALL_NEW",
        )
    elif (update_task_request.content is None) and (update_task_request.is_done is not None):
        table.update_item(
            Key={"task_id": update_task_request.task_id},
            UpdateExpression="SET is_done = :is_done",
            ExpressionAttributeValues={
                ":is_done": update_task_request.is_done,
            },
            ReturnValues="ALL_NEW",
        )
    return {"updated_task_id": update_task_request.task_id}

# Deleting a task
@app.delete("/delete-task/{task_id}")
async def delete_task(task_id: str):
    table = _get_table()
    table.delete_item(
        Key={"task_id": task_id},
    )
    return {"deleted_task_id": task_id}

# Retrieving an instance of the table
def _get_table():
    table_name = os.environ.get("TABLE_NAME")
    return boto3.resource("dynamodb").Table(table_name)