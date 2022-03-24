from fastapi import APIRouter, HTTPException, status, UploadFile, File

from app_v2.domain.domain import NutrientsName

from app_v2.domain.domain import UserDomain, LogDomain, UserJoinModel, physique, MealLog

class UserRouter:
    def __init__(self, domain: UserDomain):
        self.__domain= domain

    @property
    def router(self):
        api_router= APIRouter(prefix= '/user', tags= ['user'])

        @api_router.get('/')
        def root():
            return 'Welcome Here!'

        ####1 신규 유저 가입
        @api_router.post('/join')
        def join_user(request: UserJoinModel):
            try:
                return self.__domain.join_user(request)
            except:
                raise HTTPException(status_code= status.HTTP_406_NOT_ACCEPTABLE, detail= 'Please enter the appropriate format for the item')

        ####2 유저 정보 업데이트 - physique, RDI 수정
        @api_router.put('/update/{userid}')
        def update_user_physique(userid: str, physique: physique):
            return self.__domain.update_user_physique(userid, physique)

        ####3 유저 physique 정보 요청
        @api_router.get('/get/physique/{userid}')
        def get_user_physique(userid: str):
            return self.__domain.get_user_physique(userid)

        ####4 유저 정보 요청
        @api_router.get('/info/{userid}')
        def get_user(userid):
            try:
                return self.__domain.get_user(userid)
            except:
                raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail= 'No exist userid')

        ####5 유저 정보 삭제
        @api_router.delete('/delete/{userid}')
        def delete_user(userid: str):
            return self.__domain.delete_user(userid)

        ####6 유저 RDI 정보 요청
        @api_router.get('/get/RDI/{userid}')
        def get_user_RDI(userid: str):
            return self.__domain.get_user_RDI(userid)

        ####7 nutr_suppl 수정 - 영양제 추가 등록 및 수정
        @api_router.put('/update/nutrients/{userid}')
        def update_user_nutr_suppl(userid: str, nutrsuppl: NutrientsName):
            return self.__domain.update_user_nutr_suppl(userid, nutrsuppl.dict())
        
        ####8 유저 nutr_suppl 정보 요청
        @api_router.get('/get/nutr/suppl/{userid}')
        def get_user_nutr_suppl(userid: str):
            return self.__domain.get_user_nutr_suppl(userid)

        ####9 search nutr_suppl list
        @api_router.get('/search/nutr-list')
        def get_nutr_suppl_list(search: str):
            return self.__domain.get_nutr_suppl_list(search)


        return api_router
        
