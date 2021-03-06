from collections import Counter
from itertools import count
from urllib import response
from app_v2.repository.tablename import *
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
import pandas as pd
from pprint import pprint

from sklearn.metrics.pairwise import cosine_similarity

from datetime import date, datetime, timedelta


from app_v2.yolov3_onnx_inf import detect

base_rdi= {
    'Dietary_Fiber': Decimal('0'), 'Calcium': Decimal('0'), 'Iron': Decimal('0'), 'Magnesium': Decimal('0'), 'Phosphorus': Decimal('0'), 'Potassium': Decimal('0'), 'Sodium': Decimal('0'), 'Zinc': Decimal('0'), 'Copper': Decimal('0'), 'Manganese': Decimal('0'), 'Selenium': Decimal('0'), 'Vitamin_A': Decimal('0'), 'Vitamin_D': Decimal('0'), 'Niacin': Decimal('0'), 'Folic_acid': Decimal('0'), 'Vitamin_B12': Decimal('0'), 'Vitamin_B6': Decimal('0'), 'Vitamin_C': Decimal('0'), 'Vitamin_E': Decimal('0'), 'Vitamin_K': Decimal('0'), 'Leucine': Decimal('0'), 'Iso_Leucine': Decimal('0'), 'Histidine': Decimal('0'), 'Linoleic_Acid': Decimal('0'), 'Alpha_Linolenic_Acid': Decimal('0'), 'Lysine': Decimal('0'), 'Methionine': Decimal('0'), 'Phenylalanine+Tyrosine': Decimal('0'), 'Threonine': Decimal('0'), 'Valine': Decimal('0')
}
    # 'Protein': 0, 'Fat': 0, 'Carbohydrate': 0, 'Dietary_Fiber': 0, 'Calcium': 0,
    # 'Iron': 0, 'Magnesium': 0, 'Phosphorus': 0, 'Potassium': 0, 'Sodium': 0, 'Zinc': 0,
    # 'Copper': 0, 'Manganese': 0, 'Selenium': 0, 'Vitamin_A': 0, 'Vitamin_D': 0, 'Niacin': 0,
    # 'Folic_acid': 0, 'Vitamin_B12': 0, 'Vitamin_B6': 0, 'Vitamin_C': 0, 'Vitamin_E': 0,
    # 'Vitamin_K': 0, 'Leucine': 0, 'Iso_Leucine': 0, 'Histidine': 0, 'Linoleic_Acid': 0, 
    # 'Alpha_Linolenic_Acid': 0, 'Lysine': 0, 'Methionine': 0, 'Phenylalanine+Tyrosine': 0,
    # 'Threonine': 0, 'Valine': 0, 'Cholesterol': 0, 'Calories': 0
    # }

pcf_status= {
    'Protein': 0, 'Fat': 0, 'Calories': 0, 'Carbohydrate': 0
    }

# fnames = ["pork_belly","ramen","bibimbap","champon","cold_noodle","cutlassfish","egg_custard",
#         "egg_soup","jajangmyeon","kimchi_stew","multigrain_rice",
#         "oxtail_soup","pickled spianch","pizza","pork_feet","quail_egg_stew","seasoned_chicken",
#         "seaweed_soup","soy_bean_paste_soup","stewed_bean","stewed_lotus_stew",
#         "stir_fried_anchovy","sitr_fried_pork","salad","ice_americano","Bottled_Beer","Canned_Beer",
#         "Draft_Beer","Fried_Chicken","Tteokbokki","Cabbage_Kimchi","Radish_Kimchi", "No_detect"]

fnames = ["???????????????","??????","?????????","??????","??????","????????????","?????????",
        "?????????","?????????","????????????","?????????",
        "?????????","???????????????","??????","??????","?????????????????????","????????????",
        "?????????","????????????","?????????","????????????",
        "????????????","????????????","?????????","???????????????","??????","??????",
        "??????","??????????????????","?????????","????????????","?????????", "No_detect"]

KST = timedelta(hours=9)

