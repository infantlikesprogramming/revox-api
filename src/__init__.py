from fastapi import FastAPI
from src.translation.routes import translation_router
from src.ai.routes import ai_router
from src.speechinfo.routes import speechinfo_router
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

# from tailscale import Tailscale
# import os
# import socket


version = "v0.1.1"

description = """
A REST API for speech-related translation services

This REST API is able to 
- Create Translation and its audio version and update to the database
- Create Topic and Speaker's information and update to the database"""

version_prefix = f"api/{version}"

app = FastAPI(
    title="EngVietSpeechTranslation",
    description="A REST API for a speech translation web service",
    version=version,
    license_info={"name": "MIT License", "url": "https://opensource.org/license/mit"},
    terms_of_service="https://example.com/tos",
    openapi_url=f"/{version_prefix}/openapi.json",
    docs_url=f"/{version_prefix}/docs",
    redoc_url=f"/{version_prefix}/redoc",
)


app.include_router(translation_router, prefix=f"/translations", tags=["translations"])
app.include_router(ai_router, prefix=f"/ai", tags=["ai"])
app.include_router(speechinfo_router, prefix=f"/urlinfo", tags=["urlinfo"])


# @app.get("/devices")
# async def list_devices():
#     async with Tailscale(
#         tailnet=os.getenv("TAILNET"), api_key=os.getenv("TAILSCALE_API_KEY")
#     ) as tailscale:
#         devices = await tailscale.devices()
#         return {"devices": devices}


@app.get("/")
async def root():
    return {"message": "Hello, World!"}


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "https://qweqweqwe-theta.vercel.app",
        "https://coolapp.space",
        "https://www.coolapp.space",
    ],  # Allow Next.js origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# print(f"Private IP: {socket.gethostbyname(socket.gethostname())}")
