# GET /index/:id -Retrieves an index by it's ID
# POST /index - Creates a new index
# PUT /index/:id - Updates an index by it;s ID
# DELETE /index/:id - Deletes an index by it's ID
# GET /index/:id/query - Queries an index by it's ID
# GET /index/compare - Returns a dictionary of index type: response

import fastapi
import redis
from pydantic import BaseModel
import uuid
import logging
import llama_index

logging.basicConfig(level=logging.INFO)

redis_client = redis.Redis(host='localhost', port=6379, db=0)
app = fastapi.FastAPI()


class Index(BaseModel):
    index: str


@app.get("/index/{idx}")
def read_index(idx: str):
    index = redis_client.get(idx)
    if index is None:
        return fastapi.Response(status_code=404)
    index = index.decode('utf-8')
    return str(index)


@app.get("/index/{idx}/query")
def query_index(idx: str):
    index = redis_client.get(idx)
    if index is None:
        return fastapi.Response(status_code=404)
    index = str(index.decode('utf-8'))
    x = llama_index.GPTTreeIndex(index)


@app.post("/index")
def create_index(index: Index):
    _id = uuid.uuid4()
    redis_client.set(str(_id), index.index)
    return _id


@app.put("/index/{idx}")
def update_index(idx: str, index: Index):
    if redis_client.get(idx) is None:
        return fastapi.Response(status_code=404)
    redis_client.set(idx, index.index)
    return idx


@app.delete("/index/{idx}")
def delete_index(idx: str):
    if redis_client.get(idx) is None:
        return fastapi.Response(status_code=404)
    redis_client.delete(idx)
    return idx
