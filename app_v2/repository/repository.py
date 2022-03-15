from tkinter import image_types
from urllib import response
from boto3.resources.base import ServiceResource
from botocore.exceptions import ClientError
from fastapi.responses import JSONResponse
from boto3.dynamodb.conditions import Key, Attr
from decimal import Decimal
import os
import logging

from datetime import date, datetime

#from app_v2.yolov3_onnx_main import detect_nutriai

total= {
    'Protein': 0, 'Fat': 0, 'Carbohydrate': 0, 'Dietary_Fiber': 0, 'Calcium': 0,
    'Iron': 0, 'Magnesium': 0, 'Phosphorus': 0, 'Potassium': 0, 'Sodium': 0, 'Zinc': 0,
    'Copper': 0, 'Manganese': 0, 'Selenium': 0, 'Vitamin_A': 0, 'Vitamin_D': 0, 'Niacin': 0,
    'Folic_acid': 0, 'Vitamin_B12': 0, 'Vitamin_B6': 0, 'Vitamin_C': 0, 'Vitamin_E': 0,
    'Vitamin_K': 0, 'Leucine': 0, 'Iso_Leucine': 0, 'Histidine': 0, 'Linoleic_Acid': 0, 'Alpha_Linolenic_Acid': 0, 'Lysine': 0, 'Methionine': 0, 'Phenylalanine+Tyrosine': 0,
    'Threonine': 0, 'Valine': 0, 'Cholesterol': 0
    }

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

        temp_rdi['Calories'] = Decimal(cal)
        temp_rdi['Carbohydrate'] = Decimal('0.6')*Decimal(cal)/4
        temp_rdi['Protein'] = Decimal('0.17')*Decimal(cal)/4
        temp_rdi['Fat'] = Decimal('0.23')*Decimal(cal)/9
        # temp_rdi['Calories'] = cal
        # temp_rdi['Carbohydrate'] = Decimal('0.6')*cal/4
        # temp_rdi['Protein'] = Decimal('0.17')*cal/4
        # temp_rdi['Fat'] = Decimal('0.23')*cal/9
        
        return temp_rdi
        
    ####1 신규 유저 가입
    # input: userid, physique{}
    # output: {physique, RDI}
    def join_user(self, request:dict):
        userid = request.pop('userid')

        request['PK'] = f'USER#{userid}'
        request['SK'] = f'USER#{userid}#INFO'
        #physique= request.get('physique')
        request['RDI'] = self.__calculate_RDI(request.get('physique'))
        request['nutr_suppl'] = list()

        response = self.__table.put_item(
            Item=request,
            ConditionExpression=Attr('PK').not_exists() & Attr('SK').not_exists()
        )
        return response



    ####2 유저 정보 업데이트 - physique, RDI 수정
    # input: userid, physique{}
    # output: {physique, RDI}
    def update_user_physique(self, userid:str, physique:dict):
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
        return response.get('Attributes')

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
        return response.get('Attributes').get('userid')

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
        return response.get('Item').get('RDI')

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
    def get_user_nutr_suppl(self, userid:str) -> dict:
        response = self.__table.get_item(
            Key={
                'PK': f'USER#{userid}',
                'SK': f'USER#{userid}#INFO'
            },
            ProjectionExpression='nutr_suppl'
        )
        return response.get('Item').get('nutr_suppl')

    # search nutr_suppl
    # input: search word
    # output: [{'prod_name': ...}, {}, .. ]
    ####################3
    # def get_nutr_suppls(self, search:str) -> list:
    #     response = self.__table.query(
    #         KeyConditionExpression=Key('PK').eq('NUTRSUPPL'),
    #         FilterExpression=Attr('prod_name').contains(search),
    #     )
    #     return response.get('Items')

