from fastapi import APIRouter

from app_v2.domain.domain import UserDomain, UserLog

class UserRouter:
    def __init__(self, domain: UserDomain):
        self.__domain= domain

    @property
    def router(self):
        api_router= APIRouter(prefix= '/user', tags= ['user'])

        @api_router.get('/')
        def root():
            return 'Welcome Here!'

        @api_router.post('/join')
        def join_user(request: UserJoinModel):
            return self.__domain.join_user(request)

        @api_router.put('/update/{PK}')
        def update_user(PK: str):
            return self.__domain.update_user(PK)

        @api_router.delete('/delete/{PK}')
        def delete_user(PK: str):
            return self.__domain.delete_user(PK)

        @api_router.get('/info/{PK}')
        def get_user(PK):
            return self.__domain.get_user(PK)
        
        @api_router.put('/update/nutrients/{PK}')
        def update_nutrients(PK):
            return self.__domain.update_nutrients(PK)

        
class LogRouter:
    def __init__(self, domain: LogDomain):
        self.__domain= domain
    
    @property
    def router(self):
        api_router= APIRouter(prefix= 'log/', tags= ['log'])