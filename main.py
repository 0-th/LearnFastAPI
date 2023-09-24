from datetime import datetime, time, timedelta
from enum import Enum
from typing import Annotated, Dict, List, Union
from uuid import UUID

from fastapi import Body, FastAPI, Path, Query, Cookie
from pydantic import BaseModel, Field, HttpUrl

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
    # Pydantic `Required` class can replace the ellipsis only within models.
    # FastAPI doesn't recognize it outside of models

    # Also, since assigning ellipsis directly doesn't provide good validation
    # error messages, it's better to use it within Query, Path or Body classes
    # `Query(...)`
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
        # required query param `q` without a default value coming after a param
        # with a default value
        q: str = ...,  # could also use Pydantic's `Required` class (wrong)
        # only use Pydantic's `Required` class within models.
        # use `Query(...)` instead here, since ellipsis doesn't provide good
        # validation error messages.

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


class LibUser(str, Enum):
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

# ----------------------------------------------------------------------------
# REQUEST BODY FIELDS
# Metadata can be added to the fields of Pydantic models that describe the
# request body.
# `Field` class is used to add metadata to the fields of a Pydantic model.
# It accepts arguments similar to the `Query` and `Path` classes.


class FieldItem(BaseModel):
    name: str
    description: Annotated[
        Union[str, None], Field(
            default=None,
            title="The description of the item",
            max_length=300
        )
    ]
    price: Annotated[float, Field(
        default=...,
        gt=0,
        description="The price must be greater than zero"
    )]
    tax: Union[float, None] = None


@app.put("/field-items/{item_id}")
async def update_field_item(
        item_id: int,
        item: Annotated[FieldItem, Body(embed=True)]
):
    results = {"item_id": item_id, "item": item}
    return results


# ----------------------------------------------------------------------------
# NESTED MODELS
# Pydantic's models can have fields with types that are themselves Pydantic
# models


class NestedImage(BaseModel):
    url: HttpUrl  # Pydantic's special type for URLs
    name: str


class NestedItem(BaseModel):
    name: str
    description: Union[str, None] = None
    price: float
    tax: Union[float, None] = None
    tags: List[str] = []
    image: Union[NestedImage, None] = None


class NestedUser(BaseModel):
    username: str
    full_name: Union[str, None] = None
    items: List[NestedItem]


# NOTE: Request bodies should only be sent with POST, PUT or PATCH requests
# it shouldn't be added as a parameter to a GET request
@app.post("/nested-user/{user_id}")
async def create_nested_user(
        user_id: int,
        user: Annotated[NestedUser, Body(default=..., embed=True)],
        q: Union[str, None] = None
):
    results = {"user_id": user_id, "user": user}
    if q:
        results.update({"q": q})
    return results


# The request body type could also be a dict with a data type specified for
# the key and values.
# This is useful when you don't know what fields the request body would have
# beforehand.


class HeightLabel(str, Enum):
    tall = "tall"
    medium = "medium"
    short = "short"


@app.post("/index-heights")
async def create_index_heights(
        weights: Annotated[
        Dict[int, HeightLabel], Body(default=..., embed=True)
        ]
):
    return weights


# ----------------------------------------------------------------------------
# DECLARE REQUEST EXAMPLE DATA
# Example data for request model can be declared for documentation purposes


class ExampleItem(BaseModel):
    name: str
    description: Union[str, None] = None
    price: float
    tax: Union[float, None] = None

    # declare example data
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Foo",
                "description": "A very nice Item",
                "price": 35.4,
                "tax": 3.2
            }
        }
    }


@app.post("/example-items/{item_id}")
async def create_example_item(
        item_id: int,
        item: Annotated[ExampleItem, Body(default=..., embed=True)]
):
    results = {"item_id": item_id, "item": item}
    return results


# Request body fields can also have example data declared

class ExampleFieldItem(BaseModel):
    name: str = Field(examples=["Foo"])
    description: Union[str, None] = Field(
        default=None, examples=["A very nice Item"]
    )
    price: float = Field(..., gt=0, examples=[35.4])
    tax: Union[float, None] = Field(default=None, examples=[3.2])


@app.put("/example-field-items/{item_id}")
async def update_example_field_item(
        item_id: int,
        item: Annotated[ExampleFieldItem, Body(embed=True)]
):
    results = {"item_id": item_id, "item": item}
    return results

# The above also works for Query(), Path(), Body(), etc.

# Passing multiple examples to a request body parameter
# `examples` can be passed as a list of dicts


@app.post("/example-items-multiple/{item_id}")
async def create_example_items_multiple(
        item_id: int,
        item: Annotated[
            ExampleItem,
            Body(
                default=...,
                embed=True,
                # Only the first example would be included in the docs
                examples=[
                    {
                        "summary": "A foo item",
                        "description": "A very nice Item",
                        "value": {
                            "name": "Foo",
                            "description": "A very nice Item",
                            "price": 35.4,
                            "tax": 3.2
                        }
                    },
                    {
                        "summary": "A bar item",
                        "description": "A very nice Bar Item",
                        "value": {
                            "name": "Bar",
                            "description": "A very nice Bar Item",
                            "price": 62.4,
                            "tax": 3.2
                        }
                    }
                ]
            )
        ]
):
    results = {"item_id": item_id, "item": item}
    return results

# INCLUDE MULTIPLE EXAMPLES IN THE DOCS
# note: only the first example would included in the docs.
# this is because the swagger-ui doesn't support multiple examples being
# included in the json schema (as it was only recently supported in the
# json schema spec).
# However, the OpenAPI spec used to support multiple examples
# before json schema which is still supported by swagger-ui and redoc.
# To include multiple examples in the docs, replace `examples` with
# `openapi_examples` which is provided by fastapi and supported by swagger-ui


# --------------------------------------------------------------------------------
# EXTRA DATATYPES
# We've only used basic datatypes supported by Pydantic so far.
# FastAPI also allows non-basic datatypes that aren't supported by Pydantic
# models to be used in path, query and request body parameters.


@app.post("/extra-items/{item_id}")
async def create_extra_item(
        item_id: UUID,
        start_datetime: Annotated[datetime, Body(
            # declare multiple example data in the docs
            # FIX: none of the examples were displayed in the docs
            openapi_examples={
                "example1": {
                    "summary": "First example",
                    "value": "2019-07-26T20:56:00.123456+00:00"
                },
                "example2": {
                    "summary": "Second example",
                    "value": "2019-07-26T20:56:00.123456",
                }
            }
        )],
        end_datetime: Annotated[datetime, Body()],
        repeat_at: Annotated[time, Body()],
        process_after: Annotated[timedelta, Body()],
):
    # values of these datatypes can be used in the usual ways
    process_start = start_datetime + process_after
    duration = end_datetime - process_start

    result = {
        "item_id": item_id,
        "repeat_at": repeat_at,
        "process_start": process_start,
        "duration": duration
    }
    return result


# --------------------------------------------------------------------------------
# COOKIE PARAMETERS
# Cookie parameters are declared in the path operation function just like query
# and path parameters.
# If the `Cookie` class isn't added to a parameter, it would considered a query
# param


@app.get("/cookie-items/")
async def read_cookie_items(
    maryland_cookie: Annotated[str, Cookie(default="default_maryland_cookie")]
):
    return {"maryland_cookie": maryland_cookie}
