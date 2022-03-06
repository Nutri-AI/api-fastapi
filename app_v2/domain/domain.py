from pydantic import BaseModel
from decimal import Decimal
from app_v2.repository.repository import UserRepository, LogRepository

class UserJoinModel(BaseModel):
    userid: str
    physique: physique
class physique(BaseModel):
    birth: str
    sex: str
    height: Decimal
    weight: Decimal
    PAI: Decimal
class UserDomain():
    def __init__(self, repository: UserRepository):
        self.__repository= repository

    def join_user(self, request: dict):
        return self.__repository.join_user(request.dict())

    def update_user_physique(self, userid: str, physique: dict):

        return self.__repository.update_user_physique(userid, physique.dict())

    def delete_user(self, userid: str):

        return self.__repository.delete_user(userid)

    def get_user(self, userid: str):

        return self.__repository.get_user(userid)

    def update_user_nutr_suppl(self, userid: str):

        return self.__repository.update_user_nutr_suppl(userid)
        
class LogDomain():
    def __init__(self, repository: LogRepository):
        self.__repository= repository