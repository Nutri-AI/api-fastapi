from boto3.resources.base import ServiceResource

class UserRepository:
    def __init__(self, db: ServiceResource)-> None:
        self.__db= db

    def join_user(self):
        return 

    def update_user(self):
        return

    def delete_user(self):
        return

    def get_user(self):
        return

    def update_nutrients(self):
        return

class LogRepository:
    def __init__(self, db: ServiceResource)-> None:
        self.__db= db