class UserRepository:
    def __init__(self, db: ServiceResource)-> None:
        self.__db, self.__s3= db
        self.__table = self.__db.Table(table_name)

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

    ##### RDI ??????
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
        # temp_rdi['Calories'] = cal
        # temp_rdi['Carbohydrate'] = Decimal('0.6')*cal/4
        # temp_rdi['Protein'] = Decimal('0.17')*cal/4
        # temp_rdi['Fat'] = Decimal('0.23')*cal/9
        
        return temp_rdi
        
    ####1 ?????? ?????? ??????
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



    ####2 ?????? ?????? ???????????? - physique, RDI ??????
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

    ####3 ?????? physique ?????? ??????
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

    ####4 ?????? ?????? ??????
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

    ####5 ?????? ?????? ??????
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

    ####6 ?????? RDI ?????? ??????
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
        return {i:round(float(v), 1) for i,v in response.get('Item').get('RDI').items()}

    ####7 nutr_suppl ?????? - ????????? ?????? ?????? ??? ??????
    # input: userid, nutr_suppl(prod_code ??? ?????? ?????????)
    # output: nutr_suppl
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

    ####8 ?????? nutr_suppl ?????? ??????
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
        self.__table= self.__db.Table(table_name)

    #### S3 ?????? ?????? ??????? 
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

    #### S3 url ?????? ??????
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

    ####1 ????????? S3??? ?????????
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
    
    # s3 ??? ?????? ??????
    def get_s3_url_file(self, userid: str, obj_name: str):
        url = self.create_presigned_url('nutriai', obj_name)
        if url is not None:
            response = requests.get(url)
        
        print(response)
        return url

    ######### FOOOD 
    ####2 ?????? ?????? ?????? ?????? ??????
    def get_food_nutrients(self, food_cat:str, food_name: str):
        response = self.__table.get_item(
            Key={
                'PK': f'FOOD#{food_cat}',
                'SK': f'FOOD#{food_name}'
            },
            ProjectionExpression='nutrients'
        ).get('Item').get('nutrients')
        return response


    ####### MEAL log ##########
    ####3 ?????? ?????? ?????? ?????? ?????? ##
    # input : userid, image_key, class list, food list
    # output : meal nutrients
    def post_meal_log(self, userid:str, image_key:str, class_list:list, food_list:list):
        kst_datetime = (datetime.utcnow() + KST)
        response_put = self.__table.put_item(
            Item={
                'PK': f'USER#{userid}',
                'SK': f'{kst_datetime.date().isoformat()}#MEAL#{kst_datetime.time().isoformat()}',
                'photo': image_key,
                'food_list': food_list
            }
        )
        response_nutr = Counter(base_rdi) ##### 
        for c, f in zip(class_list, food_list):
            nutr = self.get_food_nutrients(c, f)
            response_nutr += Counter(nutr)
            response_status = self.update_user_meal_nutr_log(userid, nutr)
        
        for i in response_nutr.keys():
            if i in pcf_status.keys():
                response_nutr[i] = round(float(response_nutr[i]))
            else:
                response_nutr[i] = float(response_nutr[i])
        response= {'nutrients': response_nutr}
        return response


    # update ?????? ??????, ?????? ???????????? ??????
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
    
    ####4 ?????? ?????? ?????? ?????? ?????? ?????? - ?????? ???
    def get_meal_log(self, userid:str, date) -> list:
        response = self.__table.query(
            KeyConditionExpression=Key('PK').eq(f'USER#{userid}') & Key('SK').begins_with(f'{date}#MEAL#'),
            ProjectionExpression='SK, photo, food_list'
        )
        return response.get('Items')
    
    ####5 ?????? ?????? ?????? ?????? ?????? ?????? - ?????? ??????(??????)
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
    ####6 ????????? ???????????? ?????? ??????
    def get_nutr_suppl_nutrients(self, nutr_cat:str, product_code:str):
        response = self.__table.get_item(
            Key={
                'PK': f'NUTRSUPPL#{nutr_cat}',
                'SK': f'NUTRSUPPL#{product_code}'
            },
            ProjectionExpression='nutrients'
        )
        # nutr_info= response.get('Item').get('nutrients')
        # for i in total.keys():
        #     if i in nutr_info.keys():
        #         total[i]= round(float(nutr_info[i]), 1)
        #     else:
        #         total[i]= 0
        return response.get('Item').get('nutrients') #total

    ####### NUTRTAKE log
    ####7 ?????? ????????? ?????? ?????? ??????
    def post_nutrtake_log(self, userid:str, nutr_suppl_list:dict):
        kst_datetime = (datetime.utcnow() + KST)
        response = self.__table.put_item(
            Item={
                'PK': f'USER#{userid}',
                'SK': f'{kst_datetime.date().isoformat()}#SUPPLTAKE#{kst_datetime.time().isoformat()}',
                'nutr_suppl_take': nutr_suppl_list
            }
        )
        return response
    
    ####8 update ????????? ?????? ???????????? ????????? ??????
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

    ####9 ?????? ????????? ?????? ?????? ?????? ?????? - ?????? ???
    def get_nutrtake_log(self, userid:str, date) -> list:
        response = self.__table.query(
            KeyConditionExpression=Key('PK').eq(f'USER#{userid}') & Key('SK').begins_with(f'{date}#SUPPLTAKE#'),
            ProjectionExpression='SK, nutr_suppl_take'
        )
        return response.get('Items')
    
    ####10 ?????? ????????? ?????? ?????? ?????? - ?????? ??????(??????)
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
    ####11 ?????? ?????? ?????? ?????? ?????? ?????? & ????????????
    def update_user_meal_nutr_log(self, userid:str, food_nutrients:dict):
        kst_date = (datetime.utcnow() + KST).date()
        try:
            old_status = self.__table.get_item(
                Key={
                    'PK': f'USER#{userid}',
                    'SK': f'{kst_date}#NUTRSTATUS#MEAL'
                }
            ).get('Item').get('nutr_status')
        except:
            old_status = base_rdi
        new_status = Counter(old_status) + Counter(food_nutrients)
        response = self.__table.update_item(
            Key={
                'PK': f'USER#{userid}',
                'SK': f'{kst_date}#NUTRSTATUS#MEAL'
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

    ####12 ?????? ?????? ?????? ????????? ?????? ?????? & ????????????
    def update_user_nutrtake_nutr_log(self, userid:str, suppl_nutrients:dict):
        kst_date = (datetime.utcnow() + KST).date()
        try:
            old_status = self.__table.get_item(
                Key={
                    'PK': f'USER#{userid}',
                    'SK': f'{kst_date}#NUTRSTATUS#SUPPLTAKE'
                }
            ).get('Item').get('nutr_status')
        except:
            old_status = base_rdi
        new_status = Counter(old_status) + Counter(suppl_nutrients)
        response = self.__table.update_item(
            Key={
                'PK': f'USER#{userid}',
                'SK': f'{kst_date}#NUTRSTATUS#SUPPLTAKE'
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

    ####13 get ????????? ???????????? ?????? - ?????? ?????? (?????? + ?????????)
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

    ####14 get ????????? ???????????? ?????? - ?????? ?????? (??????)
    # input : userID, date
    # output : {SK, nutr_status}
    def get_user_nutr_log_meal(self, userid:str, date) -> list:
        response = self.__table.query(
            KeyConditionExpression=Key('PK').eq(f'USER#{userid}') & Key('SK').eq(f'{date}#NUTRSTATUS#MEAL'),
            ProjectionExpression='SK, nutr_status'
        )
        return response.get('Items')
    
    ####15 get ????????? ???????????? ?????? - ?????? ?????? (?????? - ?????????)
    # input : userID, date
    # output : 
    def get_user_nutr_log_meal_CPF(self, userid:str, date) -> list:
        response = self.__table.query(
            KeyConditionExpression=Key('PK').eq(f'USER#{userid}') & Key('SK').eq(f'{date}#NUTRSTATUS#MEAL'),
            ExpressionAttributeNames={'#ns': 'nutr_status'},
            ProjectionExpression='SK, #ns.Calories, #ns.Carbohydrate, #ns.Protein, #ns.Fat'
        )
        return response.get('Items')

    ####16 get ????????? ???????????? ?????? - ?????? ?????? (?????????)
    # input : userID, date
    # output : 
    def get_user_nutr_log_suppl(self, userid:str, date) -> list:
        response = self.__table.query(
            KeyConditionExpression=Key('PK').eq(f'USER#{userid}') & Key('SK').eq(f'{date}#NUTRSTATUS#SUPPLTAKE'),
            ProjectionExpression='SK, nutr_status'
        )
        return response.get('Items')

    ####17 get ????????? ?????? ?????? ?????? - ???????????? n??? (?????? + ?????????)
    # input : userID, number of days
    # output :
    def get_user_nutr_log_ndays(self, userid:str, ndays:int) -> dict:
        kst_date = (datetime.utcnow() + KST).date()
        date_from = kst_date - timedelta(days=ndays-1)
        date_to = kst_date + timedelta(days=1)
        response = self.__table.query(
            KeyConditionExpression=Key('PK').eq(f'USER#{userid}') & Key('SK').between(f'{date_from}#NUTRSTATUS#',f'{date_to}#NUTRSTATUS#'),
            FilterExpression=Attr('nutr_status').exists(),
            ProjectionExpression='SK, nutr_status'
        ).get('Items')

        cnt_items = len(response)
        count = Counter(dict())
        for i in range(cnt_items):
            count += Counter(response[i].get('nutr_status'))
        count = dict(count)
        result = {key : round(float(count[key] / cnt_items), 1) for key in count.keys()}
        return result

    ####18 get ????????? ?????? ?????? ?????? - ???????????? n??? (??????)
    # input : userID, number of days
    # output :
    def get_user_nutr_log_meal_ndays(self, userid:str, ndays:int) -> dict:
        kst_date = (datetime.utcnow() + KST).date()
        date_from = kst_date - timedelta(days=ndays-1)
        date_to = kst_date + timedelta(days=1)
        response = self.__table.query(
            KeyConditionExpression=Key('PK').eq(f'USER#{userid}') & Key('SK').between(f'{date_from}#NUTRSTATUS#',f'{date_to}#NUTRSTATUS#'),
            FilterExpression=Attr('status_type').eq('MEAL'),
            ProjectionExpression='SK'
        ).get('Items')

        cnt_items = len(response)
        count = Counter(dict())
        for i in range(cnt_items):
            count += Counter(response[i].get('nutr_status'))
        count = dict(count)
        result = {key : round(float(count[key] / cnt_items), 1) for key in count.keys()}
        return result

    ####19 get ????????? ?????? ?????? ?????? - ???????????? n??? (?????????)
    # input : userID, number of days
    # output :
    def get_user_nutr_log_suppl_ndays(self, userid:str, ndays:int) -> dict:
        kst_date = (datetime.utcnow() + KST).date()
        date_from = kst_date - timedelta(days=ndays-1)
        date_to = kst_date + timedelta(days=1)
        response = self.__table.query(
            KeyConditionExpression=Key('PK').eq(f'USER#{userid}') & Key('SK').between(f'{date_from}#NUTRSTATUS#',f'{date_to}#NUTRSTATUS#'),
            FilterExpression=Attr('status_type').eq('SUPPLTAKE'),
            ProjectionExpression='SK, nutr_status'
        ).get('Items')

        cnt_items = len(response)
        count = Counter(dict())
        for i in range(cnt_items):
            count += Counter(response[i].get('nutr_status'))
        count = dict(count)
        result = {key : round(float(count[key] / cnt_items), 1) for key in count.keys()}
        return result


    # today status query
    def get_user_today_status(self, userid:str):
        kst_date = (datetime.utcnow() + KST).date()
        # query (NUTRSTATUS#MEAL & #MEAL#)
        response_nutr = self.__table.query(
            KeyConditionExpression=Key('PK').eq(f'USER#{userid}') & Key('SK').begins_with(kst_date.isoformat()),
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
        #return {i:int(v) for i,v in response.get('RDI').items()}
        return response


    # 1 week status query
    # output: {'username','RDI','nutr_status'}
    def get_user_week_status(self, userid:str):
        # query ( NUTRSTATUS )
        response_nutr = self.get_user_nutr_log_ndays(userid, 7)
        # get user data
        response = self.__table.get_item(
            Key={
                'PK': f'USER#{userid}',
                'SK': f'USER#{userid}#INFO'
            },
            ProjectionExpression='username, RDI'
        ).get('Item')
        response['nutr_status'] = response_nutr
        return response


    ####### NUTR SUPPL
    # get ????????? ??????
    def get_nutr_suppl(self, nutr_cat:str, product_code:str):
        response = self.__table.get_item(
            Key={
                'PK': f'NUTRSUPPL#{nutr_cat}',
                'SK': f'NUTRSUPPL#{product_code}'
            },
            ProjectionExpression='price, title, nutrsuppl_url'
        )
        return response.get('Item')

    ### ?????? ????????? ??????
    def get_recomm_nutrsuppl(self, userid: str):
        # user rdi data
        user_rdi = self.__table.get_item(
            Key={
                'PK': f'USER#{userid}',
                'SK': f'USER#{userid}#INFO'
            },
            ProjectionExpression='RDI, username'
        ).get('Item')#.get('RDI')
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
                supp_pd_list = list()
                for cd in prod_code:
                    supp_pd_list.append(self.get_nutr_suppl(cat, cd))
                response[cat] = supp_pd_list
            elif cat in ['minerals']:
                # Cosine Similarity
                test_cosim_df = suppl_rat_df.append(user_diffrat).fillna(0)
                test_cosim_df['cosim'] = cosine_similarity(test_cosim_df,test_cosim_df)[:,-1]
                prod_code = list(test_cosim_df.sort_values(by='cosim', ascending=False).index[1:4])
                supp_pd_list = list()
                for cd in prod_code:
                    supp_pd_list.append(self.get_nutr_suppl(cat, cd))
                response[cat] = supp_pd_list
            else:
                pass
        return response
