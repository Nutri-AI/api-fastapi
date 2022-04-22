<div align="center">
  <img width="30%" alt="NutriAI_logo" src="https://user-images.githubusercontent.com/33509018/162863401-8f624292-3c11-4038-8b3a-b15b8803e000.png" title="NutriAI">
</div>

# Nutri-AI 

이미지 분석을 통한 식단 분석 및 영양제 추천 서비스 구현

## API
[app_v3 - NutriAI 구현 서비스](https://github.com/Nutri-AI/api-fastapi/tree/dev3/app_v3)
### FastAPI Docs
https://fastapi.tiangolo.com/

## Folder Structure
  ```
  app_v3/
  │
  ├── main.py - FastAPI 인스턴스 생성 및 라우터 연결 모듈(실행 가능)
  │
  ├── generate_table.py -  dynamo DB에 새로운 테이블을 생성하는 모듈
  │
  ├── internal/ 
  │       ├── database.py - dynamo DB와 S3 연동을 위해 접속 권한 키 작성 모듈
  │
  ├── router/ 
  │       ├── router.py - 클라이언트에게 Parameters 또는 Request Body에 어떠한 Input 데이터를 받을지 작성하는 모듈 
  │
  ├── domain/ 
  │       ├── domain.py - JSON 또는 Text 형태로 들어오는 Input 데이터를 받기 위해 Schema(for JSON)를 지정. 
  │                       router에서 클라이언트에게 입력 받은 Input 데이터를 DB 접근 Key와 맞추거나, 
  │                       DB에 추가될 value의 형태로 바꾸는 모듈
  │
  ├── repository/ 
  │       ├── repository.py - 실제 DB의 테이블에서 CRUD, Query 이용하여 작업을 수행하는 모듈
  │       ├── tablename.py - DynamoDB 테이블 이름 작성
  │
 
  ```
  ## Requirements
  [Dockerfile](https://github.com/Nutri-AI/api-fastapi/blob/feature_jh/Dockerfile)

## Transaction
1. 신규 유저 가입
2. 유저 정보 업데이트 - physique, RDI 수정
3. 유저 physique 정보 요청
4. 유저 정보 요청
5. 유저 RDI 정보 요청
6. 식단 이미지 S3 파일 서버에 업로드
7. Inference 이미지 S3 파일 서버에서 가져오기
8. 음식 영양 성분 요청
9. 유저 식단 섭취 로그 등록
10. 사용자 영양상태 로그 요청 - 특정 날짜 (식단 - 탄단지)
11. 사용자 영양 상태 로그 요청 - 오늘부터 ndays일 (식단 + 영양제)
12. today homepage 필요 정보 요청
13. a week status 필요 정보 요청
14. 유저 영양제 추천
## Database
### DynamoDB (AWS)
