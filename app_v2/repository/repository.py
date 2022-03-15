from boto3.resources.base import ServiceResource
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
import logging
import requests 

from decimal import Decimal
from collections import Counter

from datetime import date, datetime, timedelta

###
class UserRepository:
    def __init__(self, db: ServiceResource)-> None:
        self.__db= db
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



    # calculate RDI
    def __calculate_RDI(self, physique: dict) -> dict:
        user_birth = datetime.strptime(physique['birth'],'%Y-%m-%d')
        user_sex = physique['sex']
        user_height = float(physique['height'])
        user_weight = float(physique['weight'])
        user_pai = float(physique['PAI'])

        today = date.today()
        cal_age= lambda birth: today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
        age = cal_age(user_birth)

        PK = self.__get_rdi_pk(age)
        SK = f'RDI#{user_sex}'

        # 에너지 제외 사용자 권장 섭취량 가져오기
        temp_rdi = self.__table.get_item(
            Key={
                'PK': PK,
                'SK': SK
            }
        ).get('Item').get('RDI')

        # 사용자 에너지 권장 섭취량 계산
        if user_sex == 'M':
            cal = (66.47 + (13.75*user_weight) + (5*user_height) - (6.76*age)) * user_pai
        elif user_sex == 'F':
            cal = (655.1 + (9.56*user_weight) + (1.85*user_height) - (4.68*age)) * user_pai
        else:
            pass
        # rid 속성에 입력
        temp_rdi['Calories'] = Decimal(str(cal))
        temp_rdi['Carbohydrate'] = Decimal(str((0.6*cal)/4))
        temp_rdi['Protein'] = Decimal(str((0.17*cal)/4))
        temp_rdi['Fat'] = Decimal(str((0.23*cal)/9))
        
        return temp_rdi

 
    

    # user 가입
    # input: {userid, username, physique{}}
    # output: #############
    def join_user(self, request:dict):
        userid = request.pop('userid')

        request['PK'] = f'USER#{userid}'
        request['SK'] = f'USER#{userid}#INFO'
        request['RDI'] = self.__calculate_RDI(request.get('physique'))
        request['nutr_suppl'] = list()

        response = self.__table.put_item(
            Item=request,
            ConditionExpression=Attr('PK').not_exists() & Attr('SK').not_exists()
        )
        return response



    # physique, RDI 수정
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

    # nutr_suppl 수정
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


    # user 모든 정보 받기
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
    
    # physique 정보 받기
    # input: userid
    # output: physique value
    def get_user_physique(self, userid:str) -> dict:
        response = self.__table.get_item(
            Key={
                'PK': f'USER#{userid}',
                'SK': f'USER#{userid}#INFO'
            },
            ProjectionExpression='physique'
        )
        return response.get('Item').get('physique')

    # RDI 정보 받기
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

    # nutr_suppl 정보 받기
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
    def get_nutr_suppl_list(self, search:str) -> list:
        response = self.__table.query(
            KeyConditionExpression=Key('PK').eq('NUTRSUPPL'),
            FilterExpression=Attr('title').contains(search),
        )
        return response.get('Items')


    # user 삭제
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






