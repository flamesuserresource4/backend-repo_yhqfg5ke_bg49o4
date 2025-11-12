import os
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr

from database import db, create_document, get_documents
from schemas import Tee, Subscription

app = FastAPI(title="Limited Edition Tees API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Utilities

def _now_year_month():
    now = datetime.utcnow()
    return now.year, now.month


def _serialize(doc: dict) -> dict:
    if not doc:
        return doc
    d = dict(doc)
    _id = d.pop("_id", None)
    if _id is not None:
        try:
            d["id"] = str(_id)
        except Exception:
            d["id"] = _id
    return d


# Health endpoints

@app.get("/")
def root():
    return {"message": "Limited Edition Tees Backend Running"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = getattr(db, "name", None) or "Unknown"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections
                response["connection_status"] = "Connected"
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response


# API models for responses

class TeeResponse(Tee):
    id: Optional[str] = None


# Tee endpoints

@app.get("/api/tees/current", response_model=List[TeeResponse])
def get_current_tees(year: Optional[int] = None, month: Optional[int] = None):
    """Return tees for the specified month/year, defaults to current month."""
    y, m = _now_year_month()
    y = year or y
    m = month or m
    docs = get_documents("tee", {"release_year": y, "release_month": m}) if db else []
    return [_serialize(d) for d in docs]


@app.get("/api/tees/archive", response_model=List[TeeResponse])
def get_archive_tees():
    """Return tees that are not in the current month."""
    y, m = _now_year_month()
    # Query all tees and filter in DB
    docs = get_documents("tee", {}) if db else []
    filtered = [d for d in docs if not (d.get("release_year") == y and d.get("release_month") == m)]
    # Sort newest first
    filtered.sort(key=lambda d: (d.get("release_year", 0), d.get("release_month", 0)), reverse=True)
    return [_serialize(d) for d in filtered]


@app.get("/api/tees/{slug}", response_model=TeeResponse)
def get_tee_detail(slug: str):
    docs = get_documents("tee", {"slug": slug}) if db else []
    if not docs:
        raise HTTPException(status_code=404, detail="Tee not found")
    return _serialize(docs[0])


# Subscriptions

class SubscribeRequest(BaseModel):
    email: EmailStr
    name: Optional[str] = None


@app.post("/api/subscribe")
def subscribe(payload: SubscribeRequest):
    # Check for existing subscription
    existing = get_documents("subscription", {"email": payload.email}, limit=1) if db else []
    if existing:
        return {"status": "ok", "message": "Already subscribed"}
    sub = Subscription(email=payload.email, name=payload.name)
    sub_id = create_document("subscription", sub)
    return {"status": "ok", "id": sub_id}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
