# app/main.py
from typing import List
from sqlalchemy import func
from dotenv import load_dotenv
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from jinja2 import Environment, FileSystemLoader, select_autoescape
from fastapi.responses import HTMLResponse
from fastapi import FastAPI, Depends, Request

from app.models import Place
from app.router import router
from app.database.database import get_db

# Load the environment variables from the .env file
load_dotenv()
 
app = FastAPI()

# Configure the Jinja2 environment directly
env = Environment(
    loader=FileSystemLoader("app/templates"),
    autoescape=select_autoescape(['html', 'xml'])
)

# Register the router
app.include_router(router)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Place))
    places = result.scalars().all()
    template = env.get_template("index.html")
    return HTMLResponse(template.render(request=request, places=places))
