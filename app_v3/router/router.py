from fastapi import APIRouter, HTTPException, status, UploadFile, File

from app_v3.domain.domain import NutrientsName

from app_v3.domain.domain import UserDomain, LogDomain, UserJoinModel, physique, MealLog

class UserRouter:
    def __init__(self, domain: UserDomain):
        self.__domain= domain

    @property
    def router(self):
        api_router= APIRouter(prefix= '/user', tags= ['user'])

        @api_router.get('/')
        def root():
            return 'Welcome Here!'

        '''
        신규 유저 가입
        --------
        Input
        --------
        UserJoinModel= 
        { userid: str
          username: str
          physique: { birth: str,
                      sex: str,
                      height: Decimal,
                      weight: Decimal,
                      PAI: Decimal,
                        }
            }
        '''
        @api_router.post('/join')
        def join_user(request: UserJoinModel):
            try:
                return self.__domain.join_user(request)
            except:
                raise HTTPException(status_code= status.HTTP_406_NOT_ACCEPTABLE, detail= 'Please enter the appropriate format for the item')

        '''
        유저 정보 업데이트 - physique, RDI 수정
        --------
        Input
        --------
        userid: str,
        physique= 
        { birth: str,
          sex: str,
          height: Decimal,
          weight: Decimal,
          PAI: Decimal, 
            }
        '''
        @api_router.put('/update/{userid}')
        def update_user_physique(userid: str, physique: physique):
            return self.__domain.update_user_physique(userid, physique)

        '''
        유저 physique 정보 요청
        --------
        Input
        --------
        userid: str
        '''
        @api_router.get('/get/physique/{userid}')
        def get_user_physique(userid: str):
            return self.__domain.get_user_physique(userid)

        '''
        유저 정보 요청
        --------
        Input
        --------
        userid: str
        '''
        @api_router.get('/info/{userid}')
        def get_user(userid):
            try:
                return self.__domain.get_user(userid)
            except:
                raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail= 'No exist userid')

        '''
        (앱 구현 X)
        유저 정보 삭제
        --------
        Input
        --------
        userid: str
        '''
        @api_router.delete('/delete/{userid}')
        def delete_user(userid: str):
            return self.__domain.delete_user(userid)

        '''
        유저 RDI 정보 요청
        --------
        Input
        --------
        userid: str
        '''
        @api_router.get('/get/RDI/{userid}')
        def get_user_RDI(userid: str):
            return self.__domain.get_user_RDI(userid)

        '''
        (앱 구현 X)
        nutr_suppl 수정 - 유저 별 영양제 추가 등록 및 수정
        --------
        Input
        --------
        userid: str,
        NutrientsName=
        nutrition_supplements: List[str]
        '''
        @api_router.put('/update/nutrients/{userid}')
        def update_user_nutr_suppl(userid: str, nutrsuppl: NutrientsName):
            return self.__domain.update_user_nutr_suppl(userid, nutrsuppl.dict())
        
        '''
        (앱 구현 X)
        유저 nutr_suppl 정보 요청
        --------
        Input
        --------
        userid: str
        '''
        @api_router.get('/get/nutr/suppl/{userid}')
        def get_user_nutr_suppl(userid: str):
            return self.__domain.get_user_nutr_suppl(userid)


        return api_router
        
class LogRouter:
    def __init__(self, domain: LogDomain):
        self.__domain= domain
    
    @property
    def router(self):
        api_router= APIRouter(prefix= '/log', tags= ['log'])

        '''
        식단 이미지 S3 파일 서버에 업로드
        --------
        Input
        --------
        userid: str,
        image: bytes
        '''
        @api_router.post('/upload/image/{userid}')
        def upload_image(userid: str, image: bytes= File(...)):
            return self.__domain.upload_image(userid, image)

        '''
        Inference 이미지 S3 파일 서버에서 가져오기
        --------
        Input
        --------
        obj_name: Inference 이미지 S3 Image Key
        '''
        @api_router.get('/get/s3-url')
        def get_s3_url_file(obj_name: str):
            return self.__domain.get_s3_url_file(obj_name)

        
        '''
        음식 영양 성분 요청 
        --------
        Input - Inference 결과의 Class_type, Class_type의 상세 음식 이름
        --------
        food_cat: str,
        food_name: str
        '''
        @api_router.get('/get/food')
        def get_food(food_cat: str, food_name: str):
            return self.__domain.get_food(food_cat, food_name)

        '''
        유저 식단 섭취 로그 등록
        --------
        Input
        --------
        userid: str,
        request: MealLog=
        { image_key: str
          class_list: List[str]
          food_list: List[str] 
          }
        '''
        @api_router.post('/post/meal/log/{userid}')
        def post_meal_log(userid: str, request: MealLog):
            return self.__domain.post_meal_log(userid, request.dict())

        '''
        사용자 영양상태 로그 요청 - 특정 날짜 (식단 - 탄단지)
        --------
        Input
        --------
        userid: str,
        date: yyyy-mm-dd 형식
        '''
        @api_router.get('/get/nutr-log-meal-cpf')
        def get_user_nutr_log_meal_CPF(userid: str, date):
            return self.__domain.get_user_nutr_log_meal_CPF(userid, date)

     
        '''
        사용자 영양 상태 로그 요청 - 오늘부터 ndays일 (식단 + 영양제)
        --------
        Input
        --------
        userid: str,
        ndays: int 
        '''
        @api_router.get('/get/nutr-log-ndays')
        def get_user_nutr_log_ndays(userid: str, ndays: int):
            return self.__domain.get_user_nutr_log_ndays(userid, ndays)

        '''
        today homepage 필요 정보 요청
        --------
        Input
        --------
        userid: str,
        '''
        @api_router.get('/today/homepage/{userid}')
        def get_user_today_status(userid: str):
            return self.__domain.get_user_today_status(userid)
        
        '''
        a week status 필요 정보 요청
        --------
        Input
        --------
        userid: str,
        '''
        @api_router.get('/week/status/{userid}')
        def get_user_week_status(userid:str):
            return self.__domain.get_user_week_status(userid)

        '''
        유저 영양제 추천
        --------
        Input
        --------
        userid: str,
        '''
        @api_router.get('/recommend/nutrients/{userid}')
        def get_recomm_nutrsuppl(userid: str):
            return self.__domain.get_recomm_nutrsuppl(userid)

        @api_router.get('/get/barcode/product')
        def get_barcode_data(bcode: str):
            return self.__domain.get_barcode_data(bcode)

        @api_router.post('/barcode/product/{userid}/{bcode}')
        def log_barcode_product(userid: str, bcode: str):
            return self.__domain.log_barcode_product(userid, bcode)

        return api_router