from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.models.models import Base
from app.database import engine
from app.api.v1 import circles, members, payments, wallets

app = FastAPI(title=settings.app_name, version="1.0.0")

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(circles.router, prefix=settings.api_v1_prefix)
app.include_router(members.router, prefix=settings.api_v1_prefix)
app.include_router(payments.router, prefix=settings.api_v1_prefix)
app.include_router(wallets.router, prefix=settings.api_v1_prefix)

@app.get("/health")
def health_check():
    return {"status": "ok"}
