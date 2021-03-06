from collections import Counter
from app_v3.repository.tablename import *
from boto3.resources.base import ServiceResource
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr
from decimal import ROUND_HALF_UP, Decimal
import logging
import requests
import cv2
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from datetime import datetime, timedelta

from app_v3.yolov3_onnx_inf import detect

total= {
    'Protein': 0, 'Fat': 0, 'Carbohydrate': 0, 'Dietary_Fiber': 0, 'Calcium': 0,
    'Iron': 0, 'Magnesium': 0, 'Phosphorus': 0, 'Potassium': 0, 'Sodium': 0, 'Zinc': 0,
    'Copper': 0, 'Manganese': 0, 'Selenium': 0, 'Vitamin_A': 0, 'Vitamin_D': 0, 'Niacin': 0,
    'Folic_acid': 0, 'Vitamin_B12': 0, 'Vitamin_B6': 0, 'Vitamin_C': 0, 'Vitamin_E': 0,
    'Vitamin_K': 0, 'Leucine': 0, 'Iso_Leucine': 0, 'Histidine': 0, 'Linoleic_Acid': 0, 
    'Alpha_Linolenic_Acid': 0, 'Lysine': 0, 'Methionine': 0, 'Phenylalanine+Tyrosine': 0,
    'Threonine': 0, 'Valine': 0, 'Cholesterol': 0, 'Calories': 0
    }

pcf_status= {
    'Protein': 0, 'Fat': 0, 'Calories': 0, 'Carbohydrate': 0
    }

# fnames = ["pork_belly","ramen","bibimbap","champon","cold_noodle","cutlassfish","egg_custard",
#         "egg_soup","jajangmyeon","kimchi_stew","multigrain_rice",
#         "oxtail_soup","pickled spianch","pizza","pork_feet","quail_egg_stew","seasoned_chicken",
#         "seaweed_soup","soy_bean_paste_soup","stewed_bean","stewed_lotus_stew",
#         "stir_fried_anchovy","sitr_fried_pork","salad","ice_americano","Bottled_Beer","Canned_Beer",
#         "Draft_Beer","Fried_Chicken","Tteokbokki","Cabbage_Kimchi","Radish_Kimchi", "No_detect"]

fnames = ["삼겹살구이","라면","비빔밥","짬뽕","냉면","갈치조림","달걀찜",
        "달걀국","짜장면","김치찌개","잡곡밥",
        "설렁탕","시금치무침","피자","족발","메추리알장조림","양념치킨",
        "미역국","된장찌개","콩자반","연근조림",
        "멸치볶음","제육볶음","샐러드","아메리카노","맥주","맥주",
        "맥주","후라이드치킨","떡볶이","배추김치","깍두기"]

# 시간 : UtC -> 한국화
KST= timedelta(hours= 9)