class LogRepository:
    def __init__(self, db: ServiceResource)-> None:
        self.__db, self.__s3= db
        self.__table= self.__db.Table('nutriai_test')

    ####1 이미지 S3에 업로드
    def upload_image(self, userid: str, image):
        s3= self.__s3
        obj_path= os.path.basename(image.filename)
        try: 
            s3.Bucket('nutriai').upload_fileobj(image.file, f'{userid}/{obj_path}',
                            ExtraArgs={'ACL': 'public-read','ContentType': image.content_type}
                        ) 
        except ClientError as e : logging.error(e)
        #link= f'https://nutriai.s3.ap-northeast-2.amazonaws.com/{userid}/{obj_path}'
        link= f'{userid}/{obj_path}'
        return link

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
        nutr_info= response.get('Item').get('nutrients')
        for i in total.keys():
            if i in nutr_info.keys():
                total[i]= nutr_info[i]
            else:
                total[i]= 0

        return total

    ####### MEAL log
    ####3 유저 식단 섭취 로그 등록
    def post_meal_log(self, userid:str, image_key:str, food_list):
        response = self.__table.put_item(
            Item={
                'PK': f'USER#{userid}',
                'SK': f'MEAL#{datetime.now()}',
                'photo': image_key,
                'food_list': food_list
            }
        )
        return response
    
    ####4 유저 식단 섭취 로그 정보 요청 - 특정 날
    def get_meal_log(self, userid:str, date: date) -> list:
        response = self.__table.query(
            KeyConditionExpression=Key('PK').eq(f'USER#{userid}') & Key('SK').begins_with(f'MEAL#{date}'),
            ProjectionExpression='SK, food_list'
        )
        return response.get('Items')
    
    ####5 유저 식단 섭취 로그 정보 삭제 - 특정 시간(시기)
    def delete_meal_log(self, userid:str, datetime:datetime):
        response = self.__table.delete_item(
            Key={
                'PK': f'USER#{userid}',
                'SK': f'MEAL#{datetime}'
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
                total[i]= nutr_info[i]
            else:
                total[i]= 0
                
        return total

    ####### NUTRTAKE log
    ####7 유저 영양제 섭취 로그 등록
    def post_nutrtake_log(self, userid:str, nutr_suppl_list:dict):
        response = self.__table.put_item(
            Item={
                'PK': f'USER#{userid}',
                'SK': f'NUTRTAKE#{datetime.now()}',
                'nutr_suppl_list': nutr_suppl_list
            }
        )
        return response

    ####8 유저 영양제 섭취 로그 정보 요청 - 특정 날
    def get_nutrtake_log(self, userid:str, date: date) -> list:
        response = self.__table.query(
            KeyConditionExpression=Key('PK').eq(f'USER#{userid}') & Key('SK').begins_with(f'NUTRTAKE#{date}'),
            ProjectionExpression='SK, nutr_suppl_list'
        )
        return response.get('Items')
    
    ####9 유저 영양제 섭취 로그 삭제 - 특정 시간(시기)
    def delete_nutrtake_log(self, userid:str, datetime:datetime):
        response = self.__table.delete_item(
            Key={
                'PK': f'USER#{userid}',
                'SK': f'NUTRTAKE#{datetime}'
            },
            # ReturnValues='ALL_OLD'
        )
        return response

    ####10 유저 영양 상태 식단 로그 입력 & 업데이트
    def update_user_meal_nutr_log(self, userid:str, nutrients:dict):
        response = self.__table.update_item(
            Key={
                'PK': f'USER#{userid}',
                'SK': f'NUTRSTATUS#{date.today()}#MEAL'
            },
            UpdateExpression='''
                ADD
                    nutr_intake = :new_nutr_intake
            ''',
            ExpressionAttributeValues={
                ':new_nutr_intake' : nutrients
            },
            ReturnValues='ALL_NEW'
        )
        return response.get('Attributes')

    ####11 유저 영샹 상태 영양제 로그 입력 & 업데이트
    def update_user_nutrtake_nutr_log(self, userid:str, nutrients:dict):
        response = self.__table.update_item(
            Key={
                'PK': f'USER#{userid}',
                'SK': f'NUTRSTATUS#{date.today()}#NUTRTAKE'
            },
            UpdateExpression='''
                ADD
                    nutr_intake = :new_nutr_intake
            ''',
            ExpressionAttributeValues={
                ':new_nutr_intake' : nutrients
            },
            ReturnValues='ALL_NEW'
        )
        return response.get('Attributes')

    ####12 유저 영양 상태 로그 정보 요청 - 특정 날
    def get_user_nutr_log(self, userid:str, date:date) -> list:
        response = self.__table.query(
            KeyConditionExpression=Key('PK').eq(f'USER#{userid}') & Key('SK').begins_with(f'NUTRSTATUS#{date}'),
            ProjectionExpression='SK, nutr_status'
        )
        return response.get('Items')

    ####13 유저 영양제 추천
    def recommend_nutrients(self, userid: str, request):
        #부족 영양소로 db 영양제 정보에 어떻게 접근??
        return