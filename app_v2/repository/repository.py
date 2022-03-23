from collections import Counter
from urllib import response
from boto3.resources.base import ServiceResource
from botocore.exceptions import ClientError
from fastapi.responses import JSONResponse
from boto3.dynamodb.conditions import Key, Attr
from decimal import ROUND_HALF_UP, ROUND_UP, Decimal
import os
import logging
import requests
import cv2
import numpy as np
import boto3
import json
import re

from datetime import date, datetime, timedelta

from app_v2.yolov3_onnx_inf import detect

total= {
    'Protein': 0, 'Fat': 0, 'Carbohydrate': 0, 'Dietary_Fiber': 0, 'Calcium': 0,
    'Iron': 0, 'Magnesium': 0, 'Phosphorus': 0, 'Potassium': 0, 'Sodium': 0, 'Zinc': 0,
    'Copper': 0, 'Manganese': 0, 'Selenium': 0, 'Vitamin_A': 0, 'Vitamin_D': 0, 'Niacin': 0,
    'Folic_acid': 0, 'Vitamin_B12': 0, 'Vitamin_B6': 0, 'Vitamin_C': 0, 'Vitamin_E': 0,
    'Vitamin_K': 0, 'Leucine': 0, 'Iso_Leucine': 0, 'Histidine': 0, 'Linoleic_Acid': 0, 
    'Alpha_Linolenic_Acid': 0, 'Lysine': 0, 'Methionine': 0, 'Phenylalanine+Tyrosine': 0,
    'Threonine': 0, 'Valine': 0, 'Cholesterol': 0
    }

# fnames = ["pork_belly","ramen","bibimbap","champon","cold_noodle","cutlassfish","egg_custard",
#         "egg_soup","jajangmyeon","kimchi_stew","multigrain_rice",
#         "oxtail_soup","pickled spianch","pizza","pork_feet","quail_egg_stew","seasoned_chicken",
#         "seaweed_soup","soy_bean_paste_soup","stewed_bean","stewed_lotus_stew",
#         "stir_fried_anchovy","sitr_fried_pork","salad","ice_americano","Bottled_Beer","Canned_Beer",
#         "Draft_Beer","Fried_Chicken","Tteokbokki","Cabbage_Kimchi","Radish_Kimchi", "No_detect"]

fnames = ["삼겹살구이","라면","비빔밥","짬뽕","냉면","갈치조림","계란찜",
        "계란국","짜장면","김치찌개","잡곡밥",
        "설렁탕","시금치무침","피자","족발","메추리알장조림","양념치킨",
        "미역국","된장찌개","콩자반","연근조림",
        "멸치볶음","제육볶음","샐러드","아메리카노","맥주","맥주",
        "맥주","후라이드치킨","떡볶이","배추김치","깍두기", "No_detect"]

