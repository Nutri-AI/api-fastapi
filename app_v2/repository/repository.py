from boto3.resources.base import ServiceResource

from datetime import date, datetime
from decimal import Decimal

###
class UserRepository:
    def __init__(self, db: ServiceResource)-> None:
        self.__db= db
        self.__table = db.Table('NutriAI')


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
    def __calculate_RDI(self, physique:dict) -> dict:
        today = date.today()
        cal_age = lambda birth : today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
        age = Decimal(cal_age(date(physique.birth)))
        PK = self.__get_rdi_pk(age)
        SK = f'RDI#{physique.sex}'

        temp_rdi = self.__table.get_item(
            Key={
                'PK': PK,
                'SK': SK
            }
        ).get('Item').get('rid')

        if physique.sex == 'M':
            cal = Decimal('66.47') + (Decimal('13.75')*physique.weight) + (Decimal('5')*physique.height) - (Decimal('6.76')*age)
        elif physique.sex == 'F':
            cal = Decimal('655.1') + (Decimal('9.56')*physique.weight) + (Decimal('1.85')*physique.height) - (Decimal('4.68')*age)
        else:
            pass
        temp_rdi['Calories'] = cal
        temp_rdi['Carbohydrate'] = (Decimal('0.6')*cal)/Decimal('4')
        temp_rdi['Protein'] = (Decimal('0.17')*cal)/Decimal('4')
        temp_rdi['Fat'] = (Decimal('0.23')*cal)/Decimal('9')
        
        return

    

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
            ConditionExpression='attribute_not_exists(PK) AND attribute_not_exists(SK)'
        )
        return #######



    # physique, RDI 수정
    # input: userid, physique{}
    # output: {physique, RDI}
    def update_user_physique(self, userid:str, physique:dict) -> dict:
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
            ExpressionAttributeValue={
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
        return response.get('Attributes').get('username')



class LogRepository:
    def __init__(self, db: ServiceResource, s3)-> None:
        self.__db = db
        self.__table = db.Table('NutriAI')
        # self.__s3 = s3
    
    # meal log 입력
    def post_meal_log(self, userid:str, image_key:str, food_list:list) -> None:
        response = self.__table.put_item(
            Item={
                'PK': f'USER#{userid}',
                'SK': f'MEAL#{datetime.now()}',
                'photo': image_key,
                'food_list': food_list
            },
            ConditionExpression='attribute_not_exists(PK) AND attribute_not_exists(SK)'
        )
    
    # meal log 가져오기
    def get_meal_log(self, userid:str)
