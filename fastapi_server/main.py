# fastapi_server/main.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
# rag_module에서 get_rag_chain을 제거했으므로, initialize_rag_chain만 임포트합니다.
from .rag_module import initialize_rag_chain, KNOWLEDGE_TEXTS 

# --- 전역 변수 정의 ---
# initialize_rag_chain의 결과를 저장할 변수입니다.
# Uvicorn의 서브 프로세스에서 이 전역 변수를 공유하여 사용합니다.
global_rag_chain = None 
# ----------------------

# --- 1. FastAPI 애플리케이션 인스턴스 생성 ---
app = FastAPI(
    title="QR Phishing RAG Analyzer",
    description="RAG 기반으로 URL의 피싱 위험도를 분석하는 API 서버"
)

# --- 2. 요청/응답 데이터 모델 정의 ---
class AnalysisRequest(BaseModel):
    url: str
    # Spring Boot에서 미리 추출하거나 조회하여 전달할 추가 정보
    ip_location: str = "정보 없음"
    safe_browsing_result: str = "미확인"

class AnalysisResponse(BaseModel):
    # RAG의 JSON 출력을 문자열로 전달받음
    rag_json_result: str

# --- 3. 서버 이벤트 (RAG 체인 로드) ---
@app.on_event("startup")
async def startup_event():
    """서버 시작 시 RAG 체인을 미리 로드하고 전역 변수에 저장합니다."""
    global global_rag_chain
    # initialize_rag_chain()이 객체를 반환하면 전역 변수에 저장됩니다.
    global_rag_chain = initialize_rag_chain()

# --- 4. 핵심 API 엔드포인트 정의 ---
@app.post("/analyze-qr", response_model=AnalysisResponse)
async def analyze_qr_endpoint(request: AnalysisRequest):
    rag_chain = global_rag_chain
    
    if rag_chain is None:
        raise HTTPException(status_code=503, detail="RAG 모델이 초기화되지 않았습니다.")

    print(f"\n[분석 요청] URL: {request.url}")

    try:
        # RAG 체인 실행
        result_json_str = rag_chain.invoke({
            # KNOWLEDGE_TEXTS 전역 변수를 context_text로 전달
            "context_text": KNOWLEDGE_TEXTS, 
            "question": request.url,
            "ip_location": request.ip_location,
            "safe_browsing_result": request.safe_browsing_result
        })

        print(f"[RAG 결과 수신] 길이: {len(result_json_str)}")
        
        return AnalysisResponse(rag_json_result=result_json_str)

    except Exception as e:
        # RAG 체인 실행 중 발생하는 실제 오류 메시지를 반환하여 진단에 사용합니다.
        error_type = type(e).__name__
        error_msg = str(e).split('\n')[0] 
        
        error_detail = f"RAG 체인 실행 실패 ({error_type}): {error_msg}"
        print(f"RAG 체인 실행 중 오류 발생: {error_detail}") 
        
        # 503 오류와 함께 실제 오류 내용을 응답 detail로 반환
        raise HTTPException(status_code=503, detail=error_detail) 
    
# --- 5. 서버 실행 (테스트용) ---
if __name__ == "__main__":
    # 이 스크립트를 직접 실행할 때만 작동합니다.
    uvicorn.run(app, host="0.0.0.0", port=8000)