from pydantic import BaseModel, Field
from decimal import Decimal
from app_v2.repository.repository import UserRepository, LogRepository

class UserJoinModel(BaseModel):
    userid: str= Field(example= '@email')
    physique: physique
class physique(BaseModel):
    birth: str= Field(example= 'yyyy-mm-dd')
    sex: str= Field(example= 'f or m')
    height: Decimal= Field(example= 'allow decimal point with (""), ex) "177.2"')
    weight: Decimal= Field(example= 'allow decimal point with (""), ex) "67.7"')
    PAI: Decimal= Field(example= 'allow decimal point with (""), ex) "1.2"')
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
    
    def get_user_RDI(self, userid: str):
        return self.__repository.get_user_RDI(userid)
        
class LogDomain():
    def __init__(self, repository: LogRepository):
        self.__repository= repository