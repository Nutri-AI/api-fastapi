from fastapi import FastAPI

from app_v3.internal.database import initialize_db

from app_v3.repository.repository import UserRepository, LogRepository
from app_v3.domain.domain import UserDomain, LogDomain
from app_v3.router.router import UserRouter, LogRouter

app= FastAPI()

db= initialize_db()

#generate_table(db)

user_repository= UserRepository(db)
user_domain= UserDomain(user_repository)
user_router= UserRouter(user_domain)

log_repository= LogRepository(db)
log_domain= LogDomain(log_repository)
log_router= LogRouter(log_domain)

app.include_router(user_router.router)
app.include_router(log_router.router)

@app.get('/')
def root():
    return 'Hello World!'