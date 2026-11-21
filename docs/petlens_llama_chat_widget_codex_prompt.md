# petlens Llama Chat Widget Codex Prompt

## Codex 실행 프롬프트

프로젝트명: petlens / Recycling unlabeled PET

작업명:
petlens 홈페이지 Real Chat Widget 구현 - Ollama Llama 기반 자유 채팅

목표:
petlens 홈페이지 및 모든 페이지에 Llama와 자유롭게 채팅할 수 있는 modern chat widget을 추가한다.

채팅 위젯은 기본적으로 화면 우측 하단 또는 모바일 하단에 아이콘 상태로 표시된다.
사용자가 아이콘을 클릭하면 깔끔하고 현대적인 팝업 채팅창이 열리고, 로컬 Ollama의 `llama3.2-vision:11b` 모델과 텍스트 채팅을 할 수 있어야 한다.

이번 작업은 text-only chat MVP이다.
이미지 첨부, streaming 응답, DB 대화 저장은 이번 작업에 포함하지 않는다.

가장 중요한 조건:
현재 정상 작동 중인 petlens 서비스에 영향을 주면 안 된다.

특히 아래 기능은 반드시 기존 동작을 유지해야 한다.

- 기존 홈페이지
- 기존 `/api/predict/` 기본 응답 형식
- 기존 웹 Model Test 기능
- 기존 PredictionLog 저장/조회 기능
- 기존 low-confidence / low-margin 자동 수집 기능
- 기존 actual_class 검수 기능
- 기존 학습 데이터 추가 기능
- 기존 Dataset Version Build 기능
- 기존 TrainingJob / run_training_job 기능
- 기존 TrainedModel 상세 화면
- 기존 confusion matrix comparison 기능
- 기존 Dashboard 기능
- 기존 active model 유지 정책
- 기존 Ollama Vision fallback / Vision gate 기능
- 기본 inference/API TTA off 정책

이번 작업은 “기능 추가”이지 “기존 기능 변경”이 아니다.
breaking change는 허용하지 않는다.

---

## 0단계. 현재 상태 확인

먼저 현재 프로젝트 상태를 확인하라.

실행:

```bash
pwd
git status --short
conda run -n dj5 python manage.py check
conda run -n dj5 python manage.py makemigrations --check --dry-run
curl -s http://127.0.0.1:11434/api/version || true
ollama list || true
ollama ps || true
nvidia-smi || true
```

확인할 것:

- 현재 git 변경사항
- Django check 결과
- migration 누락 여부
- Ollama 실행 여부
- `llama3.2-vision:11b` 모델 존재 여부
- GPU/VRAM 상태
- 기존 running service가 있는지
- 기존 training process가 있는지

주의:

- 기존 변경사항이 있으면 덮어쓰지 않는다.
- 기존 실행 중인 Django 서비스는 중단하지 않는다.
- 기존 training process가 있으면 종료하지 않는다.
- 이번 작업은 채팅 기능 추가이므로 DB migration이 꼭 필요한지 먼저 검토한다.
- 채팅 이력은 DB에 저장하지 않기로 했으므로, 가능하면 migration 없이 구현한다.

---

## 1단계. 현재 template / static / API 구조 조사

다음 파일과 구조를 조사하라.

- config urls 또는 root urls.py
- apps/api/views.py
- apps/api/urls.py
- apps/inference/views.py
- apps/inference/services.py
- apps/dashboard/views.py
- templates/base.html
- templates/dashboard/home.html
- templates 관련 home/landing 파일
- static/css/petlens.css
- static/js 구조
- settings 파일
- .env.example 또는 환경변수 예시 파일
- requirements 관련 파일

조사 목적:

