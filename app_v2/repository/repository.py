from boto3.resources.base import ServiceResource
from boto3.dynamodb.conditions import Key, Attr
from decimal import Decimal

from datetime import date, datetime


###
class UserRepository:
    def __init__(self, db: ServiceResource)-> None:
        self.__db= db
        self.__table = self.__db.Table('NutriAI')

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



    # calculate RDI
    def __calculate_RDI(self, physique: dict) -> dict:
        user_birth = date(physique['birth'])
        user_sex = physique['sex']
        user_height = float(physique['height'])
        user_weight = float(physique['weight'])
        user_pai = float(physique['pai'])

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
        ).get('Item').get('rdi')

        if user_sex == 'M':
            cal = (66.47 + (13.75*user_weight) + (5*user_height) - (6.76*age))*user_pai
        elif user_sex == 'F':
            cal = (655.1 + (9.56*user_weight) + (1.85*user_height) - (4.68*age))*user_pai
        else:
            pass

        temp_rdi['Calories'] = cal
        temp_rdi['Carbohydrate'] = (0.6*cal)/4
        temp_rdi['Protein'] = (0.17*cal)/4
        temp_rdi['Fat'] = (0.23*cal)/9
        
        return temp_rdi

 
    

    # user 가입
    # input: {userid, username, physique{}}
    # output: ??? #############
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
            ExpressionAttributeValue={
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
    # def get_nutr_suppls(self, search:str) -> list:
    #     response = self.__table.query(
    #         KeyConditionExpression=Key('PK').eq('NUTRSUPPL'),
    #         FilterExpression=Attr('prod_name').contains(search),
    #     )
    #     return response.get('Items')


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
        self.__table= self.__db.Table('NutriAI')


    # 식단 로그 입력
    def post_meal_log(self, userid:str, image_key:str, food_list:list):
        response = self.__table.put_item(
            Item={
                'PK': f'USER#{userid}',
                'SK': f'MEAL#{datetime.now()}',
                'photo': image_key,
                'food_list': food_list
            }
        )
        return response

    # 식품 영양성분 정보 받기
    def get_food_nutrients(self, food_cat:str, food_name: str):
        response = self.__table.get_item(
            Key={
                'PK': f'FOOD#{food_cat}',
                'SK': f'FOOD#{food_name}'
            },
            ProjectionExpression='nutrients'
        )
        return response.get('Item').get('nutrients')
    

    # 영양제 로그 입력
    def post_nutrsuppl_log(self, userid:str, nutr_suppl_list:dict):
        response = self.__table.put_item(
            Item={
                'PK': f'USER#{userid}',
                'SK': f'NUTRTAKE{datetime.now()}',
                'nutr_suppl_list': nutr_suppl_list
            }
        )
        return response

    # 영양제 영양정보 받기
    def get_nutr_suppl_nutrients(self, nutr_cat:str, product_code:str):
        response = self.__table.get_item(
            Key={
                'PK': f'NUTRSUPPL#{nutr_cat}',
                'SK': f'NUTRSUPPL#{product_code}'
            },
            ProjectionExpression='nutrients'
        )
        return response.get('Item').get('nutrients')


    # 사용자 영양상테 로그 입력&업데이트
    def update_user_nutr_log(self, userid:str, nutrients:dict):
        response = self.__table.update_item(
            Key={
                'PK': f'USER#{userid}',
                'SK': f'NUTRSTATUS#{date.today()}'
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


    def upload_image(self, userid: str, image, detail: str):
        # 대분류 후보?
        return 

    def record_meal(self, userid: str, big: str, small: str):
        response= self.__table.get_item()
        # 영양 정보 가져와서 로그 기록 저장
        response2= self.__table.update_item()
        return response2

    def post_time_nutri(self, userid: str, request):
        #유저 아이디 별 저장, 방식에 따라 수정해주십쇼 그냥 적어봤슴다.
        response= self.__table.put_item()
        
        return response 




    def recommend_nutrients(self, userid: str, request):
        #부족 영양소로 db 영양제 정보에 어떻게 접근??
        return