class LogRepository:
    def __init__(self, db: ServiceResource):
        self.__db= db
        self.__table= self.__db.Table('nutriai_test')


    ####### MEAL log
    # post 식단 로그 입력
    # input : userID, s3 image key, food list
    # output : ###
    def post_meal_log(self, userid:str, image_key:str, food_list:list):
        response = self.__table.put_item(
            Item={
                'PK': f'USER#{userid}',
                'SK': f'MEAL#{datetime.now().isoformat()}',
                'photo': image_key,
                'food_list': food_list
            }
        )
        return response
    
    # update 식단 로그, 음식 리스트만 수정
    # input : userID, datetime, new food list
    # output : updated food list
    def update_meal_log_food_list(self, userid:str, date_time:datetime, new_food_list:list) -> list:
        response = self.__table.update_item(
            Key={
                'PK': f'USER#{userid}',
                'SK': f'MEAL#{date_time}'
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

    # get 식단 로그 가져오기 - 특정 날
    # input : userID, date
    # output : {SK(date), food list} list
    def get_meal_log(self, userid:str, date: date) -> list:
        response = self.__table.query(
            KeyConditionExpression=Key('PK').eq(f'USER#{userid}') & Key('SK').begins_with(f'MEAL#{date}'),
            ProjectionExpression='SK, photo, food_list'
        )
        return response.get('Items')
    
    # delete 식단 로그 - 특정 시기
    # input : userID, datetime
    # output : #####
    def delete_meal_log(self, userid:str, datetime:datetime):
        response = self.__table.delete_item(
            Key={
                'PK': f'USER#{userid}',
                'SK': f'MEAL#{datetime}'
            },
            # ReturnValues='ALL_OLD'
        )
        return response
    
    
    ######### FOOD 
    # get 식품 영양성분 정보
    # input : food category(model output), food name(user choice)
    # output : nutrient dict
    def get_food_nutrients(self, food_cat:str, food_name: str) -> dict:
        response = self.__table.get_item(
            Key={
                'PK': f'FOOD#{food_cat}',
                'SK': f'FOOD#{food_name}'
            },
            ProjectionExpression='nutrients'
        )
        return response.get('Item').get('nutrients')
    

    ####### NUTRTAKE log
    # post 영양제 로그
    # input : userID, nutrition supplement list
    # output : #####
    def post_nutrtake_log(self, userid:str, nutr_suppl_list:dict):
        response = self.__table.put_item(
            Item={
                'PK': f'USER#{userid}',
                'SK': f'NUTRTAKE#{datetime.now().isoformat()}',
                'nutr_suppl_list': nutr_suppl_list
            }
        )
        return response

    # update 영양제 로그
    # input : userID, datetime, new supplement list
    # output : updated supplement
    def update_nutrtake_log_suppl_list(self, userid:str, date_time:datetime, new_suppl_list:list) -> list:
        response = self.__table.update_item(
            Key={
                'PK': f'USER#{userid}',
                'SK': f'NUTRTAKE#{date_time}'
            },
            UpdateExpression='''
                SET
                    nutr_suppl_list = :new_nutr_suppl_list
            ''',
            ExpressionAttributeValues={
                ':new_nutr_suppl_list' : new_suppl_list
            },
            ReturnValues='UPDATED_NEW'
        )
        return response.get('Attributes').get('nutr_suppl_list')

    # get 영양제 로그 가져오기 - 특정 날
    # input : userID, date
    # output : {SK(date), food list} list
    def get_nutrtake_log(self, userid:str, date: date) -> list:
        response = self.__table.query(
            KeyConditionExpression=Key('PK').eq(f'USER#{userid}') & Key('SK').begins_with(f'NUTRTAKE#{date}'),
            ProjectionExpression='SK, nutr_suppl_list'
        )
        return response.get('Items')
    
    # delete 영양제 로그 - 특정 시기
    # input : userID, datetime
    # output : ######
    def delete_nutrtake_log(self, userid:str, datetime:datetime):
        response = self.__table.delete_item(
            Key={
                'PK': f'USER#{userid}',
                'SK': f'NUTRTAKE#{datetime}'
            },
            # ReturnValues='ALL_OLD'
        )
        return response



    ####### NUTR SUPPL 
    # get 영양제 영양성분 정보
    # input : nutrition supplement category, product code
    # output : nutrient dict
    def get_nutr_suppl_nutrients(self, nutr_cat:str, product_code:str) -> dict:
        response = self.__table.get_item(
            Key={
                'PK': f'NUTRSUPPL',
                'SK': f'NUTRSUPPL#{product_code}'
            },
            ProjectionExpression='nutrients'
        )
        return response.get('Item').get('nutrients')



    ######## NUTRSTATUS log

    # 사용자 영양상태 로그 입력&업데이트 - 식단
    # input : userID, nutrients
    # output : updated attributes
    def update_user_meal_nutr_log(self, userid:str, nutrients:dict):
        old_status = self.__table.get_item(
            Key={
                'PK': f'USER#{userid}',
                'SK': f'NUTRSTATUS#{date.today()}#MEAL'
            }
        ).get('Item').get('nutr_intake')
        new_status = Counter(old_status) + Counter(nutrients)
        response = self.__table.update_item(
            Key={
                'PK': f'USER#{userid}',
                'SK': f'NUTRSTATUS#{date.today()}#MEAL'
            },
            UpdateExpression='''
                SET
                    nutr_status = :new_nutr_status
            ''',
            ExpressionAttributeValues={
                ':new_nutr_status' : new_status
            },
            ReturnValues='ALL_NEW'
        )
        return response.get('Attributes')

    # 사용자 영양상태 로그 입력&업데이트 - 영양제
    # input : userID, nutrients
    # output : updated attributes
    def update_user_nutrtake_nutr_log(self, userid:str, nutrients:dict):
        old_status = self.__table.get_item(
            Key={
                'PK': f'USER#{userid}',
                'SK': f'NUTRSTATUS#{date.today()}#NUTRTAKE'
            }
        ).get('Item').get('nutr_intake')
        new_status = Counter(old_status) + Counter(nutrients)
        response = self.__table.update_item(
            Key={
                'PK': f'USER#{userid}',
                'SK': f'NUTRSTATUS#{date.today()}#NUTRTAKE'
            },
            UpdateExpression='''
                ADD
                    nutr_status = :new_nutr_status
            ''',
            ExpressionAttributeValues={
                ':new_nutr_status' : new_status
            },
            ReturnValues='ALL_NEW'
        )
        return response.get('Attributes')

    # get 사용자 영양상태 로그 - 특정 날짜 (식단 + 영양제)
    # input : userID, date
    # output : 
    def get_user_nutr_log(self, userid:str, date:date) -> list:
        response = self.__table.query(
            KeyConditionExpression=Key('PK').eq(f'USER#{userid}') & Key('SK').begins_with(f'NUTRSTATUS#{date}'),
            ProjectionExpression='SK, nutr_status'
        )
        return response.get('Items')

    # get 사용자 영양상태 로그 - 특정 날짜 (식단)
    # input : userID, date
    # output : 
    def get_user_nutr_log_meal(self, userid:str, date:date) -> list:
        response = self.__table.query(
            KeyConditionExpression=Key('PK').eq(f'USER#{userid}') & Key('SK').eq(f'NUTRSTATUS#{date}#MEAL'),
            ProjectionExpression='SK, nutr_status'
        )
        return response.get('Items')
    
    # get 사용자 영양상태 로그 - 특정 날짜 (식단 - 탄단지)
    # input : userID, date
    # output : 
    def get_user_nutr_log_meal_CPF(self, userid:str, date:date) -> list:
        response = self.__table.query(
            KeyConditionExpression=Key('PK').eq(f'USER#{userid}') & Key('SK').eq(f'NUTRSTATUS#{date}#MEAL'),
            ProjectionExpression='SK, nutr_status.Calories, nutr_status.Carbohydrate, nutr_status.Protein, nutr_status.Fat'
        )
        return response.get('Items')

    # get 사용자 영양상태 로그 - 특정 날짜 (영양제)
    # input : userID, date
    # output : 
    def get_user_nutr_log_suppl(self, userid:str, date:date) -> list:
        response = self.__table.query(
            KeyConditionExpression=Key('PK').eq(f'USER#{userid}') & Key('SK').eq(f'NUTRSTATUS#{date}#NUTRTAKE'),
            ProjectionExpression='SK, nutr_status'
        )
        return response.get('Items')
    
    # get 사용자 영양 상태 로그 - 오늘부터 n일 (식단 + 영양제)
    # input : userID, number of days
    # output :
    def get_user_nutr_log_ndays(self, userid:str, ndays:int) -> list:
        date_from = date.today() - timedelta(days=ndays)
        date_to = date.today()+ timedelta(days=1)
        response = self.__table.query(
            KeyConditionExpression=Key('PK').eq(f'USER#{userid}') & Key('SK').between(f'NUTRSTATUS#{date_from}',f'NUTRSTATUS#{date_to}'),
            ProjectionExpression='SK, nutr_status'
        )
        return response.get('Items')

    # get 사용자 영양 상태 로그 - 오늘부터 n일 (식단)
    # input : userID, number of days
    # output :
    def get_user_nutr_log_ndays(self, userid:str, ndays:int) -> list:
        date_from = date.today() - timedelta(days=ndays)
        response = self.__table.query(
            KeyConditionExpression=Key('PK').eq(f'USER#{userid}') & Key('SK').between(f'NUTRSTATUS#{date_from}#MEAL',f'NUTRSTATUS#{date.today()}#MEAL'),
            ProjectionExpression='SK, nutr_status'
        )
        return response.get('Items')

    # get 사용자 영양 상태 로그 - 오늘부터 n일 (영양제)
    # input : userID, number of days
    # output :
    def get_user_nutr_log_ndays(self, userid:str, ndays:int) -> list:
        date_from = date.today() - timedelta(days=ndays)
        response = self.__table.query(
            KeyConditionExpression=Key('PK').eq(f'USER#{userid}') & Key('SK').between(f'NUTRSTATUS#{date_from}#NUTRTAKE',f'NUTRSTATUS#{date.today()}#NUTRTAKE'),
            ProjectionExpression='SK, nutr_status'
        )
        return response.get('Items')




class ImageRepository:
    def __init__(self, s3) -> None:
        self.__s3 = s3 # client
    
    # get presigned url
    def __get_presigned_url(client, bucket_name:str, object_name:str, expiration=3600) -> str:
        try:
            response = client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': bucket_name,
                    'Key':object_name
                },
                ExpiresIn=expiration
            )
        except ClientError as e:
            logging.error(e)
            return None
        return response.get('url')


    def post_image(self, object_name:str):
        response = self.__get_presigned_url(self.__s3, 'nutriai', object_name)
        if response is None:
            exit(1)
        # Demonstrate how another Python program can use the presigned URL to upload a file
        with open(object_name, 'rb') as f:
            files = {'file': (object_name, f)}
            http_response = requests.post(response['url'], data=response['fields'], files=files)
        # If successful, returns HTTP status code 204
        logging.info(f'File upload HTTP status code: {http_response.status_code}')