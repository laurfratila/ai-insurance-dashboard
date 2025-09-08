from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import marts,overview, claims, risk, ops, c360,admin

app = FastAPI(title="AI Insurance Dashboard", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


# mount the marts router
app.include_router(marts.router)
app.include_router(overview.router)
app.include_router(claims.router)
app.include_router(risk.router)
app.include_router(ops.router)
app.include_router(c360.router)
app.include_router(admin.router)