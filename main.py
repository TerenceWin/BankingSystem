from fastapi import FastAPI, Request, status
from .models import Base
from .database import engine
from .routers import auth, account, beneficary, transaction, admin, user
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI()
app.mount("/static", StaticFiles(directory="Banking_system/static"), name="static")

Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory="Banking_system/templates")



@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/signup")
def loginPage(request: Request):
    return templates.TemplateResponse("signUp.html", {"request": request})

@app.get("/healthy")
def get_health_status(): 
    return {"status": "Healthy"}

@app.get("/admin")
def adminPage(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(user.router)
app.include_router(account.router)
app.include_router(beneficary.router)
app.include_router(transaction.router)