class UserRepository:
    def __init__(self, db: ServiceResource)-> None:
        self.__db, self.__s3= db
        self.__table = self.__db.Table('nutriai_test')

    def __get_rdi_pk(self, age):
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

    ##### RDI 계산
    def __calculate_RDI(self, physique: dict) -> dict:
        user_birth = datetime.strptime(physique['birth'],'%Y-%m-%d')
        user_sex = physique['sex']
        user_height = physique['height']
        user_weight = physique['weight']
        user_pai = physique['PAI']

        today = date.today()
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
        # temp_rdi['Calories'] = cal
        # temp_rdi['Carbohydrate'] = Decimal('0.6')*cal/4
        # temp_rdi['Protein'] = Decimal('0.17')*cal/4
        # temp_rdi['Fat'] = Decimal('0.23')*cal/9
        
        return temp_rdi
        
    ####1 신규 유저 가입
    # input: userid, physique{}
    # output: {physique, RDI}
    def join_user(self, request:dict):
        res= request.copy()
        userid = request.pop('userid')

        request['PK'] = f'USER#{userid}'
        request['SK'] = f'USER#{userid}#INFO'
        #physique= request.get('physique')
        request['RDI'] = self.__calculate_RDI(request.get('physique'))
        request['nutr_suppl'] = list()

        self.__table.put_item(
            Item=request,
            ConditionExpression=Attr('PK').not_exists() & Attr('SK').not_exists()
        )
        return res



    ####2 유저 정보 업데이트 - physique, RDI 수정
    # input: userid, physique{}
    # output: {physique, RDI}
    def update_user_physique(self, userid:str, physique:dict):
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
        #return response.get('Attributes')
        return res

    ####3 유저 physique 정보 요청
    # input: userid
    # output: physique value
    def get_user_physique(self, userid:str):
        response = self.__table.get_item(
            Key={
                'PK': f'USER#{userid}',
                'SK': f'USER#{userid}#INFO'
            },
            ProjectionExpression='physique'
        )
        return response.get('Item').get('physique')

    ####4 유저 정보 요청
    # input: userid
    # output: {user item}
    def get_user(self, userid:str) -> dict:
        response = self.__table.get_item(
            Key={
                'PK': f'USER#{userid}',
                'SK': f'USER#{userid}#INFO'
            }
        )
        return response.get('Item')

    ####5 유저 정보 삭제
    # input : userID
    # output : username
    def delete_user(self, userid:str) -> str:
        response = self.__table.delete_item(
            Key={
                'PK': f'USER#{userid}',
                'SK': f'USER#{userid}#INFO'
            },
            ReturnValues='ALL_OLD'
        )
        #return response.get('Attributes').get('userid')
        return f'{userid} is deleted'

    ####6 유저 RDI 정보 요청
    # input: userid
    # output: RDI value
    def get_user_RDI(self, userid:str) -> dict:
        response = self.__table.get_item(
            Key={
                'PK': f'USER#{userid}',
                'SK': f'USER#{userid}#INFO'
            },
            ProjectionExpression='RDI'
        )
        return {i:round(float(v),1) for i,v in response.get('Item').get('RDI').items()}

    ####7 nutr_suppl 수정 - 영양제 추가 등록 및 수정
    # input: userid, nutr_suppl(prod_code 만 있는 리스트)
    # output: nutr_suppl
    def update_user_nutr_suppl(self, userid:str, nutrsuppl:list) -> list:
        response = self.__table.update_item(
            Key={
                'PK': f'USER#{userid}',
                'SK': f'USER#{userid}#INFO'
            },
            UpdateExpression='''
                SET
                    nutr_suppl = :new_nutr_suppl
            ''',
            ExpressionAttributeValues={
                ':new_nutr_suppl' : nutrsuppl
            },
            ReturnValues='UPDATED_NEW'
        )
        return response.get('Attributes').get('nutr_suppl')

    ####8 유저 nutr_suppl 정보 요청
    # input: userid
    # output: nutr_suppl value
    def get_user_nutr_suppl(self, userid:str):
        response = self.__table.get_item(
            Key={
                'PK': f'USER#{userid}',
                'SK': f'USER#{userid}#INFO'
            },
            ProjectionExpression='nutr_suppl'
        )
        return response.get('Item').get('nutr_suppl')

    ####9 search nutr_suppl list
    def get_nutr_suppl_list(self, search: str):
        response = self.__table.query(
            KeyConditionExpression= Key('PK').eq('NUTRSPPL'),
            FilterExpression= Attr('title').contains(search)
        )
        return response.get('Items')


