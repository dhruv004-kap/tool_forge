from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from Routers.action_assistant import actions
from Routers.prompt_library import library

app = FastAPI(
        title="Prompt Gallery API",
        redoc_url="/prompt/redoc",
        docs_url="/prompt/docs",
        openapi_url="/prompt/openapi.json",
    )

app.include_router(actions)
app.include_router(library)

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],  # allow all origins
    allow_credentials = True,
    allow_methods = ["*"],  # allow POST, GET, OPTIONS etc.
    allow_headers = ["*"],  # allow Authorization, Content-Type etc.
)

@app.get("/")
async def welcome():
    return {"message": "Hello!"}
