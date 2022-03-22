from doctest import Example
import re
from pydantic import BaseModel, Field
from decimal import Decimal
from enum import Enum
import base64

from app_v2.repository.repository import UserRepository, LogRepository

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

class NutrientsName(str, Enum):
    vitamins= ["vitamins"]
    multivitamin= ["multivitamin"]
    nothing= None
    
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
        return self.__repository.update_user_nutr_suppl(userid, nutrsuppl)

    ####8 유저 nutr_suppl 정보 요청
    def get_user_nutr_suppl(self, userid: str):
        return self.__repository.get_user_nutr_suppl(userid)

    ####9 search nutr_suppl list
    def get_nutr_suppl_list(self, search: str):
        return self.__repository.get_nutr_suppl_list(search)
        
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
    def post_meal_log(self, userid: str, image_key, class_list:list, food_list: list):
        return self.__repository.post_meal_log(userid, image_key, class_list, food_list)

    #### update 식단 로그, 음식 리스트만 수정
    def update_meal_log_food_list(self, userid:str, dt, new_food_list:list):
        return self.__repository.update_meal_log_food_list(userid, dt, new_food_list)

    ####4 유저 식단 섭취 로그 정보 요청 - 특정 날
    def get_meal_log(self, userid: str, date):
        return self.__repository.get_meal_log(userid, date)
    
    ####5 유저 식단 섭취 로그 정보 삭제 - 특정 시간(시기)
    def delete_meal_log(self, userid: str, datetime):
        return self.__repository.delete_meal_log(userid, datetime)

    ####6 영양제 영양성분 정보 요청
    def get_nutr_suppl_nutrients(self, nutr_cat: str, product_code: str):
        return self.__repository.get_nutr_suppl_nutrients(nutr_cat, product_code)

    ####7 유저 영양제 섭취 로그 등록
    def post_nutrtake_log(self, userid: str, nutr_suppl_list):
        return self.__repository.post_nutrtake_log(userid, nutr_suppl_list)
    
    #### update 영양제 섭취 로그에서 영양제 변경
    def update_nutrtake_log_suppl_list(self, userid:str, date_time, new_suppl_list:list):
        return self.__repository.update_nutrtake_log_suppl_list(userid, date_time, new_suppl_list)

    ####8 유저 영양제 섭취 로그 정보 요청 - 특정 날
    def get_nutrtake_log(self, userid: str, date):
        return self.__repository.get_nutrtake_log(userid, date)

    ####9 유저 영양제 섭취 로그 삭제 - 특정 시간(시기)
    def delete_nutrtake_log(self, userid: str, datetime):
        return self.__repository.delete_nutrtake_log(userid, datetime)

    ####10 유저 영양 상태 식단 로그 입력 & 업데이트
    def update_user_meal_nutr_log(self, userid: str, nutrients):
        return self.__repository.update_user_meal_nutr_log(userid, nutrients)

    ####11 유저 영샹 상태 영양제 로그 입력 & 업데이트
    def update_user_nutrtake_nutr_log(self, userid: str, nutrients):
        return self.__repository.update_user_nutrtake_nutr_log(userid, nutrients)

    #### get 사용자 영양상태 로그 - 특정 날짜 (식단 + 영양제)
    def get_user_nutr_log(self, userid:str, date): 
        return self.__repository.get_user_nutr_log(userid, date)

    #### get 사용자 영양상태 로그 - 특정 날짜 (식단)
    def get_user_nutr_log_meal(self, userid:str, date):
        return self.__repository.get_user_nutr_log_meal(userid, date)

    #### get 사용자 영양상태 로그 - 특정 날짜 (식단 - 탄단지)
    def get_user_nutr_log_meal_CPF(self, userid:str, date):
        return self.__repository.get_user_nutr_log_meal_CPF(userid, date)

    #### get 사용자 영양상태 로그 - 특정 날짜 (영양제)
    def get_user_nutr_log_suppl(self, userid:str, date):
        return self.__repository.get_user_nutr_log_suppl(userid, date)

    #### get 사용자 영양 상태 로그 - 오늘부터 n일 (식단 + 영양제)
    def get_user_nutr_log_ndays(self, userid:str, ndays:int):
        return self.__repository.get_user_nutr_log_ndays(userid, ndays)

    #### get 사용자 영양 상태 로그 - 오늘부터 n일 (식단)
    def get_user_nutr_log_meal_ndays(self, userid:str, ndays:int):
        return self.__repository.get_user_nutr_log_meal_ndays(userid, ndays)

    #### get 사용자 영양 상태 로그 - 오늘부터 n일 (영양제)
    def get_user_nutr_log_suppl_ndays(self, userid:str, ndays:int):
        return self.__repository.get_user_nutr_log_suppl_ndays(userid, ndays)


    #### get today nutr status
    def get_user_today_status(self, userid: str):
        return self.__repository.get_user_today_status(userid)


    #### get week nutr status
    def get_user_week_status(self, userid: str):
        return self.__repository.get_user_week_status(userid)

    ####1 유저 영양제 추천
    def recommend_nutrients(self, userid: str, request):
        return self.__repository.recommend_nutriendts(userid, request)