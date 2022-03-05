from pydantic import BaseModel

from app_v2.repository.repository import UserRepository, LogRepository

class UserJoinModel(BaseModel):
    pass

class UserDomain():
    def __init__(self, repository: UserRepository):
        self.__repository= repository

    def join_user(self, request: dict):
        request.PK= f''
        request.SK= f''
        return self.__repository.join_user(request.dict())

    def update_user(self, PK: str):
        PK= f''
        SK= f''
        return self.__repository.update_user(PK, SK)

    def delete_user(self, PK: str):
        PK= f''
        SK= f''
        return self.__repository.delete_user(PK, SK)

    def get_user(self, PK: str):
        PK= f''
        SK= f''
        return self.__repository.get_user(PK, SK)

    def update_nutrients(self, PK: str):
        PK= f''
        SK= f''
        return self.__repository.update_nutrients(PK, SK)
        
class LogDomain():
    def __init__(self, repository: LogRepository):
        self.__repository= repository