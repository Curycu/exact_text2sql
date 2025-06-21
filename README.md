# Text2SQL 질의 시스템
자연어 질문을 SQL 쿼리로 변환하고 실행하는 한국어 기반 질의 시스템입니다. cursor 로 vibe coding 되었습니다. (주의!)  

## 🎯 프로젝트 목적

이 프로젝트는 **자연어 질문을 가장 유사한 SQL 쿼리에 맵핑하는 시스템**입니다.

### 주요 기능
- **자연어 질문 처리**: 사용자가 한국어로 질문을 입력하면 유사한 질문을 벡터 데이터베이스에서 검색
- **SQL 쿼리 반환**: 미리 저장된 정답셋(Golden Records)의 SQL을 반환
- **정답셋 관리**: 새로운 질문-SQL 쌍을 추가하여 시스템 학습 데이터 확장

## 🏗️ 기술 스택

### 백엔드
- **FastAPI**: 고성능 웹 프레임워크
- **SQLAlchemy**: ORM 및 데이터베이스 관리
- **ChromaDB**: 벡터 데이터베이스 (의미적 검색)
- **SQLite**: 관계형 데이터베이스

### 프론트엔드
- **HTML5**: 웹 인터페이스
- **jQuery**: JavaScript 라이브러리
- **CSS3**: 스타일링

### AI/ML
- **Sentence Transformers**: 한국어 텍스트 임베딩
- **jhgan/ko-sroberta-multitask**: 한국어 다중 작업 모델

## 📁 프로젝트 구조

```
text2sql/
├── text2sql-api/           # 백엔드 API 서버
│   ├── main.py            # FastAPI 메인 애플리케이션
│   ├── requirements.txt   # Python 의존성
│   ├── data/              # SQLite 데이터베이스 파일
│   └── chroma_db/         # ChromaDB 벡터 데이터베이스
├── text2sql-ui/           # 프론트엔드 웹 인터페이스
│   └── index.html         # 메인 웹 페이지
└── text2sql-start.sh      # 프로젝트 실행 스크립트
```

## 🚀 설치 및 실행

### 1. 저장소 클론
```bash
git clone <repository-url>
cd text2sql
```

### 2. Python 가상환경 생성 및 활성화
```bash
cd text2sql-api
source venv/bin/activate  # macOS/Linux
```

### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

### 4. 프로젝트 실행
```bash
# 프로젝트 루트 디렉토리로 이동
cd ..
chmod +x text2sql-start.sh
./text2sql-start.sh
```

실행 스크립트 text2sql-start.sh은 다음 작업을 자동으로 수행합니다:
- 기존 8000번 포트 프로세스 종료
- FastAPI 서버 백그라운드 실행 (http://0.0.0.0:8000)
- 웹 브라우저에서 UI 자동 열기

## 🔄 작동 방식

1. **질문 입력**: 사용자가 자연어 질문 입력 (예: "지난달 최고 매출 상품은?")
2. **벡터 변환**: 질문을 벡터 임베딩으로 변환
3. **유사도 검색**: ChromaDB에서 유사한 질문 검색
4. **SQL 표시**: 해당하는 SQL 쿼리 표시

## 📊 데이터 구조

### Golden Records
- **질문 (Question)**: 사용자가 입력하는 자연어 질문
- **SQL 쿼리 (SQL Query)**: 해당 질문에 대한 SQL 쿼리
- **작성자 (Name)**: 정답셋을 추가한 사용자 정보
- **생성일시 (Created At)**: 레코드 생성 시간

### 벡터 데이터베이스
- 질문의 의미적 유사성을 검색하기 위한 임베딩 저장
- 한국어 다중 작업 모델을 사용한 벡터 변환

## 🌐 API 엔드포인트

### 주요 API
- `POST /add-record/`: 새로운 정답셋 추가
- `POST /execute-sql/`: ID 기반 SQL 쿼리 실행
- `POST /ask/`: 자연어 질문에 대한 유사 질문 검색
- `GET /`: 헬스 체크

## 💡 사용 예시

### 웹 인터페이스 사용
1. text2sql-start.sh 실행 
2. 질문 입력 필드에 자연어 질문 입력
3. "질의" 버튼 클릭
4. 유사한 질문 목록에서 원하는 결과 선택
5. 해당 SQL 확인

### 새로운 정답셋 추가
1. "새로운 정답셋 추가하기" 버튼 클릭
2. 질문, SQL 쿼리, 작성자 이름 입력
3. "추가" 버튼으로 저장

## 🔧 개발 환경 설정

### 환경 요구사항
- Python 3.8+
- pip
- 웹 브라우저

### 개발 모드 실행
```bash
cd text2sql-api
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 📞 문의

프로젝트에 대한 문의사항이 있으시면 이슈를 생성해 주세요. 