1. 공통 layout template이 무엇인지 확인한다.
2. 모든 페이지에 공통으로 들어가는 `base.html` 구조를 확인한다.
3. 현재 홈페이지/대시보드 템플릿 구조를 확인한다.
4. 현재 CSS 스타일, 색상, 버튼, 카드 디자인 톤을 확인한다.
5. JavaScript 파일을 어디에 두는지 확인한다.
6. API URL 구조를 확인한다.
7. 기존 API가 Django view인지 DRF인지 확인한다.
8. 기존 API의 CSRF 처리를 확인한다.
9. Ollama 호출 코드가 이미 있는지 확인한다.
10. 기존 Ollama Vision fallback provider 코드와 충돌하지 않도록 한다.

중요:

- 기존 template block 구조를 깨지 않는다.
- 기존 CSS를 대규모로 재작성하지 않는다.
- 기존 페이지의 기능과 링크를 깨지 않는다.
- 기존 Ollama Vision fallback과 채팅 기능은 분리한다.

---

## 2단계. 기능 요구사항 확정

확정된 요구사항은 다음과 같다.

노출 범위:

- 모든 방문자에게 채팅 위젯 표시
- 모든 페이지에 표시
- 단, settings / .env에서 `CHAT_WIDGET_ENABLED=True/False`로 전체 on/off 가능

모델:

- 현재 설치된 Ollama `llama3.2-vision:11b` 사용
- 단, settings에서 나중에 모델명을 변경 가능하게 구현

대화 저장:

- DB 저장 없음
- 브라우저 JavaScript 메모리에만 대화 유지
- 새로고침하면 대화 사라짐
- API 요청 시 최근 N개 메시지만 history로 전달

UI:

- 데스크톱: 우측 하단 floating chat button + popup chat window
- 모바일: 하단 floating button + 하단 sheet 또는 거의 전체 폭 chat panel
- 모든 페이지에서 기본 상태는 접힌 아이콘 상태
- 클릭하면 팝업/패널 열림
- 다시 닫을 수 있어야 함
- 현대적이고 깔끔한 디자인
- 기존 petlens 디자인과 일관성 유지
- 홈페이지/공통 레이아웃은 기존 기능을 깨지 않는 선에서 반응형 개선

채팅 성격:

- 자유 채팅 가능
- 기본 system prompt는 petlens 서비스 안내 챗봇
- 답변은 기본 한국어
- 페트병 촬영 방법, 이미지 업로드, 인식 결과, 재활용 정보, 서비스 사용법을 친절하게 안내
- 모르는 내용은 확정적으로 말하지 않음
- 개인정보/민감정보 입력을 유도하지 않음

응답 방식:

- 1차 구현은 non-streaming 요청/응답 방식
- streaming, SSE, WebSocket은 이번 작업에서 제외
- 나중에 streaming으로 확장하기 쉽게 JS/API 구조는 분리

API:

- `POST /api/llama/chat/`
- 기존 API 스타일에 맞춰 Django view 또는 DRF view로 구현
- CSRF 처리는 기존 API 구조를 먼저 확인하고 일관성 있게 적용
- 불필요하게 `csrf_exempt`를 남발하지 않는다.

부하 제한:

- 별도 IP rate limit은 이번 작업에서 구현하지 않는다.
- 단, timeout, 최대 입력 길이, history 길이 제한은 서비스 보호를 위해 구현한다.
- Ollama 오류/timeout이 기존 petlens 기능에 영향을 주면 안 된다.

이미지:

- 이번 작업은 텍스트 채팅만 구현
- 이미지 첨부 / Llama Vision 이미지 질의는 향후 작업

운영 문서:

- 별도 문서 작성
- `docs/llama_chat_widget_workflow.md`

---

## 3단계. settings 추가

settings 파일에 chat widget 관련 설정을 추가한다.

현재 프로젝트의 환경변수 로딩 방식이 있으면 그 방식을 따른다.
예: os.getenv, django-environ, decouple 등

추가할 설정 후보:

