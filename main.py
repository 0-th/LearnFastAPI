from enum import Enum
from typing import Union

from fastapi import FastAPI

app = FastAPI()


# handle GET request to the path "/"
@app.get("/")  # path operation decorator
async def root():
    return {"message": "Hello World"}


# path parameters with types and validation
@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}


# ORDER MATTERS
# the next two routes collide

@app.get("/users/me")
async def read_user_me():
    return {"user_id": "the current user"}


@app.get("/users/{user_id}")
async def read_user(user_id: str):
    return {"user_id": user_id}

# `read_user_me` will never be called if it was defined after
# `read_user`; it would be interpreted as path param `user_id`.

# a path operation decorator to the same route cannot be redefined
# in 2 different path operation functions.
# only the first one will always be executed.


# PREDEFINED PATH PARAMETER VALUES
class ModelName(str, Enum):
    alexnet = "alexnet"
    resnet = "resnet"
    lenet = "lenet"
# inheriting from `str` makes the values be used as strings
# also useful for api docs


@app.get("/models/{model_name}")
async def get_model(model_name: ModelName):
    # path parameter of type `ModelName`
    if model_name == ModelName.alexnet:
        return {"model_name": model_name, "msg": "Deep Learning FTW!"}
    if model_name.value == "lenet":
        # access the `str` value of the ModelName` object
        return {"model_name": model_name, "msg": "LeCNN all the images"}
    return {"model_name": model_name, "msg": "Have some residuals"}


# PATH PARAMETERS CONTAINING FILE PATHS
# to define a path parameter containing a file path, use fastapi's `path` type
@app.get("/files/{file_path:path}")
async def read_files(file_path: str):
    return {"file_path": file_path}

# -----------------------------------------------------------------------------


# QUERY PARAMETERS
# path operation function parameters that aren't part of the path are
# interpreted as query parameters
@app.get("/users/{user_id}/items/{item_id}")
async def read_user_items(
        user_id: int,
        item_id: str,
        needy: str,
        q: Union[str, None] = None,
        short: bool = False
):
    # `user_id` and `item_id` are path parameters
    # `needy` is a required query parameter
    # `q` is an optional query parameter
    # `short` is a query parameter with a default value
    item = {"item_id": item_id, "owner_id": user_id, "needy": needy}
    if q:
        item.update({"q": q})
    if not short:
        item.update(
            {
                "description":
                "This is an amazing item that has a long description"
            }
        )
