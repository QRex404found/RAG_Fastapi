# 🐍 QRex RAG Analyzer (FastAPI & LangChain)

**QRex RAG Analyzer**는 QR 코드 및 URL의 피싱 위험도를 심층 분석하기 위한 **Python 기반의 AI 마이크로서비스**입니다.
**FastAPI**의 고성능 비동기 처리와 **LangChain**의 정교한 프롬프트 엔지니어링을 결합하여, Spring 메인 서버로부터 요청받은 의심 URL을 정밀 진단합니다.

> **Project QRex (404 FOUND Team)**
> **Microservice:** AI Deep Analysis Engine

---

## 🚀 Key Features

### 1. ⚡ High-Performance API (FastAPI)
- **비동기 처리(Async IO):** 다수의 분석 요청을 병목 없이 처리하기 위해 `uvicorn` 기반의 ASGI 서버로 구축되었습니다.
- **경량화:** 분석에 불필요한 기능을 배제하고, 오직 **LLM 추론과 데이터 처리**에 집중한 마이크로서비스 구조입니다.

### 2. 🧠 LangChain 기반 RAG 파이프라인
- **Context Injection:** 최신 피싱 사례, 화이트리스트, 블랙리스트 데이터를 LLM의 컨텍스트 윈도우에 주입하여 환각(Hallucination)을 억제합니다.
- **Prompt Engineering:** 보안 전문가의 판단 로직(도메인 검증 → 타이포스쿼팅 확인 → 위험 패턴 분석)을 프롬프트 단계에서 구조화했습니다.

### 3. 🛡️ Hybrid Safety Check
- **Dual-Layer Filtering:**
  1. **Pre-check:** Python 메모리 상의 블랙리스트 `Set`을 통한 O(1) 속도의 즉시 차단.
  2. **AI Analysis:** 블랙리스트에 없더라도, **Gemini 2.5 Flash** 모델이 URL의 미세한 변형(Typosquatting)과 구조적 위험성을 추론.

---

## 🛠 Tech Stack

| Category | Technology | Description |
| :--- | :--- | :--- |
| **Language** | **Python 3.9+** | AI 및 데이터 처리에 최적화된 생태계 활용 |
| **Web Framework** | **FastAPI** | 고성능 API 서버 구축 및 Pydantic 데이터 검증 |
| **LLM Orchestration** | **LangChain** | LLM 체인 구성, 프롬프트 템플릿 관리 |
| **LLM Model** | **Google Gemini** | `gemini-2.5-flash` (속도와 추론 능력의 균형) |
| **Vector/Data** | **Local Knowledge** | 텍스트 기반 지식 베이스 및 Chroma DB 호환 구조 |

---

## 📂 System Architecture & Logic

### 🔍 분석 파이프라인 (Analysis Pipeline)

교수님 및 평가자를 위한 핵심 로직 설명입니다.

1.  **Request Ingestion:** Spring 서버로부터 `URL`, `IP Location`, `Safe Browsing Result`를 수신합니다.
2.  **Fast Filtering (Rule-Based):**
    - `urlparse`를 통해 도메인을 추출하고, 메모리에 로드된 `BLACKLIST`와 대조합니다.
    - 매칭 시 LLM을 호출하지 않고 즉시 `DANGEROUS` 응답을 반환하여 비용과 시간을 절약합니다.
3.  **Context Loading:**
    - `data/` 디렉토리의 최신 보안 지식(`.txt`)을 로드하여 프롬프트 컨텍스트(`{context_text}`)로 구성합니다.
4.  **LLM Reasoning (Chain Execution):**
    - **LangChain**이 구성한 프롬프트를 **Gemini**에 전송합니다.
    - AI는 "블랙리스트 확인 > 화이트리스트 대조 > 타이포스쿼팅 탐지 > URL 구조 분석" 순서로 사고(Chain of Thought)합니다.
5.  **Structured Output:**
    - 최종 결과를 파싱하기 쉬운 JSON 포맷으로 반환합니다.

---

## 🔌 API Specification

### 🧪 URL 심층 분석 엔드포인트
**POST** `/analyze-qr`

Spring Backend 또는 외부 클라이언트로부터 분석 요청을 처리합니다.

**Request (JSON):**
```json
{
  "url": "[http://naver-login-secure.com](http://naver-login-secure.com)",
  "ip_location": "China",
  "safe_browsing_result": "Clean"
}
