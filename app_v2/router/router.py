from fastapi import APIRouter, HTTPException, status, UploadFile

from app_v2.domain.domain import NutrientsName

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
            try:
                return self.__domain.join_user(request)
            except:
                raise HTTPException(status_code= status.HTTP_406_NOT_ACCEPTABLE, detail= 'Please enter the appropriate format for the item')

        @api_router.put('/update/{userid}')
        def update_user_physique(userid: str, physique: physique):
            return self.__domain.update_user_physique(userid, physique)

        @api_router.delete('/delete/{userid}')
        def delete_user(userid: str):
            return self.__domain.delete_user(userid)

        @api_router.get('/info/{userid}')
        def get_user(userid):
            try:
                return self.__domain.get_user(userid)
            except:
                raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail= 'No exist userid')
        
        @api_router.put('/update/nutrients/{userid}')
        def update_user_nutr_suppl(userid, nutrsuppl: NutrientsName):
            return self.__domain.update_user_nutr_suppl(userid, nutrsuppl)
        
        @api_router.get('/get/RDI/{userid}')
        def get_user_RDI(userid: str):
            return self.__domain.get_user_RDI(userid)

        return api_router
        
class LogRouter:
    def __init__(self, domain: LogDomain):
        self.__domain= domain
    
    @property
    def router(self):
        api_router= APIRouter(prefix= '/log', tags= ['log'])

        # 이미지는 레포에서 s3로 이동?
        @api_router.put('/upload/image/{userid}')
        def upload_image(userid: str, image: UploadFile):
            return self.__domain.upload_image(userid, image)

        @api_router.put('/record/meal/{userid}')
        def record_meal(userid: str, big: str, small: str):
            return self.__domain.record_meal(userid, big, small)

        @api_router.post('/analyze/nutri/{userid}')
        def post_time_nutri(userid: str, request):
            #request는 임의로 설정한 그냥 하루 영양 섭취 정보입니다.(앱에서 가저오는)
            return self.__domain.post_time_nutri(userid, request)
        
        @api_router.get('/recommend/nutrients/{userid}')
        def recommend_nutrients(userid: str, request):
            # request는 부족 영양소?
            return self.__domain.recommend_nutrients(userid, request)

        return api_router