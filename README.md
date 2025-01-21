# 공책 RPG (Notebook RPG)

추억의 학창시절 공책 RPG를 웹게임으로 재구현한 프로젝트입니다.

## 특징
- 레트로한 공책 스타일의 UI
- 구글/네이버 소셜 로그인
- 게임 진행 상황 자동 저장
- RPG 요소 (능력치, 장비, 크리티컬 등)

## 기술 스택
- Backend: Python Flask
- Database: SQLAlchemy
- Authentication: OAuth2.0
- Frontend: HTML5, CSS3, JavaScript

## 설치 방법
1. 저장소 클론
```bash
git clone [repository-url]
cd notebook-rpg
```

2. 가상환경 생성 및 활성화
```bash
python -m venv venv
venv\Scripts\activate
```

3. 의존성 설치
```bash
pip install -r requirements.txt
```

4. 환경변수 설정
`.env` 파일을 생성하고 필요한 환경변수를 설정하세요:
```
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-secret-key
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

5. 데이터베이스 초기화
```bash
flask db upgrade
```

6. 서버 실행
```bash
flask run
```
