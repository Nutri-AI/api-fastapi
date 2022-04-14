# Nutri-AI project

이미지 기반 식단 분석 및 영양제 추천

## API
### FastAPI
link : https://fastapi.tiangolo.com/

## Folder Structure
  ```
  app_v2/
  │
  ├── main.py - FastAPI 인스턴스 생성 및 라우터 연결 모듈(실행 가능)
  │
  ├── generate_table.py -  dynamo DB에 새로운 테이블을 생성하는 모듈
  │
  ├── internal/ 
  │       ├── database.py - dynamo DB와 S3 접속 권한 설정 모듈
  │
  ├── router/ 
  │       ├──router.py - 클라이언트에게 Parameters 또는 Request Body에 어떠한  Input 데이터를 받을지 작성하는 모듈 
  │
  ├── domain/ 
  │       ├── domain.py - JSON 또는 Text 형태로 들어오는 Input 데이터를 받기 위해 Schema (for JSON)를 지정한다. 
                          router에서 클라이언트에게 입력 받은 Input 데이터를 DB 접근 Key와 맞추거나, DB에 추가될 value의 형태로 바꾸는 모듈
  │
  ├── repository/ 
  │       ├──repository.py - 실제 DB의 테이블에서 CRUD, Query 이용하여 작업을 수행하는 모듈
  │
 
  ```


## Database
### DynamoDB (AWS)