```python
CHAT_WIDGET_ENABLED = os.getenv("CHAT_WIDGET_ENABLED", "True") == "True"

CHAT_OLLAMA_BASE_URL = os.getenv("CHAT_OLLAMA_BASE_URL", "http://127.0.0.1:11434")
CHAT_OLLAMA_MODEL = os.getenv("CHAT_OLLAMA_MODEL", "llama3.2-vision:11b")
CHAT_OLLAMA_TIMEOUT_SECONDS = int(os.getenv("CHAT_OLLAMA_TIMEOUT_SECONDS", "30"))

CHAT_HISTORY_MAX_MESSAGES = int(os.getenv("CHAT_HISTORY_MAX_MESSAGES", "6"))
CHAT_MESSAGE_MAX_LENGTH = int(os.getenv("CHAT_MESSAGE_MAX_LENGTH", "1000"))
CHAT_SYSTEM_PROMPT = os.getenv(
    "CHAT_SYSTEM_PROMPT",
    "너는 petlens 서비스의 친절한 AI 안내 챗봇이다. 사용자가 페트병 촬영, 이미지 업로드, 제품 인식, 재활용 정보, 서비스 사용법을 쉽게 이해하도록 돕는다. 답변은 짧고 친절한 한국어로 한다. 사용자가 일반 질문을 해도 가능한 범위에서 답하되, petlens 서비스와 관련된 안내를 우선한다. 개인정보나 민감한 정보를 입력하도록 유도하지 않는다."
)
```

주의:

- `CHAT_WIDGET_ENABLED=False`이면 UI에 채팅 위젯을 표시하지 않는다.
- 채팅 API도 disabled 상태에서는 부드럽게 503 또는 JSON error를 반환한다.
- settings 기본값은 운영에서 안전하게 수정 가능해야 한다.
- `.env.example`이 있으면 예시를 추가한다.

---

## 4단계. Ollama chat service 구현

채팅용 Ollama 호출 로직을 별도 service로 구현한다.

추천 파일:

- `apps/api/llama_chat.py`
또는
- `apps/common/ollama_chat.py`
또는
- 기존 프로젝트 구조에 맞는 위치

역할:

1. 사용자 message 검증
2. history 정리
3. system prompt 포함
4. Ollama API 호출
5. 응답 파싱
6. timeout / connection error 처리
7. API view에 결과 반환

Ollama 호출 방식:

- endpoint: `{CHAT_OLLAMA_BASE_URL}/api/chat` 우선 검토
- 현재 Ollama 버전에서 `/api/chat`이 안정적으로 사용 가능하면 사용
- 아니면 `/api/generate` 사용
- 반드시 현재 설치된 Ollama API 동작을 확인하고 구현한다.

권장 payload 예시:

```json
{
  "model": "llama3.2-vision:11b",
  "messages": [
    {"role": "system", "content": "...petlens 안내 챗봇 system prompt..."},
    {"role": "user", "content": "페트병을 어떻게 찍어야 정확도가 높아?"}
  ],
  "stream": false
}
```

응답 구조는 Ollama API에 맞춰 parsing한다.

실패 처리:

- Ollama timeout
- Ollama connection refused
- Ollama invalid response
- model not loaded
- JSON parsing error

실패 시 API 전체가 Django error page를 반환하면 안 된다.
항상 JSON 응답으로 부드럽게 처리한다.

예:

```json
{
  "ok": false,
  "error": "지금은 AI 챗봇 응답이 지연되고 있습니다. 잠시 후 다시 시도해 주세요."
}
```

주의:

- 채팅 내용은 DB에 저장하지 않는다.
- 로그에 사용자 메시지 전문을 남기지 않는다. 개인정보 보호를 위해 필요한 경우 길이/오류만 기록한다.
- Ollama 호출 실패가 기존 PET병 분류 기능에 영향을 주지 않게 한다.

---

## 5단계. Chat API 구현

API URL:

```text
POST /api/llama/chat/
```

요청 예시:

