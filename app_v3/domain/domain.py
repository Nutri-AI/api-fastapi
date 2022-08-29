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

    '''
    신규 유저 가입
    '''
    def join_user(self, request: dict):
        return self.__repository.join_user(request.dict())

    '''
    유저 정보 업데이트 - physique, RDI 수정
    '''
    def update_user_physique(self, userid: str, physique: dict):
        return self.__repository.update_user_physique(userid, physique.dict())

    '''
    유저 physique 정보 요청
    '''
    def get_user_physique(self, userid: str):
        return self.__repository.get_user_physique(userid)

    '''
    유저 정보 요청
    '''
    def get_user(self, userid: str):
        return self.__repository.get_user(userid)

    '''
    (앱 구현 X)
    유저 정보 삭제
    '''
    def delete_user(self, userid: str):
        return self.__repository.delete_user(userid)

    '''
    유저 RDI 정보 요청
    '''
    def get_user_RDI(self, userid: str):
        return self.__repository.get_user_RDI(userid)

    '''
    (앱 구현 X)
    nutr_suppl 수정 - 유저 별 영양제 추가 등록 및 수정
    --------
    Modify
    --------
    NutrientsName 입력 JSON에서
    섭취 영양제 리스트 정보만 전달
    '''
    def update_user_nutr_suppl(self, userid: str, nutrsuppl):
        nutrsuppl= nutrsuppl['nutrition_supplements']
        return self.__repository.update_user_nutr_suppl(userid, nutrsuppl)

    '''
    (앱 구현 X)
    유저 nutr_suppl 정보 요청
    '''
    def get_user_nutr_suppl(self, userid: str):
        return self.__repository.get_user_nutr_suppl(userid)

        
class LogDomain():
    def __init__(self, repository: LogRepository):
        self.__repository= repository

    '''
    식단 이미지 S3 파일 서버에 업로드
    '''
    def upload_image(self, userid: str, image):
        return self.__repository.upload_image(userid, image)

    '''
    Inference 이미지 S3 파일 서버에서 가져오기
    '''
    def get_s3_url_file(self, obj_name: str):
        return self.__repository.get_s3_url_file(obj_name)

    '''
    음식 영양 성분 요청 
    '''
    def get_food(self, food_cat: str, food_name: str):
        return self.__repository.get_food(food_cat, food_name)

    '''
    유저 식단 섭취 로그 등록
    --------
    Modify
    --------
    MealLog 입력 JSON에서
    S3 Image Key, Inference Class_type, Class_type 상세 음식 이름만 전달
    '''
    def post_meal_log(self, userid: str, request):
        img_key= request['image_key']
        class_f= request['class_list']
        food= request['food_list']
        return self.__repository.post_meal_log(userid, class_list=class_f, food_list=food, image_key=img_key)

    '''
    사용자 영양상태 로그 요청 - 특정 날짜 (식단 - 탄단지)
    '''
    def get_user_nutr_log_meal_CPF(self, userid:str, date):
        return self.__repository.get_user_nutr_log_meal_CPF(userid, date)

    '''
    사용자 영양 상태 로그 요청 - 오늘부터 ndays일 (식단 + 영양제) 
    '''
    def get_user_nutr_log_ndays(self, userid:str, ndays:int):
        return self.__repository.get_user_nutr_log_ndays(userid, ndays)

    '''
    today homepage 필요 정보 요청
    '''
    def get_user_today_status(self, userid: str):
        return self.__repository.get_user_today_status(userid)

    '''
    a week status 필요 정보 요청
    '''
    def get_user_week_status(self, userid: str):
        return self.__repository.get_user_week_status(userid)

    '''
    유저 영양제 추천
    '''
    def get_recomm_nutrsuppl(self, userid: str):
        return self.__repository.get_recomm_nutrsuppl(userid)

    def get_barcode_data(self, bcode: str):
        return self.__repository.get_barcode_data(bcode)
    '''
    바코드 식품 상품 로그
    '''
    def log_barcode_product(self, userid: str, bcode: str):
        return self.__repository.log_barcode_product(userid, bcode)