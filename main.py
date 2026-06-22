from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
import random
import string
from pydantic import BaseModel
from fastapi.responses import RedirectResponse
from database import engine, get_db
import models
from redis_client import redis_client

# Create all tables on startup
models.Base.metadata.create_all(bind=engine)

class URLRequest(BaseModel):
    url: str

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "URL Shortener API is running!"}

def generate_short_code():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=7))

@app.get("/generate")
def generate_endpoint():
    short_code = generate_short_code()
    return {"short_code": short_code}

@app.post("/shorten")
def shorten_url(request: URLRequest, db: Session = Depends(get_db)):
    short_code = generate_short_code()
    new_url = models.URL(short_code = short_code, long_url = request.url)
    db.add(new_url)
    db.commit()
    db.refresh(new_url)
    return {"short_code": short_code, "long_url": request.url}

@app.get("/{short_code}")
def redirect_url(short_code: str, db: Session = Depends(get_db)):
    cached_url = redis_client.get(short_code)
    if cached_url:
        return RedirectResponse(cached_url)
    
    url_entry = db.query(models.URL).filter(models.URL.short_code == short_code).first()
    if url_entry:
        redis_client.set(short_code, url_entry.long_url, ex=3600)
        return RedirectResponse(url_entry.long_url)
    return {"error": "Short code not found"}