```json
{
  "message": "페트병을 어떻게 찍어야 정확도가 높아?",
  "history": [
    {"role": "user", "content": "안녕"},
    {"role": "assistant", "content": "안녕하세요. petlens 안내 챗봇입니다."}
  ]
}
```

응답 예시:

```json
{
  "ok": true,
  "reply": "페트병 전체가 잘 보이도록 촬영하고, 주변 여백을 충분히 두면 인식 정확도가 높아집니다.",
  "model": "llama3.2-vision:11b"
}
```

disabled 상태 응답 예시:

```json
{
  "ok": false,
  "error": "AI 채팅 기능이 현재 비활성화되어 있습니다."
}
```

검증 규칙:

- message 필수
- message 공백이면 error
- message 최대 길이 제한
- history는 list만 허용
- history는 최근 `CHAT_HISTORY_MAX_MESSAGES`개만 사용
- history role은 user/assistant만 허용
- system role은 클라이언트에서 받지 않는다
- 서버가 system prompt를 직접 붙인다

CSRF/보안:

- 기존 API가 CSRF를 어떻게 처리하는지 먼저 확인한다.
- Django template fetch 방식이면 CSRF token header를 포함하도록 구현한다.
- 기존 프로젝트가 API endpoint에 대해 csrf_exempt 패턴을 쓰고 있다면, 이유를 확인하고 일관성 있게 구현하되 보고서에 명시한다.
- 모든 방문자에게 공개되므로 에러 메시지에 내부 경로나 stack trace를 노출하지 않는다.

URL 연결:

- 기존 `urls.py` 구조에 맞춰 추가
- `/api/llama/chat/` endpoint가 동작해야 한다.

---

## 6단계. Chat Widget UI 구현

채팅 위젯은 모든 페이지에서 표시한다.

권장 방식:

- 공통 template partial 생성
  - `templates/includes/chat_widget.html`
  - 또는 현재 구조에 맞는 위치
- `base.html`에서 `CHAT_WIDGET_ENABLED`일 때 include
- JS 파일 분리
  - `static/js/llama_chat_widget.js`
- CSS는 기존 `static/css/petlens.css`에 추가하거나 별도 CSS 파일 생성
  - 기존 스타일 구조에 맞춘다.

UI 요구사항:

Desktop:

- 우측 하단 floating chat button
- 둥근 원형 또는 pill 형태
- 클릭 시 우측 하단 popup chat window
- popup 크기: 대략 360px x 520px 수준, 화면 크기에 따라 조정
- header, message list, input area 구성
- 닫기 버튼
- loading indicator

Mobile:

- 하단 floating button
- 클릭 시 하단 sheet 또는 거의 전체 폭 panel
- 높이는 화면의 70~85% 정도
- input이 키보드에 가려지지 않도록 최대한 고려
- 작은 화면에서 overflow 처리

디자인 방향:

- 기존 petlens 스타일과 일관성 유지
- 화이트/라이트 기반의 깔끔한 카드형 UI
- 둥근 모서리
- 부드러운 그림자
- 적절한 여백
- 메시지는 말풍선 형태
- 사용자 메시지와 AI 메시지 시각적으로 구분
- 전송 중 “입력 중…” 또는 dot loading 표시
- 오류 시 부드러운 안내 메시지 표시
- z-index는 충분히 높되 기존 모달/메뉴를 과도하게 방해하지 않게 설정

첫 인사말:

- Codex가 현재 디자인 톤에 맞게 짧고 친근하게 작성
- 조건:
  - petlens 서비스 안내 챗봇임이 드러나야 함
  - 페트병 촬영, 이미지 업로드, 인식 결과, 재활용 정보를 물어볼 수 있음을 안내
  - 너무 길거나 딱딱하지 않게
  - 이모지는 0~1개 정도

예시:

```text
안녕하세요 👋 페트병 촬영 방법이나 인식 결과가 궁금하면 편하게 물어보세요.
```

