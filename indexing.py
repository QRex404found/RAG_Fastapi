# qishing-rag-project/indexing.py

import os
from dotenv import load_dotenv
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings # Gemini 임베딩 사용
from langchain_community.vectorstores import Chroma

load_dotenv()

# .env에서 키를 가져옵니다. (rag_module.py와 동일)
GOOGLE_API_KEY_VALUE = os.getenv("GEMINI_API_KEY")

# 데이터가 저장된 폴더와 벡터 DB를 저장할 폴더 지정
DATA_PATH = "data"
DB_PATH = "vectorstores" # rag_module.py의 DB_PATH와 일치해야 합니다.

if __name__ == "__main__":
    if not GOOGLE_API_KEY_VALUE:
        print("FATAL: GEMINI_API_KEY가 설정되지 않았습니다. 인덱싱을 진행할 수 없습니다.")
        exit()

    # LangChain이 인식하는 표준 환경 변수에 키를 설정합니다. (키 주입)
    os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY_VALUE
    print("Gemini API Key가 성공적으로 로드되었습니다. 초기화 계속...")
    
    print("=== 1단계: 지식 베이스 파일 로드 ===")
    # 프로젝트 루트에 'data' 폴더가 있고, .txt 파일이 있다고 가정합니다.
    loader = DirectoryLoader(DATA_PATH, glob="**/*.txt", loader_cls=TextLoader, show_progress=True)
    documents = loader.load()
    print(f"총 {len(documents)}개의 문서를 불러왔습니다.")

    print("=== 2단계: 문서 분할 (Chunking) ===")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    splits = text_splitter.split_documents(documents)
    print(f"총 {len(splits)}개의 청크(Chunk)로 분할되었습니다.")
    
    print("=== 3단계: 임베딩 및 벡터 DB 저장 (인덱싱) ===")
    
    # 임베딩 모델 설정 (FastAPI의 rag_module.py와 동일한 모델 및 키 사용)
    embeddings = GoogleGenerativeAIEmbeddings(
        model="text-embedding-004"
    )

    # 기존 벡터 DB 폴더 삭제 (새 모델로 인덱싱할 때 이전 데이터와의 충돌 방지)
    if os.path.exists(DB_PATH):
        print(f"경고: 기존 벡터 DB 폴더 ({DB_PATH})를 삭제합니다.")
        import shutil
        shutil.rmtree(DB_PATH)

    # ChromaDB에 분할된 문서와 임베딩 벡터 저장
    vectordb = Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        persist_directory=DB_PATH
    )

    print(f"성공: 벡터 DB에 {vectordb._collection.count()}개의 벡터를 저장했습니다.")
    print("=== 지식 베이스 인덱싱 완료 ===")