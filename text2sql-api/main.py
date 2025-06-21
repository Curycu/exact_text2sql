import os
import datetime
import uvicorn
import chromadb

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, Column, Integer, String, DateTime, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer
from fastapi.middleware.cors import CORSMiddleware

# ===============================================================================
# 1. Database and ORM Setup (과거 database.py, models.py)
# ===============================================================================

# API 파일의 위치를 기준으로 절대 경로 계산
API_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DATA_DIR = os.path.join(API_DIR, 'data')
os.makedirs(DB_DATA_DIR, exist_ok=True) # DB 파일 저장 디렉토리 생성

# SQLite 데이터베이스 설정
DATABASE_URL = f"sqlite:///{os.path.join(DB_DATA_DIR, 'golden_records.db')}"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 데이터베이스 테이블 모델 (GoldenRecord)
class GoldenRecordDB(Base):
    __tablename__ = "golden_records"
    id = Column(Integer, primary_key=True, index=True)
    question = Column(String, unique=True, index=True, nullable=False)
    sql_query = Column(String, nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

# ===============================================================================
# 2. Vector DB Setup (과거 services.py 일부)
# ===============================================================================

CHROMA_DB_DIR = os.path.join(API_DIR, "chroma_db")
os.makedirs(CHROMA_DB_DIR, exist_ok=True) # ChromaDB 파일 저장 디렉토리 생성

# ChromaDB 클라이언트 초기화
chroma_client = chromadb.PersistentClient(path=CHROMA_DB_DIR)

# 모델을 처음 사용하는 경우, 아래 local_files_only=True를 False로 변경하여 모델을 다운로드해야 합니다.
MODEL_NAME = 'jhgan/ko-sroberta-multitask'
# 로컬에 모델을 다운로드 받은 후에는 다시 True로 변경하여 사용. 모델 다운로드를 위해 False로 변경합니다.
model = SentenceTransformer(MODEL_NAME, local_files_only=False)

# ChromaDB 컬렉션 가져오기 또는 생성
golden_record_collection = chroma_client.get_or_create_collection("golden_records")

def get_embedding(text: str):
    """주어진 텍스트를 벡터 임베딩으로 변환합니다."""
    return model.encode(text).tolist()

# ===============================================================================
# 3. Pydantic Schemas (과거 schemas.py)
# ===============================================================================

class GoldenRecordBase(BaseModel):
    question: str
    sql_query: str
    name: str

class GoldenRecordCreate(GoldenRecordBase):
    pass

class ExecuteSqlRequest(BaseModel):
    id: int

class GoldenRecord(GoldenRecordBase):
    id: int
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class Question(BaseModel):
    text: str

# ===============================================================================
# 4. CRUD Operations (과거 crud.py)
# ===============================================================================

def create_golden_record(db: Session, record: GoldenRecordCreate):
    """새로운 Golden Record를 SQL DB와 Vector DB에 저장합니다."""
    # SQL DB에 저장
    db_record = GoldenRecordDB(**record.dict())
    db.add(db_record)
    db.commit()
    db.refresh(db_record)

    # Vector DB에 저장
    embedding = get_embedding(record.question)
    golden_record_collection.add(
        ids=[str(db_record.id)],
        embeddings=[embedding],
        metadatas=[{"question": record.question, "sql_query": record.sql_query}]
    )
    return db_record

# ===============================================================================
# 5. FastAPI Application
# ===============================================================================

app = FastAPI()

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    """데이터베이스 세션 종속성"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.on_event("startup")
def on_startup():
    """애플리케이션 시작 시 데이터베이스 테이블을 생성합니다."""
    Base.metadata.create_all(bind=engine)

@app.post("/add-record/", response_model=GoldenRecord)
def add_new_record(record: GoldenRecordCreate, db: Session = Depends(get_db)):
    db_record = db.query(GoldenRecordDB).filter(GoldenRecordDB.question == record.question).first()
    if db_record:
        raise HTTPException(status_code=400, detail="이미 동일한 질문이 존재합니다.")
    return create_golden_record(db=db, record=record)

@app.post("/execute-sql/")
def execute_sql(request: ExecuteSqlRequest, db: Session = Depends(get_db)):
    """주어진 ID의 Golden Record에 저장된 SQL을 실행하고 결과를 반환합니다."""
    
    # 1. ID로 Golden Record 조회
    record = db.query(GoldenRecordDB).filter(GoldenRecordDB.id == request.id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Golden record not found")

    # 2. SQL 실행 및 결과 반환
    try:
        # text()를 사용하여 SQL 문자열을 안전하게 실행 가능한 형태로 변환
        result = db.execute(text(record.sql_query))
        
        # 결과를 [ {column: value}, ... ] 형태로 가공
        keys = result.keys()
        rows = [dict(zip(keys, row)) for row in result.fetchall()]
        
        return {"keys": list(keys), "rows": rows}
    except Exception as e:
        # SQL 실행 중 오류 발생 시
        raise HTTPException(status_code=400, detail=f"SQL 실행 오류: {str(e)}")

@app.post("/ask/")
def ask_question(question: Question):
    """사용자 질문에 대해 유사한 질문을 Vector DB에서 검색하여 반환"""
    query_embedding = get_embedding(question.text)
    results = golden_record_collection.query(
        query_embeddings=[query_embedding],
        n_results=20
    )
    
    if not results or not results["ids"][0]:
        return {"message": "유사한 질문을 찾지 못했습니다."}

    similar_questions = []
    for i in range(len(results["ids"][0])):
        similar_questions.append({
            "id": results["ids"][0][i],
            "question": results["metadatas"][0][i]["question"],
            "sql_query": results["metadatas"][0][i]["sql_query"],
            "distance": results["distances"][0][i]
        })
    return {"results": similar_questions}

@app.get("/")
def read_root():
    """헬스 체크 엔드포인트"""
    return {"status": "ok", "message": "Text2SQL API is running"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