---

## 7단계. Frontend JavaScript 구현

JS 기능:

1. floating button 클릭 시 채팅창 열기/닫기
2. 사용자 메시지 입력
3. Enter로 전송
4. Shift+Enter는 줄바꿈 또는 현재 UI 정책에 맞게 처리
5. 전송 중 input disable
6. loading indicator 표시
7. `/api/llama/chat/`로 fetch POST
8. 최근 history를 함께 전송
9. 응답을 채팅창에 append
10. 오류 시 사용자 친화적 메시지 표시
11. 새로고침 전까지 브라우저 메모리에만 history 유지
12. DB/localStorage 저장하지 않음

history 정책:

- 브라우저 JS 배열에 messages 유지
- API 요청 시 최근 `CHAT_HISTORY_MAX_MESSAGES`개만 전송
- 서버도 다시 제한
- 새로고침하면 사라짐
- localStorage/sessionStorage는 사용하지 않음

보안:

- 사용자 입력은 DOM에 넣을 때 textContent 사용
- innerHTML 직접 삽입 금지
- XSS 방지
- AI 응답도 textContent 기반으로 표시
- 줄바꿈은 안전하게 처리

CSRF:

- 기존 Django CSRF 구조에 맞춰 fetch header에 `X-CSRFToken` 추가
- CSRF가 필요 없는 API 구조라면 기존 방식에 맞추되 보고서에 명시

---

## 8단계. 홈페이지/공통 레이아웃 반응형 개선

채팅 위젯과 충돌하지 않도록 홈페이지/공통 레이아웃을 반응형으로 점검하고 필요한 만큼 개선한다.

주의:

- 기존 디자인을 대규모로 바꾸지 않는다.
- 기존 기능을 깨지 않는다.
- header/nav/main/footer 구조를 먼저 확인한다.
- desktop/tablet/mobile breakpoint를 최소한으로 적용한다.
- 채팅 위젯이 주요 버튼, 하단 CTA, 모바일 navigation을 가리지 않게 한다.
- 모바일에서 화면 가로 overflow가 생기지 않게 한다.
- 기존 Model Test 진입, Dashboard, navigation 링크가 유지되어야 한다.

가능한 개선:

- main container max-width / padding 조정
- 카드 grid 반응형화
- 버튼/텍스트 크기 모바일 대응
- hero section 또는 dashboard card layout 개선
- chat widget이 있는 하단 공간 고려

보고서에 어떤 반응형 개선을 했는지 명시한다.

---

## 9단계. 운영 문서 작성

다음 문서를 작성한다.

```text
docs/llama_chat_widget_workflow.md
```

문서에 포함할 내용:

1. 기능 개요
2. 채팅 위젯 표시 위치
3. 데스크톱/모바일 UI 동작
4. 사용 모델
   - `llama3.2-vision:11b`
5. Ollama endpoint
6. settings / .env 설정값
7. `CHAT_WIDGET_ENABLED`로 on/off 하는 방법
8. `/api/llama/chat/` API 사용법
9. 요청/응답 예시
10. 대화 이력 저장 정책
    - DB 저장 없음
    - 브라우저 메모리에서만 유지
    - 새로고침 시 사라짐
11. system prompt 역할
12. timeout 처리
13. Ollama 실패 시 사용자 안내
14. CSRF/보안 처리 방식
15. XSS 방지 방식
16. 모든 방문자 공개에 따른 GPU 부하 주의
17. 운영 중 문제가 생기면 끄는 방법
18. 향후 개선 계획
    - streaming 응답
    - 이미지 첨부
    - 채팅 전용 경량 모델 분리
    - rate limit
    - 관리자 설정 UI

---

## 10단계. 테스트 요구사항

구현 후 반드시 실행한다.

