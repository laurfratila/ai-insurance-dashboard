from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import marts
from .routers import overview

app = FastAPI(title="Insurance Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten later
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}


# mount the marts router
app.include_router(marts.router)
app.include_router(overview.router)