class UserRepository:
    def __init__(self, db: ServiceResource)-> None:
        self.__db, self.__s3= db
        self.__table = self.__db.Table('table_name')

    '''
    유저 나이 별 RDI 분류
    --------
    생년월일 -> 나이 계산 -> 나이 별 RDI 기준으로 Partition Key 분류     
    '''
    @staticmethod
    def __get_rdi_pk(age):
        if age == 0:
            return 'RDI#0'
        elif age in range(1,3):
            return 'RDI#1-2'
        elif age in range(3,6):
            return 'RDI#3-5'
        elif age in range(6,9):
            return 'RDI#6-8'
        elif age in range(9,12):
            return 'RDI#9-11'
        elif age in range(12,15):
            return 'RDI#12-14'
        elif age in range(15,19):
            return 'RDI#15-18'
        elif age in range(19,30):
            return 'RDI#19-29'
        elif age in range(30,50):
            return 'RDI#30-49'
        elif age in range(50,65):
            return 'RDI#50-64'
        elif age in range(65,75):
            return 'RDI#65-74'
        elif age >=75:
            return 'RDI#75-'
        else:
            return None

    '''
    유저 RDI 계산
    --------
    나이 별 RDI 기준으로 Partition Key, 성 별 Sort Key -> 유저 별 1일 권장 섭취 칼로리 계산 -> 1일 권장 섭취 탄수화물, 단백질, 지방
    '''
    def __calculate_RDI(self, physique: dict) -> dict:
        user_birth = datetime.strptime(physique['birth'],'%Y-%m-%d')
        user_sex = physique['sex']
        user_height = physique['height']
        user_weight = physique['weight']
        user_pai = physique['PAI']

        today = (datetime.utcnow()+KST).date()
        cal_age= lambda birth: today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
        age = cal_age(user_birth)

        PK = self.__get_rdi_pk(age)
        SK = f'RDI#{user_sex}'

        temp_rdi = self.__table.get_item(
            Key={
                'PK': PK,
                'SK': SK
            }
        ).get('Item').get('RDI')

        if user_sex == 'M':
            cal = Decimal('66.47') + (Decimal('13.75')*user_weight) + (5*user_height) - (Decimal('6.76')*age)*user_pai
        elif user_sex == 'F':
            cal = Decimal('655.1') + (Decimal('9.56')*user_weight) + (Decimal('1.85')*user_height) - (Decimal('4.68')*age)*user_pai
        else:
            pass

        temp_rdi['Calories'] = Decimal(cal).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        temp_rdi['Carbohydrate'] = (Decimal('0.6')*Decimal(cal)/4).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        temp_rdi['Protein'] = (Decimal('0.17')*Decimal(cal)/4).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        temp_rdi['Fat'] = (Decimal('0.23')*Decimal(cal)/9).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        
        return temp_rdi
 
    '''
    신규 유저 가입
    --------
    Output== Input
    '''
    def join_user(self, request:dict):
        res= request.copy()
        userid = request.pop('userid')

        request['PK'] = f'USER#{userid}'
        request['SK'] = f'USER#{userid}#INFO'
        request['RDI'] = self.__calculate_RDI(request.get('physique'))
        request['nutr_suppl'] = list()

        self.__table.put_item(
            Item=request,
            ConditionExpression=Attr('PK').not_exists() & Attr('SK').not_exists()
        )
        return res

    '''
    유저 정보 업데이트 - physique, RDI 수정
    --------
    Output== Input의 physique
    --------
    '''
    def update_user_physique(self, userid: str, physique: dict):
        res= physique.copy()
        new_RDI = self.__calculate_RDI(physique)
        response = self.__table.update_item(
            Key={
                'PK': f'USER#{userid}',
                'SK': f'USER#{userid}#INFO'
            },
            UpdateExpression='''
                SET
                    physique.birth = :new_birth,
                    physique.sex = :new_sex,
                    physique.height = :new_height,
                    physique.weight = :new_weight,
                    physique.PAI = :new_PAI,
                    RDI = :new_RDI
            ''',
            ExpressionAttributeValues={
                ':new_birth' : physique.get('birth'),
                ':new_sex' : physique.get('sex'),
                ':new_height' : physique.get('height'),
                ':new_weight' : physique.get('weight'),
                ':new_PAI' : physique.get('PAI'),
                ':new_RDI' : new_RDI
            },
            ReturnValues='UPDATED_NEW'
        )
        return res

    '''
    유저 physique 정보 요청
    --------
    Output
    --------
    해당 userid의 physique 정보
    '''
    def get_user_physique(self, userid:str):
        response = self.__table.get_item(
            Key={
                'PK': f'USER#{userid}',
                'SK': f'USER#{userid}#INFO'
            },
            ProjectionExpression='physique'
        )
        return response.get('Item').get('physique')

    '''
    유저 정보 요청
    --------
    Output
    --------
    해당 userid 정보 전체
    '''
    def get_user(self, userid:str) -> dict:
        response = self.__table.get_item(
            Key={
                'PK': f'USER#{userid}',
                'SK': f'USER#{userid}#INFO'
            }
        )
        return response.get('Item')

    '''
    (앱 구현 X)
    유저 정보 삭제
    --------
    Output
    --------
    return f'{userid} is deleted'
    '''
    def delete_user(self, userid:str) -> str:
        response = self.__table.delete_item(
            Key={
                'PK': f'USER#{userid}',
                'SK': f'USER#{userid}#INFO'
            },
            ReturnValues='ALL_OLD'
        )
        return f'{userid} is deleted'

    '''
    유저 RDI 정보 요청
    --------
    Output
    --------
    해당 userid의 RDI 정보 
    '''
    def get_user_RDI(self, userid:str) -> dict:
        response = self.__table.get_item(
            Key={
                'PK': f'USER#{userid}',
                'SK': f'USER#{userid}#INFO'
            },
            ProjectionExpression='RDI'
        )
        return {i:round(float(v), 1) for i,v in response.get('Item').get('RDI').items()}

    '''
    (앱 구현 X)
    nutr_suppl 수정 - 유저 별 영양제 추가 등록 및 수정
    --------
    Output
    --------
    해당 userid의 섭취 영양제 목록 정보
    '''
    def update_user_nutr_suppl(self, userid:str, nutrsuppl:list) -> list:
        response = self.__table.update_item(
            Key={
                'PK': f'USER#{userid}',
                'SK': f'USER#{userid}#INFO'
            },
            UpdateExpression='''
                SET
                    nutr_suppl= list_append(nutr_suppl, :new_nutr_suppl)
            ''',
            ExpressionAttributeValues={
                ':new_nutr_suppl' : nutrsuppl
            },
            ReturnValues='UPDATED_NEW'
        )
        return response.get('Attributes').get('nutr_suppl')

    '''
    (앱 구현 X)
    유저 nutr_suppl 정보 요청
    --------
    Output
    --------
    해당 userid의 섭취 영양제 목록 정보
    '''
    def get_user_nutr_suppl(self, userid:str):
        response = self.__table.get_item(
            Key={
                'PK': f'USER#{userid}',
                'SK': f'USER#{userid}#INFO'
            },
            ProjectionExpression='nutr_suppl'
        )
        return response.get('Item').get('nutr_suppl')