```bash
conda run -n dj5 python manage.py check
conda run -n dj5 python manage.py makemigrations --check --dry-run
curl -s http://127.0.0.1:11434/api/version
ollama list
ollama ps
nvidia-smi
```

이번 작업은 DB 저장이 없으므로 migration이 없어야 정상일 가능성이 높다.
만약 migration이 발생했다면 이유를 보고하라.

API 테스트:

```bash
curl -X POST http://127.0.0.1:<port>/api/llama/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message":"페트병을 어떻게 찍어야 정확도가 높아?","history":[]}'
```

단, 실제 port는 현재 개발 서버/운영 서버 환경에 맞춰 사용한다.
CSRF가 필요한 구조라면 Django test client 또는 browser에서 테스트한다.

Smoke Test 시나리오:

### A. settings 로딩

- CHAT_WIDGET_ENABLED
- CHAT_OLLAMA_BASE_URL
- CHAT_OLLAMA_MODEL
- CHAT_OLLAMA_TIMEOUT_SECONDS
- CHAT_HISTORY_MAX_MESSAGES
- CHAT_MESSAGE_MAX_LENGTH 확인

### B. widget enabled

- CHAT_WIDGET_ENABLED=True일 때 모든 페이지에 아이콘 표시
- 클릭 시 채팅창 표시

### C. widget disabled

- CHAT_WIDGET_ENABLED=False일 때 아이콘 미표시
- API는 disabled 응답 또는 프로젝트 정책에 맞게 처리

### D. API basic chat

- `/api/llama/chat/`에 message 전송
- Ollama 응답 반환 확인
- model 이름 반환 확인

### E. API validation

- 빈 message
- 너무 긴 message
- 잘못된 history 형식
- system role injection 시도
- 모두 안전하게 처리

### F. Ollama failure

- 잘못된 base_url 또는 timeout 상황을 mock/설정
- 사용자에게 부드러운 error 반환
- Django error page나 stack trace 노출 없음
- 기존 petlens 기능 영향 없음

### G. frontend chat

- 버튼 클릭
- 메시지 전송
- loading 표시
- 응답 표시
- 오류 표시
- 닫기/열기 동작

### H. history

- 브라우저 메모리에서 최근 대화 context 전달
- 새로고침 시 사라짐
- localStorage/DB에 저장되지 않음

### I. responsive desktop

- 데스크톱에서 우측 하단 popup 표시
- 기존 메뉴/버튼 가리지 않음

### J. responsive mobile

- 모바일 폭에서 하단 sheet/panel 표시
- 입력창 사용 가능
- 화면 overflow 없음

### K. XSS safety

- `<script>alert(1)</script>` 같은 입력이 실행되지 않고 텍스트로 표시됨

### L. regression

- 기존 `/api/predict/` 응답 변경 없음
- 웹 Model Test 정상
- PredictionLog 정상
- Dashboard 정상
- Dataset Build / Training workflow 손상 없음
- active model 자동 변경 없음

---

## 11단계. 결과 보고서 형식

작업 완료 후 아래 형식으로 보고하라.

