import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import models  # noqa: F401  (registers the tables)
from database import Base, engine
from routers import auth, cars, listings, maintenance, people, reservations

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Leaves tables already created by schema.sql untouched; only creates missing ones.
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Car Rental API", version="2.0.0", lifespan=lifespan)

origins = [o.strip() for o in os.getenv("FRONTEND_ORIGIN", "http://localhost:5173").split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins + ["http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in (auth, people, cars, listings, reservations, maintenance):
    app.include_router(r.router)


@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "docs": "/docs"}