class LogRouter:
    def __init__(self, domain: LogDomain):
        self.__domain= domain
    
    @property
    def router(self):
        api_router= APIRouter(prefix= '/log', tags= ['log'])

        ####1 이미지 S3로 업로드 및 등등
        @api_router.post('/upload/image/{userid}')
        def upload_image(userid: str, image: bytes= File(...)):
            return self.__domain.upload_image(userid, image)

        @api_router.get('/get/s3-url')
        def get_s3_url_file(userid: str, obj_name: str):
            return self.__domain.get_s3_url_file(userid, obj_name)

        ####2 음식 영양 성분 요청
        @api_router.get('/get/food/nutrients')
        def get_food_nutrients(food_cat: str, food_name: str):
            return self.__domain.get_food_nutrients(food_cat, food_name)

        ####3 유저 식단 섭취 로그 등록
        @api_router.post('/post/meal/log/{userid}')
        def post_meal_log(userid: str, request: MealLog):
            return self.__domain.post_meal_log(userid, request.dict())

        #### update 식단 로그, 음식 리스트만 수정
        @api_router.put('/update/meal-log/food-list/{userid}')
        def update_meal_log_food_list(userid:str, dt, new_food_list:list):
            return self.__domain.update_meal_log_food_list(userid, dt, new_food_list)

        ####4 유저 식단 섭취 로그 정보 요청 - 특정 날
        @api_router.get('/get/meal/log/{userid}')
        def get_meal_log(userid: str, date):
            return self.__domain.get_meal_log(userid, date)

        ####5 유저 식단 섭취 로그 삭제 - 특정 시간(시기)
        @api_router.delete('/delete/meal/log/{userid}')
        def delete_meal_log(self, userid: str, datetime):
            return self.__domain.delete_meal_log(userid, datetime)
        
        ####6 영양제 영양성분 정보 요청
        @api_router.get('/get/nutr_suppl/nutrients')
        def get_nutr_suppl_nutrients(nutr_cat: str, product_code: str):
            return self.__domain.get_nutr_suppl_nutrients(nutr_cat, product_code)

        ####7 유저 영양제 섭취 로그 등록
        @api_router.post('/post/nutrtake/log/{userid}')
        def post_nutrtake_log(userid: str, nutr_suppl_list):
            return self.__domain.post_nutrtake_log(userid, nutr_suppl_list)

        ####8 update 영양제 섭취 로그에서 영양제 변경
        @api_router.put('/update/')
        def update_nutrtake_log_suppl_list(userid:str, date_time, new_suppl_list:list):
            return self.__domain.update_nutrtake_log_suppl_list(userid, date_time, new_suppl_list)

        ####9 유저 영양제 섭취 로그 정보 요청 - 특정 날
        @api_router.get('/get/nutrtake/log/{userid}')
        def get_nutrtake_log(userid: str, date):
            return self.__domain.get_nutrtake_log(userid, date)

        ####10 유저 영양제 섭취 로그 삭제 - 특정 시간(시기)
        @api_router.delete('/delete/nutrtake/log/{userid}')
        def delete_nutrtake_log(userid: str, datetime):
            return self.__domain.delete_nutrtake_log(userid, datetime)

        ####11 유저 영양 상태 식단 로그 입력 & 업데이트
        @api_router.put('/update/meal/nutr/log/{userid}')
        def update_user_meal_nutr_log(userid: str, nutrients):
            return self.__domain.update_user_meal_nutr_log(userid, nutrients)
        
        ####12 유저 영양 상태 영양제 로그 입력 & 업데이트
        @api_router.put('/update/nutrtake/nutr/log/{userid}')
        def update_user_nutrtake_nutr_log(userid: str, nutrients):
            return self.__domain.update_user_nutrtake_nutr_log(userid, nutrients)
        
        ####13 get 사용자 영양상태 로그 - 특정 날짜 (식단 + 영양제)
        @api_router.get('/get/nutr-log')
        def get_user_nutr_log(self, userid:str, date): 
            return self.__domain.get_user_nutr_log(userid, date)

        ####14 get 사용자 영양상태 로그 - 특정 날짜 (식단)
        @api_router.get('/get/nutr-log-meal')
        def get_user_nutr_log_meal(self, userid:str, date):
            return self.__domain.get_user_nutr_log_meal(userid, date)

        ####15 get 사용자 영양상태 로그 - 특정 날짜 (식단 - 탄단지)
        @api_router.get('/get/nutr-log-meal-cpf')
        def get_user_nutr_log_meal_CPF(self, userid:str, date):
            return self.__domain.get_user_nutr_log_meal_CPF(userid, date)

        ####16 get 사용자 영양상태 로그 - 특정 날짜 (영양제)
        @api_router.get('/get/nutr-log-suppl')
        def get_user_nutr_log_suppl(self, userid:str, date):
            return self.__domain.get_user_nutr_log_suppl(userid, date)

        ####17 get 사용자 영양 상태 로그 - 오늘부터 n일 (식단 + 영양제)
        @api_router.get('/get/nutr-log-ndays')
        def get_user_nutr_log_ndays(userid:str, ndays:int):
            return self.__domain.get_user_nutr_log_ndays(userid, ndays)

        ####18 get 사용자 영양 상태 로그 - 오늘부터 n일 (식단)
        @api_router.get('/get/fnutr-log-ndays')
        def get_user_nutr_log_meal_ndays(userid:str, ndays:int):
            return self.__domain.get_user_nutr_log_meal_ndays(userid, ndays)

        ####19 get 사용자 영양 상태 로그 - 오늘부터 n일 (영양제)
        @api_router.get('/get/nnutr-log-ndays')
        def get_user_nutr_log_suppl_ndays(userid:str, ndays:int):
            return self.__domain.get_user_nutr_log_suppl_ndays(userid, ndays)

        @api_router.get('/today/homepage/{userid}')
        def get_user_today_status(userid: str):
            return self.__domain.get_user_today_status(userid)
        
        @api_router.get('/week/status/{userid}')
        def get_user_week_status(userid:str):
            return self.__domain.get_user_week_status(userid)


        ####20 유저 영양제 추천
        @api_router.get('/recommend/nutrients/{userid}')
        def recommend_nutrients(userid: str, request):
            # request는 부족 영양소?
            return self.__domain.recommend_nutrients(userid, request)

        return api_router