
from uuid import uuid4
import requests

ENDPOINT = "https://fl3r7z7g7r3nsdyo3bhnjggjwe0xsvsr.lambda-url.us-west-2.on.aws/"

def test_create_get_task():
    # Create a random UNIQUE user
    user_id = f"user_{uuid4().hex}"
    # Create random task content
    random_task_content = f"task content: {uuid4().hex}"

    # Call upon a helper function to create the task then test if the task is created.
    create_response = create_task(user_id, random_task_content)
    assert create_response.status_code == 200

    # Call upon a helper function to get the task id then test if it matches the created task's id.
    task_id = create_response.json()["task"]["task_id"]
    get_response = get_task(task_id)
    assert get_response.status_code == 200

    # Check if the task's content that was retrieved matches the created test content.
    task = get_response.json()
    assert task['user_id'] == user_id
    assert task['content'] == random_task_content

def test_can_list_tasks():
    user_id = f"user_{uuid4().hex}"
    # Create 3 tasks for this user.
    for i in range(3):
        create_task(user_id, f"task_{i}")
    
    # List the tasks for this user and check if it matches the length of the tasks assigned to this user by the test earlier.
    response = list_tasks(user_id)
    tasks = response.json()["tasks"]
    assert len(tasks) == 3

def test_can_update_task():
    user_id = f"user_{uuid4().hex}"
    create_response = create_task(user_id, "task content")
    task_id = create_response.json()["task"]["task_id"]

    # Update the task with new content.
    new_task_content = f"updated task content: {uuid4().hex}"
    payload = {
        "content": new_task_content,
        "task_id": task_id,
        "is_done": True,
    }
    update_task_response = update_task(payload)
    assert update_task_response.status_code == 200

    # Check if the task updated content matches the content provided by the test.
    get_task_response = get_task(task_id)
    assert get_task_response.status_code == 200
    assert get_task_response.json()['content'] == new_task_content
    assert get_task_response.json()['is_done'] == True

def test_can_delete_task():
    user_id = f"user_{uuid4().hex}"
    create_response = create_task(user_id, "task1")
    task_id = create_response.json()["task"]["task_id"]

    # Delete the task
    delete_task(task_id)

    # Check if the task is deleted as 404 Not Found
    get_task_response = get_task(task_id)
    assert get_task_response.status_code == 404

def create_task(user_id:str, content:str) -> dict:
    payload = {
        "user_id":user_id,
        "content":content,
    }
    return requests.put(f"{ENDPOINT}/create-task", json=payload)

def update_task(payload) -> dict:
    return requests.put(f"{ENDPOINT}/update-task", json=payload)

def get_task(task_id: str) -> dict:
    return requests.get(f"{ENDPOINT}/get-task/{task_id}")

def list_tasks(user_id: str) -> dict:
    return requests.get(f"{ENDPOINT}/list-tasks/{user_id}")

def delete_task(task_id: str)-> dict:
    return requests.delete(f"{ENDPOINT}/delete-task/{task_id}")