class LogRepository:
    def __init__(self, db: ServiceResource)-> None:
        self.__db, self.__s3= db
        self.__table= self.__db.Table('table_name')

    '''
    S3 파일 서버에 presigned 저장 공간 생성 요청
    --------
    Input
    --------
    S3 bucket name,
    저장 경로 및 파일 이름,
    '''
    def create_presigned_post(self, bucket_name: str, key_name: str, 
            fields= None,
            conditions= None, expiration= 60):
        
        try:
            response = self.__s3.generate_presigned_post(
                bucket_name,
                key_name,
                Fields= fields,
                Conditions= conditions,
                ExpiresIn= expiration
            )
        except ClientError as e:
            logging.error(e)
            return None
        # The response contains the presigned URL and required fields
        return response

    '''
    S3 파일 서버에 presigned url 생성 요청
    --------
    Input
    --------
    S3 bucket name,
    저장 경로 및 파일 이름,
    '''
    def create_presigned_url(self, bucket_name: str, key_name: str, expiration= 3600):
        # Generate a presigned URL for the S3 object
        try:
            response= self.__s3.generate_presigned_url('get_object',
                                                        Params={'Bucket': bucket_name,
                                                                'Key': key_name},
                                                        ExpiresIn= expiration)
        except ClientError as e:
            logging.errer(e)
            return None
        # The response contains the presigned URL
        #print(response)
        return response

    '''
    식단 이미지 S3 파일 서버에 업로드
    --------
    Output
    --------
    return {'Origin_S3_key': 원본 이미지 S3 Image Key,
            'Class_type': [Inference 결과, ...],
            'S3_key': Inference 이미지 S3 Image Key,
            'link': presigned_url,
            'food_list': [[Class_type의 상세 음식 이름 정보 리스트], ...]}
    '''
    def upload_image(self, userid: str, image):
        #return f"{type(image)}"
        img= np.fromstring(image, dtype= np.uint8)
        dimg= cv2.imdecode(img, cv2.COLOR_RGB2BGR)
        _, dimg_byte = cv2.imencode('.jpg', dimg)
        kst_datetime = (datetime.utcnow() + KST).isoformat()

        origin_obj_name= f'{userid}/origin_{kst_datetime}.jpeg'
        origin_response= self.create_presigned_post('nutriai', origin_obj_name)
        if origin_response is None:
            exit(1)
        origin_files= {'file': (origin_obj_name, dimg_byte)}
        http_response= requests.post(origin_response['url'], data= origin_response['fields'], files= origin_files)

        # Inference
        _img, _class = detect.main(image)

        obj_name= f'{userid}/{kst_datetime}.jpeg'
        infer_response= self.create_presigned_post('nutriai', obj_name)
        if infer_response is None:
            exit(1)
        files= {'file': (obj_name, _img)}
        http_response= requests.post(infer_response['url'], data= infer_response['fields'], files= files)
        # If successful, returns HTTP status code 204
        logging.info(f'File upload HTTP status code: {http_response.status_code}')

        # url link
        url = self.create_presigned_url('nutriai', obj_name)
        if url is not None:
            url_response = requests.get(url)

        # get food list
        answer= []
        for name in _class:
            response= self.__table.query(
                        KeyConditionExpression= Key('PK').eq(f'FOOD#{fnames[name]}'),
                        ProjectionExpression= 'SK'
            )
            a= [i['SK'][5:] for i in response['Items']]
            b= []
            for i in a:
                b.append(i)
            #b.insert(0, fnames[name])
            answer.append(b)

        return {'Origin_S3_key': origin_obj_name,
                'Class_type': [fnames[name] for name in _class],
                'S3_key': obj_name,
                'link': url,
                'food_list': answer}

    '''
    Inference 이미지 S3 파일 서버에서 가져오기
    --------
    Output
    --------
    presigned_url
    '''
    def get_s3_url_file(self, obj_name: str):
        url = self.create_presigned_url('nutriai', obj_name)
        if url is not None:
            response = requests.get(url)
        
        print(response)
        return url

    '''
    음식 영양 성분 정보 요청
    --------
    Output
    --------
    해당 음식 영양 성분 정보
    '''
    def get_food_nutrients(self, food_cat: str, food_name: str):
        response = self.__table.get_item(
            Key={
                'PK': f'FOOD#{food_cat}',
                'SK': f'FOOD#{food_name}'
            },
            ProjectionExpression='nutrients'
        ).get('Item').get('nutrients')

        return response

    '''
    유저 식단 섭취 로그 등록
    --------
    Output
    --------
    Inference 해당 음식 영양 성분
    '''
    def post_meal_log(self, userid:str, image_key:str, class_list: list, food_list: list):
        kst_datetime = (datetime.utcnow() + KST)
        response_put= self.__table.put_item(
            Item={
                'PK': f'USER#{userid}',
                'SK': f'{kst_datetime.date().isoformat()}#MEAL#{kst_datetime.time().isoformat()}',
                'photo': image_key,
                'food_list': food_list
            }
        )
        response_nutr= Counter(total)
        for c, f in zip(class_list, food_list):
            nutr = self.get_food_nutrients(c, f)
            response_nutr+= Counter(nutr)

        for i in response_nutr.keys():  
            if i in pcf_status.keys():
                response_nutr[i]= round(float(response_nutr[i]))
            else:          
                response_nutr[i]= round(float(response_nutr[i]), 1)
         
        response= {'nutrients': response_nutr}
        # 음식 영양 성분
        return response

    '''
    사용자 영양상태 로그 요청 - 특정 날짜 (식단 - 탄단지)
    --------
    Output
    --------
    해당 userid의 입력 date의 섭취 칼로리, 탄수화물, 단백질, 지방
    '''
    def get_user_nutr_log_meal_CPF(self, userid:str, date) -> list:
        response = self.__table.query(
            KeyConditionExpression=Key('PK').eq(f'USER#{userid}') & Key('SK').eq(f'{date}#NUTRSTATUS#MEAL'),
            ExpressionAttributeNames={'#ns': 'nutr_status'},
            ProjectionExpression='SK, #ns.Calories, #ns.Carbohydrate, #ns.Protein, #ns.Fat'
        )
        return response.get('Items')

    '''
    사용자 영양 상태 로그 요청 - 오늘부터 ndays일 (식단 + 영양제)
    --------
    Output
    --------
    해당 userid의 ndays 간 평균 섭취 영양 성분 정보
    '''
    def get_user_nutr_log_ndays(self, userid:str, ndays:int) -> dict:
        kst_date = (datetime.utcnow() + KST).date()
        date_from = kst_date - timedelta(days=ndays-1)
        date_to = kst_date + timedelta(days=1)
        response = self.__table.query(
            KeyConditionExpression=Key('PK').eq(f'USER#{userid}') & Key('SK').between(f'{date_from}#NUTRSTATUS#',f'{date_to}#NUTRSTATUS#'),
            FilterExpression=Attr('nutr_status').exists(),
            ProjectionExpression='SK, nutr_status'
        ).get('Items')
        cnt_itmes= len(response)
        count= Counter(dict())
        for i in range(cnt_itmes):
            count += Counter(response[i].get('nutr_status'))
        count = dict(count)
        result= {key: round(float(count[key]/cnt_itmes), 1) for key in count.keys()}
        return result

    '''
    today homepage 필요 정보 요청
    --------
    Output
    --------
    해당 userid의 username,
    해당 userid의 RDI,
    오늘 섭취한 음식,
    오늘 섭취한 영양 성분 정보
    '''
    def get_user_today_status(self, userid:str):
        kst_date = (datetime.utcnow() + KST).date()
        # query (NUTRSTATUS#MEAL & #MEAL#)
        response_nutr = self.__table.query(
            KeyConditionExpression=Key('PK').eq(f'USER#{userid}') & Key('SK').begins_with(kst_date.isoformat()),
            FilterExpression=Attr('status_type').ne('SUPPLTAKE') & Attr('nutr_suppl_take').not_exists(),
            ExpressionAttributeNames={'#ns': 'nutr_status'},
            ProjectionExpression='SK, status_type, food_list, #ns' # ns.Calories, #ns.Carbohydrate, #ns.Protein, #ns.Fat'
        ).get('Items')
        response = self.__table.get_item(
            Key={
                'PK': f'USER#{userid}',
                'SK': f'USER#{userid}#INFO'
            },
            ProjectionExpression='username, RDI'
        ).get('Item')
        response['MEAL'] = list()
        for i, item in enumerate(response_nutr):
            if 'food_list' in item.keys():
                response['MEAL'].append([item['SK'].replace('#MEAL#','T'), item['food_list']])
            elif item['status_type'] == 'MEAL':
                response['nutr_status'] = item['nutr_status']
            else:
                pass

        return response

    '''
    a week status 필요 정보 요청
    --------
    Output
    --------
    해당 userid의 username,
    해당 userid의 RDI,
    일주일 간 섭취한 영양 성분 정보
    '''
    def get_user_week_status(self, userid:str):
        # query ( NUTRSTATUS )
        response_nutr = self.get_user_nutr_log_ndays(userid, 7)
        response = self.__table.get_item(
            Key={
                'PK': f'USER#{userid}',
                'SK': f'USER#{userid}#INFO'
            },
            ProjectionExpression='username, RDI'
        ).get('Item')
        response['nutr_status'] = response_nutr
        return response

    '''
    영양제 정보 요청
    --------
    Input - 영양제 타입과 상품 코드 입력
    --------
    nutr_cat: str
    product_code: str
    --------
    Output
    --------
    해당 영양제 정보(아이허브 링크 등...)
    '''
    def get_nutr_suppl(self, nutr_cat:str, product_code:str):
        response = self.__table.get_item(
            Key={
                'PK': f'NUTRSUPPL#{nutr_cat}',
                'SK': f'NUTRSUPPL#{product_code}'
            }
        )
        return response.get('Item')

    '''
    유저 영양제 추천
    --------
    Output
    --------
    미네랄, 비타민, 아미노산 타입 별 영양제 3종류 상품 코드,
    아이허브 링크 반환
    '''
    def get_recomm_nutrsuppl(self, userid: str):
        # user rdi data
        user_rdi = self.__table.get_item(
            Key={
                'PK': f'USER#{userid}',
                'SK': f'USER#{userid}#INFO'
            },
            ProjectionExpression='RDI, username'
        ).get('Item')
        user_rdi_sr = pd.Series(user_rdi.get('RDI'), dtype=float).drop(['Calories', 'Folic_acid', 'Carbohydrate', 'Protein', 'Fat'])
        # user week status
        user_status = self.get_user_nutr_log_ndays(userid, 7)
        user_status_sr = pd.Series(user_status, dtype=float).drop(['Calories', 'Folic_acid', 'Carbohydrate', 'Protein', 'Fat', 'Cholesterol'])
        # diff rat
        user_diffrat = pd.Series(((user_rdi_sr - user_status_sr) / user_rdi_sr) / 100., dtype=float, name='user')
        user_diffrat.fillna(0, inplace=True)
        # standard columns
        std_col = user_diffrat.index

        # nutrition supplements data
        response = dict()
        response['name']= user_rdi.get('username')
        nutrsuppl_cat = ['amino-acids','minerals','vitamins']
        for cat in nutrsuppl_cat:
            suppl_list = self.__table.query(
                KeyConditionExpression=Key('PK').eq(f'NUTRSUPPL#{cat}'),
                ProjectionExpression='SK, nutrients'
            ).get('Items')

            temp_list = list()
            for suppl in suppl_list:
                suppl['nutrients']['prod_cd'] = suppl.pop('SK').replace('NUTRSUPPL#','')
                temp_list.append(suppl['nutrients'])
            suppl_df = pd.DataFrame(pd.DataFrame(temp_list).set_index('prod_cd'), columns=std_col, dtype=float).fillna(0)
            suppl_rat_df = (suppl_df/user_rdi_sr) / 100.

            if cat in ['amino-acids','vitamins']:
                # SSE
                suppl_sse = suppl_rat_df.apply(lambda row : np.sum((row - user_diffrat)**2), axis=1)
                prod_code = list(suppl_sse.sort_values().index[0:3])
                print(prod_code)
                supp_pd_list = list()
                for cd in prod_code:
                    supp_pd_list.append(self.get_nutr_suppl(cat, cd))
                response[cat] = supp_pd_list
            elif cat == ['minerals']:
                # 코사인 유사도
                test_cosim_df = suppl_rat_df.append(user_diffrat).fillna(0)
                test_cosim_df['cosim'] = cosine_similarity(test_cosim_df,test_cosim_df)[:,-1]
                prod_code = list(test_cosim_df.sort_values(by='cosim', ascending=False).index[1:4])
                supp_pd_list = list()
                print(prod_code)
                for cd in prod_code:
                    supp_pd_list.append(self.get_nutr_suppl(cat, cd))
                response[cat] = supp_pd_list
            else:
                pass
        return response
