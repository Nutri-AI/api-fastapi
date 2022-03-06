from fastapi import APIRouter

from app_v2.domain.domain import UserDomain, LogDomain, UserJoinModel, physique

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

        @api_router.put('/update/{userid}')
        def update_user_physique(userid: str, physique: physique):
            return self.__domain.update_user_physique(userid, physique)

        @api_router.delete('/delete/{userid}')
        def delete_user(userid: str):
            return self.__domain.delete_user(userid)

        @api_router.get('/info/{userid}')
        def get_user(userid):
            return self.__domain.get_user(userid)
        
        @api_router.put('/update/nutrients/{userid}')
        def update_user_nutr_suppl(userid):
            return self.__domain.update_user_nutr_suppl(userid)

        
class LogRouter:
    def __init__(self, domain: LogDomain):
        self.__domain= domain
    
    @property
    def router(self):
        api_router= APIRouter(prefix= 'log/', tags= ['log'])