class LogRepository:
    def __init__(self, db: ServiceResource)-> None:
        self.__db, self.__s3= db
        self.__table= self.__db.Table('nutriai_test')

    #### S3 저장 공간 생성? 
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

    #### S3 url 접속 권한
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
        print(response)
        return response

    ####1 이미지 S3에 업로드
    def upload_image(self, userid: str, image):
        #return f"{type(image)}"
        img= np.fromstring(image, dtype= np.uint8)
        dimg= cv2.imdecode(img, cv2.COLOR_RGB2BGR)
        _, dimg_byte = cv2.imencode('.jpg', dimg)

        origin_obj_name= f'{userid}/origin_{datetime.now().isoformat()}.jpeg'
        origin_response= self.create_presigned_post('nutriai', origin_obj_name)
        if origin_response is None:
            exit(1)
        origin_files= {'file': (origin_obj_name, dimg_byte)}
        http_response= requests.post(origin_response['url'], data= origin_response['fields'], files= origin_files)

        # Inference
        _img, _class = detect.main(image)

        obj_name= f'{userid}/{datetime.now().isoformat()}.jpeg'
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
    
    # s3 키 접속 권한
    def get_s3_url_file(self, userid: str, obj_name: str):
        url = self.create_presigned_url('nutriai', obj_name)
        if url is not None:
            response = requests.get(url)
        
        print(response)
        return url

    ######### FOOOD 
    ####2 음식 영양 성분 정보 요청
    def get_food_nutrients(self, food_cat:str, food_name: str):
        response = self.__table.get_item(
            Key={
                'PK': f'FOOD#{food_cat}',
                'SK': f'FOOD#{food_name}'
            },
            ProjectionExpression='nutrients'
        )
        nutr_info= response
        for i in total.keys():
            if i in nutr_info.keys():
                total[i]= round(float(nutr_info[i]), 1)
            else:
                total[i]= 0
        return total

    ####### MEAL log ##########
    ####3 유저 식단 섭취 로그 등록 ##
    ###########################
    def post_meal_log(self, userid:str, image_key:str, class_list, food_list):
        dt = datetime.now()
        response = self.__table.put_item(
            Item={
                'PK': f'USER#{userid}',
                'SK': f'{dt.date().isoformat()}#MEAL#{dt.time().isoformat()}',
                'photo': image_key,
                'food_list': food_list
            }
        )
        for c, f in zip(class_list, food_list):
            nutr = self.get_food_nutrients(c, f)
            self.update_user_meal_nutr_log(userid, nutr)
        return None ####

    # update 식단 로그, 음식 리스트만 수정
    # input : userID, datetime(isoformat), new food list
    # output : updated food list
    def update_meal_log_food_list(self, userid:str, dt, new_food_list:list) -> list:
        response = self.__table.update_item(
            Key={
                'PK': f'USER#{userid}',
                'SK': f'{dt.date().isoformat()}#MEAL#{dt.time().isoformat()}'
            },
            UpdateExpression='''
                SET
                    food_list = :new_food_list
            ''',
            ExpressionAttributeValues={
                ':new_food_list' : new_food_list
            },
            ReturnValues='UPDATED_NEW'
        )
        return response.get('Attributes').get('food_list')
    
    ####4 유저 식단 섭취 로그 정보 요청 - 특정 날
    def get_meal_log(self, userid:str, date) -> list:
        response = self.__table.query(
            KeyConditionExpression=Key('PK').eq(f'USER#{userid}') & Key('SK').begins_with(f'{date}#MEAL#'),
            ProjectionExpression='SK, photo, food_list'
        )
        return response.get('Items')
    
    ####5 유저 식단 섭취 로그 정보 삭제 - 특정 시간(시기)
    def delete_meal_log(self, userid:str, dt):
        response = self.__table.delete_item(
            Key={
                'PK': f'USER#{userid}',
                'SK': f'{dt.date().isoformat()}#MEAL#{dt.time().isoformat()}'
            },
            # ReturnValues='ALL_OLD'
        )
        return response
    
    ####### NUTR SUPPL 
    ####6 영양제 영양성분 정보 요청
    def get_nutr_suppl_nutrients(self, nutr_cat:str, product_code:str):
        response = self.__table.get_item(
            Key={
                'PK': f'NUTRSUPPL#{nutr_cat}',
                'SK': f'NUTRSUPPL#{product_code}'
            },
            ProjectionExpression='nutrients'
        )
        nutr_info= response.get('Item').get('nutrients')
        for i in total.keys():
            if i in nutr_info.keys():
                total[i]= round(float(nutr_info[i]), 1)
            else:
                total[i]= 0
                
        return total

    ####### NUTRTAKE log
    ####7 유저 영양제 섭취 로그 등록
    def post_nutrtake_log(self, userid:str, nutr_suppl_list:dict):
        dt = datetime.now()
        response = self.__table.put_item(
            Item={
                'PK': f'USER#{userid}',
                'SK': f'{dt.date().isoformat()}#SUPPLTAKE#{dt.time().isoformat()}',
                'nutr_suppl_take': nutr_suppl_list
            }
        )
        return response
    
    ####8 update 영양제 섭취 로그에서 영양제 변경
    # input : userID, datetime, new supplement list
    # output : updated supplement
    def update_nutrtake_log_suppl_list(self, userid:str, dt, new_suppl_list:list) -> list:
        response = self.__table.update_item(
            Key={
                'PK': f'USER#{userid}',
                'SK': f'{dt.date().isoformat()}#SUPPLTAKE#{dt.time().isoformat()}'
            },
            UpdateExpression='''
                SET
                    nutr_suppl_take = :new_nutr_suppl_take
            ''',
            ExpressionAttributeValues={
                ':new_nutr_suppl_take' : new_suppl_list
            },
            ReturnValues='UPDATED_NEW'
        )
        return response.get('Attributes').get('nutr_suppl_take')

    ####9 유저 영양제 섭취 로그 정보 요청 - 특정 날
    def get_nutrtake_log(self, userid:str, date) -> list:
        response = self.__table.query(
            KeyConditionExpression=Key('PK').eq(f'USER#{userid}') & Key('SK').begins_with(f'{date}#SUPPLTAKE#'),
            ProjectionExpression='SK, nutr_suppl_take'
        )
        return response.get('Items')
    
    ####10 유저 영양제 섭취 로그 삭제 - 특정 시간(시기)
    def delete_nutrtake_log(self, userid:str, dt):
        response = self.__table.delete_item(
            Key={
                'PK': f'USER#{userid}',
                'SK': f'{dt.date().isoformat()}#SUPPLTAKE#{dt.time().isoformat()}'
            },
            # ReturnValues='ALL_OLD'
        )
        return f'{datetime} record of {userid} is deleted'

