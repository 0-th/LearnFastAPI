from fastapi import FastAPI

app = FastAPI()


# handle GET request to the path "/"
@app.get("/")  # path operation decorator
async def root():
    return {"message": "Hello World"}
