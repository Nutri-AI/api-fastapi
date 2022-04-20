from lib2to3.pytree import Base
from pydantic import BaseModel, Field
from decimal import Decimal
from typing import List

from app_v3.repository.repository import UserRepository, LogRepository

class physique(BaseModel):
    birth: str= Field(...,example= "1995-04-04")
    sex: str= Field(...,example= "M")
    height: Decimal= Field(...,example= "177.2")
    weight: Decimal= Field(...,example= "67.7")
    PAI: Decimal= Field(...,example= "1.2")

class UserJoinModel(BaseModel):
    userid: str= Field(...,example= "nutriai@email.com")
    username: str= Field(..., example= "호날두")
    physique: physique

class NutrientsName(BaseModel):
    nutrition_supplements: List[str]

class MealLog(BaseModel):
    image_key: str
    class_list: List[str]
    food_list: List[str]

class UserDomain():
    def __init__(self, repository: UserRepository):
        self.__repository= repository   

    ####1 신규 유저 가입
    def join_user(self, request: dict):
        return self.__repository.join_user(request.dict())

    ####2 유저 정보 업데이트 - physique, RDI 수정
    def update_user_physique(self, userid: str, physique: dict):
        return self.__repository.update_user_physique(userid, physique.dict())

    ####3 유저 physique 정보 요청
    def get_user_physique(self, userid: str):
        return self.__repository.get_user_physique(userid)

    ####4 유저 정보 요청
    def get_user(self, userid: str):
        return self.__repository.get_user(userid)

    ####5 유저 정보 삭제
    def delete_user(self, userid: str):
        return self.__repository.delete_user(userid)

    ####6 유저 RDI 정보 요청
    def get_user_RDI(self, userid: str):
        return self.__repository.get_user_RDI(userid)

    ####7 nutr_suppl 수정 - 영양제 추가 등록 및 수정
    def update_user_nutr_suppl(self, userid: str, nutrsuppl):
        nutrsuppl= nutrsuppl['nutrition_supplements']
        return self.__repository.update_user_nutr_suppl(userid, nutrsuppl)

    ####8 유저 nutr_suppl 정보 요청
    def get_user_nutr_suppl(self, userid: str):
        return self.__repository.get_user_nutr_suppl(userid)

        
class LogDomain():
    def __init__(self, repository: LogRepository):
        self.__repository= repository

    ####1 이미지 S3에 업로드
    def upload_image(self, userid: str, image):
        return self.__repository.upload_image(userid, image)

    def get_s3_url_file(self, userid: str, obj_name: str):
        return self.__repository.get_s3_url_file(userid, obj_name)

    ####2 음식 영양 성분 정보 요청
    def get_food_nutrients(self, food_cat: str, food_name: str):
        return self.__repository.get_food_nutrients(food_cat, food_name)

    ####3 유저 식단 섭취 로그 등록
    def post_meal_log(self, userid: str, request):
        image_key= request['image_key']
        class_list= request['class_list']
        food_list= request['food_list']
        return self.__repository.post_meal_log(userid, image_key, class_list, food_list)


    #### get 사용자 영양상태 로그 - 특정 날짜 (식단 - 탄단지)
    def get_user_nutr_log_meal_CPF(self, userid:str, date):
        return self.__repository.get_user_nutr_log_meal_CPF(userid, date)


    #### get 사용자 영양 상태 로그 - 오늘부터 n일 (식단 + 영양제)
    def get_user_nutr_log_ndays(self, userid:str, ndays:int):
        return self.__repository.get_user_nutr_log_ndays(userid, ndays)

    #### get today nutr status
    def get_user_today_status(self, userid: str):
        return self.__repository.get_user_today_status(userid)

    #### get week nutr status
    def get_user_week_status(self, userid: str):
        return self.__repository.get_user_week_status(userid)

    ####1 유저 영양제 추천
    def get_recomm_nutrsuppl(self, userid: str):
        return self.__repository.get_recomm_nutrsuppl(userid)