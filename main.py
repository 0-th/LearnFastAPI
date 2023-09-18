from enum import Enum
from typing import Annotated, Dict, List, Union

from fastapi import Body, FastAPI, Path, Query
from pydantic import BaseModel

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
    # `short`'s type would be converted to `bool` by FastAPI
    # any value other than F(f)alse will be interpreted as `True`
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


# -----------------------------------------------------------------------------
# REQUEST BODY
# Request body is data sent by the client (mobile/web) to the API
# it is included in the request as JSON

class Category(str, Enum):
    fiction = "fiction"
    non_fiction = "non-fiction"


# Pydantic models are used to declare request body
class Book(BaseModel):
    title: str
    author: str
    year: int
    price: float
    isbn: int


@app.post("/books/{category}")
async def create_book(
        book: Book, quantity: int = 1, category: Union[Category, None] = None
):
    # `book` is a request body parameter
    # `quantity` is a query parameter
    # `category` is a path parameter
    if category:
        book.category = category

    result = book.model_dump()  # returns a dict of the model's values
    result.update({"quantity": quantity})
    return result


# -----------------------------------------------------------------------------
# Query parameters and string validations
# Pydantic can be used to validate the values for the query parameters
@app.get("/query-item/")
async def read_query_items(q: Annotated[Union[str, None], Query()] = ...):
    # `q` is a required query parameters. It also accepts None
    # Pydantic `Required` class can replace the ellipsis.
    query_items = {q: q}
    return query_items


# a list of values can also be accepted for a query parameter
@app.get("/query-list-items")
async def read_list_items(q: Annotated[List[str], Query()] = ["foo", "bar"]):
    # query param `q` accepts a list of strings and has a default value
    # http://localhost:8000/items/?q=foo&q=bar
    query_list_items = {"q": q}
    return query_list_items


# Fastapi also recognizes other non-validation metadata for query parameters
@app.get("/query-metadata-items")
async def read_metadata_items(
        q: Annotated[
            Union[str, None],
            Query(
                alias="item-query",
                title="Query String",
                description=(
                    "Query string for the items to search in the database that"
                    "have a good match"
                ),
                min_length=3,
                max_length=50,
                pattern="^fixedquery$",
                deprecated=True
            )
        ] = None
):
    # query parameter `q` contains the following metadata:
    # - alias: enables the use of `item-query` instead of `q` in the query str
    # - title and description: used in the OpenAPI schema or docs
    # - min_length, max_length and pattern: used for string validation
    # - deprecated: used to mark a query parameter as deprecated in the docs
    results = {}
    if q:
        results.update({"q": q})
    return results


# ----------------------------------------------------------------------------
# Path parameters and numerical validation
# In ordering (path/query) parameters, params with a default value cannot come
# before params without. If that's the case, python would spit an error.
# if you need to order it that way let the first argument to the path-operation
# function be an `*`, then python would parse all params as kwargs

@app.get(path='/items/{item_id}')
def read_path_items(
        item_id: Annotated[int, Path(title="ID of the retrieved item")],
        desc: Annotated[bool, Query(description="Add a description")] = False,
        q: str = ...,  # could also use Pydantic's `Required` class
        # required query param without a default value coming after a param
        # with a default value
):
    results: Dict[str, Union[int, str, bool]] = {"item_id": item_id}
    # BUG: `item_id` isn't included in the response
    results.update({"q": q})  # BUG: `q` isn't included in the response
    if desc:
        results.update(
            {
                "description":
                "This is an amazing item that has a long description"
            }
        )
    return results


# numeric validations
# `gt` and `lt` are greater than and less than respectively
# `ge` and `le` are greater than or equal to and less than or equal to
@app.get("/numeric-items/{item_id}")
async def read_numeric_items(
        item_id: Annotated[
            int,
            Path(
                title="ID of the item to get",
                ge=1,
                le=1000
            )
        ],
        q: str,
        size: Annotated[float, Query(gt=0, lt=10.5)]  # float datatype
):
    results = {"item_id": item_id, "q": q, "size": size}
    return results


# ----------------------------------------------------------------------------
# MULTIPLE REQUEST BODY PARAMETERS
# Query parameters of complex types(e.g list) should be annotated with `Query`,
# similarly, request body parameters of single values should be annotated with
# `Body`, else FastAPI would interpret them as query parameters or in the case
# of query parameters, FastAPI would interpret them as request body parameters


class LibUser(BaseModel):
    student = "student"
    teacher = "teacher"


class LibItem(BaseModel):
    title: str
    category: Union[Category, None] = None


@app.put("/lib-items/{item_id}")
async def update_lib_item(
        item_id: int,
        item: LibItem,
        user: LibUser,
        # single value request body parameter
        importance: Annotated[
            int,
            Body(gt=0, lt=1000)
            ],
        q: Union[str, None] = None
):
    results = {
        "item_id": item_id,
        "item": item,
        "user": user,
        "importance": importance
    }
    if q:
        results.update({"q": q})
    return results


# Embed a single body parameter in the request body.
# the request body is a single json object,if there's a single parameter
# in the request body, it would be interpreted as the json object and only
# the value of the parameter would be returned.
# To embed the parameter with the key itself, use `Body(..., embed=True)`
@app.get("/embed-body-item/{item_id}")
async def read_embed_body_item(
        item_id: int,
        item: Annotated[LibItem, Body(embed=True)]
):
    results = {"item_id": item_id, "item": item}
    return results
# Request body would look like:
""" {
    "item": {
        "name": "Foo",
        "description": "The pretender",
        "price": 42.0,
        "tax": 3.2
    }
}
"""
# instead of the default:
"""
{
    "name": "Foo",
    "description": "The pretender",
    "price": 42.0,
    "tax": 3.2,
}
"""
