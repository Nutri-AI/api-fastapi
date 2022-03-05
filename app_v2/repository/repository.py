from urllib import response
from boto3.resources.base import ServiceResource
from boto3.dynamodb.conditions import Key, Attr

###
class UserRepository:
    def __init__(self, db: ServiceResource)-> None:
        self.__db= db
        self.__table = db.Table('NutriAI')

    # calculate RDI
    #####################
    def __calculate_RDI(physique:dict) -> dict:

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
            ConditionExpression=Attr('PK').not_exists() & Attr('SK').not_exists()
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
    # input: userid, nutr_suppl
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
    def __init__(self, db: ServiceResource)-> None:
        self.__db= db
