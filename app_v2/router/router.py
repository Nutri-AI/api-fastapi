from fastapi import APIRouter

from app_v2.domain.domain import UserDomain, LogDomain, UserJoinModel

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

        @api_router.put('/update/{id}')
        def update_user(id: str):
            return self.__domain.update_user(id)

        @api_router.delete('/delete/{id}')
        def delete_user(id: str):
            return self.__domain.delete_user(id)

        @api_router.get('/info/{id}')
        def get_user(id):
            return self.__domain.get_user(id)
        
        @api_router.put('/update/nutrients/{id}')
        def update_nutrients(id):
            return self.__domain.update_nutrients(id)

        
class LogRouter:
    def __init__(self, domain: LogDomain):
        self.__domain= domain
    
    @property
    def router(self):
        api_router= APIRouter(prefix= 'log/', tags= ['log'])