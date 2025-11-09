# fastapi_server/rag_module.py

import os
from dotenv import load_dotenv
# from langchain_community.vectorstores import Chroma  # <-- 삭제
# from langchain_google_genai import GoogleGenerativeAIEmbeddings # <-- 삭제
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from google import genai 
import pathlib
# from langchain_community.document_loaders import DirectoryLoader, TextLoader # <-- 추가 로직이 필요 없음

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") 
BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" 

# --- 지식 베이스 텍스트를 저장할 전역 변수 ---
KNOWLEDGE_TEXTS = "" 
# ---------------------------------------------


def initialize_rag_chain():
    global KNOWLEDGE_TEXTS # <-- 전역 변수 사용 명시
    
    print("RAG 체인 초기화 시작...")
    
    if not GEMINI_API_KEY:
        print("FATAL: GEMINI_API_KEY 환경 변수가 설정되지 않았습니다.")
        return None
        
    os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY

    try:
        # =======================================================
        # !!! 수정 1: 지식 베이스 텍스트를 메모리에 직접 로드 !!!
        # =======================================================
        knowledge_texts = ""
        for file_name in os.listdir(DATA_PATH):
            if file_name.endswith(".txt"):
                file_path = DATA_PATH / file_name
                with open(file_path, 'r', encoding='utf-8') as f:
                    knowledge_texts += f.read() + "\n\n---\n\n"
        
        if not knowledge_texts:
            print("FATAL: data 폴더에 .txt 지식 파일이 없습니다.")
            return None
            
        KNOWLEDGE_TEXTS = knowledge_texts # <-- 전역 변수에 저장
        # -----------------------------------------------------------------

        # 2. LLM 설정 (클라이언트 객체 주입)
        print("Gemini API 클라이언트 초기화...")
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash", 
            temperature=0, 
            client=gemini_client,
            model_kwargs={"response_mime_type": "application/json"}
        )
        
        # 3. 프롬프트 템플릿 정의 (Context 변수 수정)
        template = """
        당신은 최고의 QR코드 피싱(큐싱) 탐지 전문가입니다.
        주어진 'URL'과 '추가 정보'가 피싱 위험이 있는지 아래의 '전체 지식 베이스'를 참조하여 분석하고, 최종 판단을 'JSON 형식'으로 내려주세요.
        **경고: 현재 시스템은 임베딩 오류로 인해 모든 지식 베이스를 직접 읽고 판단하고 있습니다. 검색된 정보만 참조하십시오.**

        [전체 지식 베이스 (패턴/블랙리스트/화이트리스트)]
        {context_text}

        [분석 대상 URL 및 추가 정보]
        URL: {question}
        IP 위치: {ip_location}
        실시간 Safe Browsing 결과: {safe_browsing_result}

        [출력 형식]
        {{
          "url": "분석한 URL",
          "risk_level": "최종 판단 (반드시 'SAFE', 'SUSPICIOUS', 'DANGEROUS' 중 하나로만 응답)",
          "reason": "위험도를 판단한 핵심 근거 (지식 베이스와 추가 정보를 종합하여 논리적으로 설명)",
          "analysis_details": [
            "참고 정보와의 일치 여부 (화이트리스트, 패턴 등)",
            "URL 구조의 비정상성",
            "IP 위치/실시간 검증 결과 반영"
          ]
        }}
        """
        prompt = ChatPromptTemplate.from_template(template)

        # 4. RAG 체인 구성 (RunnablePassthrough에서 지식 텍스트를 직접 전달)
        # Context 변수가 knowledge_texts를 받도록 설정
        rag_chain_local = (
            # Question과 추가 정보를 받습니다. Context는 main.py에서 전달됩니다.
            {"context_text": RunnablePassthrough(), "question": RunnablePassthrough(), "ip_location": RunnablePassthrough(), "safe_browsing_result": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
        )
        print("RAG 체인 초기화 완료 (임베딩 우회 모드).")
        return rag_chain_local

    except Exception as e:
        print(f"RAG 초기화 중 오류 발생: {e}")
        return None