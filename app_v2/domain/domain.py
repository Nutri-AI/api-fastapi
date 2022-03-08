from pydantic import BaseModel, Field
from decimal import Decimal
from enum import Enum

from app_v2.repository.repository import UserRepository, LogRepository

class physique(BaseModel):
    birth: str= Field(...,example= "1995-04-04")
    sex: str= Field(...,example= "M")
    height: Decimal= Field(...,example= "177.2")
    weight: Decimal= Field(...,example= "67.7")
    PAI: Decimal= Field(...,example= "1.2")

class UserJoinModel(BaseModel):
    userid: str= Field(...,example= "nutriai@email.com")
    physique: physique

class NutrientsName(str, Enum):
    vitamins= ["vitamins"]
    multivitamin= ["multivitamin"]
    nothing= None

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

    def update_user_nutr_suppl(self, userid: str, nutrsuppl):

        return self.__repository.update_user_nutr_suppl(userid, nutrsuppl)
    
    def get_user_RDI(self, userid: str):
        return self.__repository.get_user_RDI(userid)

        
class LogDomain():
    def __init__(self, repository: LogRepository):
        self.__repository= repository

    def upload_image(self, userid: str, image):
        #onnx runtime 추론 -> image, class number 반환
        #여기서 대분류(detail) 매핑
        #detail= mapping[int]
        return self.__repository.upload_image(userid, image)#, detail)

    def record_meal(self, userid: str, big: str, small: str):
        return self.__repository.record_meal(userid, big, small)

    def post_time_nutri(self, userid: str, request):
        return self.__repository.post_time_nutri(userid, request)

    def recommend_nutrients(self, userid: str, request):
        return self.__repository.recommend_nutriendts(userid, request)