```markdown
# petlens Llama Chat Widget Implementation Report

## Summary

| Stage | Status | Notes |
|---|---:|---|
| Current structure inspection | PASS/FAIL | |
| Existing safety check | PASS/FAIL | |
| Settings integration | PASS/FAIL | |
| Ollama chat service | PASS/FAIL | |
| Chat API | PASS/FAIL | |
| CSRF/security handling | PASS/FAIL | |
| Chat widget template | PASS/FAIL | |
| Chat widget JavaScript | PASS/FAIL | |
| Modern responsive UI | PASS/FAIL | |
| Homepage/common responsive improvements | PASS/FAIL | |
| Browser-only history | PASS/FAIL | |
| Error/timeout handling | PASS/FAIL | |
| Operation manual | PASS/FAIL | |
| Regression safety | PASS/FAIL | |

## Files Modified

- ...

## Files Created

- ...

## Settings Added

- CHAT_WIDGET_ENABLED
- CHAT_OLLAMA_BASE_URL
- CHAT_OLLAMA_MODEL
- CHAT_OLLAMA_TIMEOUT_SECONDS
- CHAT_HISTORY_MAX_MESSAGES
- CHAT_MESSAGE_MAX_LENGTH
- CHAT_SYSTEM_PROMPT

## API

### Endpoint

POST /api/llama/chat/

### Request Example

...

### Response Example

...

## Implementation Details

### Ollama chat service
...

### System prompt
...

### API validation
...

### CSRF/security
...

### Frontend widget
...

### Responsive design
...

### Browser-only history
...

### Timeout/failure handling
...

### Operation manual
...

## Commands Executed

- ...

## Smoke Test Results

| Scenario | Status | Notes |
|---|---:|---|
| A. Settings loading | PASS/FAIL | |
| B. Widget enabled | PASS/FAIL | |
| C. Widget disabled | PASS/FAIL | |
| D. API basic chat | PASS/FAIL | |
| E. API validation | PASS/FAIL | |
| F. Ollama failure | PASS/FAIL | |
| G. Frontend chat | PASS/FAIL | |
| H. History | PASS/FAIL | |
| I. Responsive desktop | PASS/FAIL | |
| J. Responsive mobile | PASS/FAIL | |
| K. XSS safety | PASS/FAIL | |
| L. Regression | PASS/FAIL | |

## Existing Service Impact

- 기존 `/api/predict/` 영향:
- 기존 Model Test 영향:
- 기존 PredictionLog 영향:
- 기존 Dashboard 영향:
- 기존 Dataset/Training 영향:

## Important Notes

- 채팅 이력은 DB에 저장하지 않았다.
- 브라우저 메모리에만 유지되며 새로고침하면 사라진다.
- 이미지 첨부 기능은 이번 작업에 포함하지 않았다.
- streaming 응답은 이번 작업에 포함하지 않았다.
- 모든 방문자에게 표시되지만 CHAT_WIDGET_ENABLED로 끌 수 있다.
- Ollama timeout/error 시 기존 petlens 기능에는 영향이 없다.
- XSS 방지를 위해 사용자 입력과 AI 응답은 안전하게 렌더링했다.

## Operation Manual

작성 문서:
docs/llama_chat_widget_workflow.md

주요 내용:
...

## Remaining Limitations

- streaming 응답이 아니다.
- 이미지 첨부 채팅은 아직 없다.
- 별도 rate limit은 없다.
- 모든 방문자에게 공개되므로 GPU 부하가 증가할 수 있다.
- 채팅 전용 경량 모델을 분리하면 응답 속도 개선 가능성이 있다.
- 향후 llama3.1:8b 또는 llama3.2:3b 같은 텍스트 전용 모델 검토 가능.

## Final Result

PASS 또는 FAIL
```

---

## 12단계. 최종 안전 조건

작업 완료 전 반드시 확인하라.

- `conda run -n dj5 python manage.py check` PASS
- migration 누락 없음
- 기존 `/api/predict/` 응답 변경 없음
- 기존 웹 Model Test 정상
- 기존 PredictionLog 정상
- 기존 Dashboard 정상
- 기존 Dataset Build 정상
- 기존 Training workflow 손상 없음
- active model 자동 변경 없음
- CHAT_WIDGET_ENABLED=False일 때 위젯 숨김
- Ollama timeout/실패 시 기존 서비스 영향 없음
- 채팅 내용 DB 저장 없음
- XSS 위험 없음
- 모바일/데스크톱 모두 UI 깨짐 없음
- 기존 정상 서비스에 영향을 주는 breaking change 없음

최종 결과가 PASS가 아니면 어떤 단계에서 실패했는지, 기존 기능에 영향이 있는지, rollback 또는 수정이 필요한 파일이 무엇인지 명확히 보고하라.