##################
    ####11 유저 영양 상태 식단 로그 입력 & 업데이트
    def update_user_meal_nutr_log(self, userid:str, food_nutrients:dict):
        old_status = self.__table.get_item(
            Key={
                'PK': f'USER#{userid}',
                'SK': f'{date.today()}#NUTRSTATUS#MEAL'
            }
        ).get('Item').get('nutr_status')
        new_status = Counter(old_status) + Counter(food_nutrients)

        response = self.__table.update_item(
            Key={
                'PK': f'USER#{userid}',
                'SK': f'{date.today()}#NUTRSTATUS#MEAL'
            },
            UpdateExpression='''
                SET
                    nutr_status = :new_nutr_status,
                    status_type = :type
            ''',
            ExpressionAttributeValues={
                ':new_nutr_status' : new_status,
                ':type' : 'MEAL'
            },
            ReturnValues='ALL_NEW'
        )
        return response.get('Attributes')

    ####12 유저 영샹 상태 영양제 로그 입력 & 업데이트
    def update_user_nutrtake_nutr_log(self, userid:str, suppl_nutrients:dict):
        old_status = self.__table.get_item(
            Key={
                'PK': f'USER#{userid}',
                'SK': f'{date.today()}#NUTRSTATUS#SUPPLTAKE'
            }
        ).get('Item').get('nutr_status')
        new_status = Counter(old_status) + Counter(suppl_nutrients)

        response = self.__table.update_item(
            Key={
                'PK': f'USER#{userid}',
                'SK': f'{date.today()}#NUTRSTATUS#SUPPLTAKE'
            },
            UpdateExpression='''
                SET
                    nutr_status = :new_nutr_status,
                    status_type = :type
            ''',
            ExpressionAttributeValues={
                ':new_nutr_status' : new_status,
                ':type' : 'SUPPLTAKE'
            },
            ReturnValues='ALL_NEW'
        )
        return response.get('Attributes')

    ####13 get 사용자 영양상태 로그 - 특정 날짜 (식단 + 영양제)
    # input : userID, date
    # output : {nutr_status}
    def get_user_nutr_log(self, userid:str, date) -> dict:
        response = self.__table.query(
            KeyConditionExpression=Key('PK').eq(f'USER#{userid}') & Key('SK').begins_with(f'{date}#NUTRSTATUS#'),
            ProjectionExpression='SK, nutr_status'
        ).get('Items')
        result = Counter(dict())
        for i in range(len(response)):
            result += Counter(response[i].get('nutr_status'))
        return result

    ####14 get 사용자 영양상태 로그 - 특정 날짜 (식단)
    # input : userID, date
    # output : {SK, nutr_status}
    def get_user_nutr_log_meal(self, userid:str, date) -> list:
        response = self.__table.query(
            KeyConditionExpression=Key('PK').eq(f'USER#{userid}') & Key('SK').eq(f'{date}#NUTRSTATUS#MEAL'),
            ProjectionExpression='SK, nutr_status'
        )
        return response.get('Items')
    
    ####15 get 사용자 영양상태 로그 - 특정 날짜 (식단 - 탄단지)
    # input : userID, date
    # output : 
    def get_user_nutr_log_meal_CPF(self, userid:str, date) -> list:
        response = self.__table.query(
            KeyConditionExpression=Key('PK').eq(f'USER#{userid}') & Key('SK').eq(f'{date}#NUTRSTATUS#MEAL'),
            ExpressionAttributeNames={'#ns': 'nutr_status'},
            ProjectionExpression='SK, #ns.Calories, #ns.Carbohydrate, #ns.Protein, #ns.Fat'
        )
        return response.get('Items')

    ####16 get 사용자 영양상태 로그 - 특정 날짜 (영양제)
    # input : userID, date
    # output : 
    def get_user_nutr_log_suppl(self, userid:str, date) -> list:
        response = self.__table.query(
            KeyConditionExpression=Key('PK').eq(f'USER#{userid}') & Key('SK').eq(f'{date}#NUTRSTATUS#SUPPLTAKE'),
            ProjectionExpression='SK, nutr_status'
        )
        return response.get('Items')

    ####17 get 사용자 영양 상태 로그 - 오늘부터 n일 (식단 + 영양제)
    # input : userID, number of days
    # output :
    def get_user_nutr_log_ndays(self, userid:str, ndays:int) -> dict:
        date_from = date.today() - timedelta(days=ndays-1)
        date_to = date.today() + timedelta(days=1)
        response = self.__table.query(
            KeyConditionExpression=Key('PK').eq(f'USER#{userid}') & Key('SK').between(f'{date_from}#NUTRSTATUS#',f'{date_to}#NUTRSTATUS#'),
            FilterExpression=Attr('nutr_status').exists(),
            ProjectionExpression='SK, nutr_status'
        ).get('Items')
        result = Counter(dict())
        for i in range(len(response)):
            result += Counter(response[i].get('nutr_status'))
        return dict(result)

    ####18 get 사용자 영양 상태 로그 - 오늘부터 n일 (식단)
    # input : userID, number of days
    # output :
    def get_user_nutr_log_meal_ndays(self, userid:str, ndays:int) -> dict:
        date_from = date.today() - timedelta(days=ndays-1)
        date_to = date.today() + timedelta(days=1)
        response = self.__table.query(
            KeyConditionExpression=Key('PK').eq(f'USER#{userid}') & Key('SK').between(f'{date_from}#NUTRSTATUS#',f'{date_to}#NUTRSTATUS#'),
            FilterExpression=Attr('status_type').eq('MEAL'),
            ProjectionExpression='SK'
        ).get('Items')
        result = Counter(dict())
        for i in range(len(response)):
            result += Counter(response[i].get('nutr_status'))
        return dict(result)

    ####19 get 사용자 영양 상태 로그 - 오늘부터 n일 (영양제)
    # input : userID, number of days
    # output :
    def get_user_nutr_log_suppl_ndays(self, userid:str, ndays:int) -> dict:
        date_from = date.today() - timedelta(days=ndays-1)
        date_to = date.today() + timedelta(days=1)
        response = self.__table.query(
            KeyConditionExpression=Key('PK').eq(f'USER#{userid}') & Key('SK').between(f'{date_from}#NUTRSTATUS#',f'{date_to}#NUTRSTATUS#'),
            FilterExpression=Attr('status_type').eq('SUPPLTAKE'),
            ProjectionExpression='SK, nutr_status'
        ).get('Items')
        for i in range(len(response)):
            result += Counter(response[i].get('nutr_status'))
        return dict(result)

    ####20 유저 영양제 추천
    def recommend_nutrients(self, userid: str, request):
        #부족 영양소로 db 영양제 정보에 어떻게 접근??
        return


    # today status query
    def get_user_today_status(self, userid:str):
        # query (NUTRSTATUS#MEAL & #MEAL#)
        response_nutr = self.__table.query(
            KeyConditionExpression=Key('PK').eq(f'USER#{userid}') & Key('SK').begins_with(date.today().isoformat()),
            FilterExpression=Attr('status_type').ne('SUPPLTAKE') & Attr('nutr_suppl_take').not_exists(),
            ExpressionAttributeNames={'#ns': 'nutr_status'},
            ProjectionExpression='SK, status_type, food_list, #ns' # .Calories, #ns.Carbohydrate, #ns.Protein, #ns.Fat'
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


    # 1 week status query
    # output: {'username','RDI','nutr_status'}
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