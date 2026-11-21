# THESYSM Gateway Llama Chat Widget Workflow

## Overview

`www.thesysm.com` home gateway provides a floating AI chat widget for service navigation help. It is implemented in the `home` Django project and is independent from petlens.

## UI

- Desktop: fixed bottom-right button opens a popup panel.
- Mobile: fixed bottom button opens a bottom sheet style panel.
- The widget uses only `th-chat-` prefixed CSS classes.
- Existing gateway card, header, hero, footer, and inactive service styles are not redefined.

## Model And Endpoint

- Ollama model: `llama3.2-vision:11b`
- Ollama base URL: `http://127.0.0.1:11434`
- Ollama endpoint: `/api/chat`
- Gateway API: `POST /api/llama/chat/`
- Response mode: non-streaming
- Image upload: not included

## Settings

```env
CHAT_WIDGET_ENABLED=True
CHAT_OLLAMA_BASE_URL=http://127.0.0.1:11434
CHAT_OLLAMA_MODEL=llama3.2-vision:11b
CHAT_OLLAMA_TIMEOUT_SECONDS=30
CHAT_HISTORY_MAX_MESSAGES=6
CHAT_MESSAGE_MAX_LENGTH=1000
CHAT_SYSTEM_PROMPT=너는 THESYSM Master Service Gateway의 친절한 AI 안내 챗봇이다.
```

Set `CHAT_WIDGET_ENABLED=False` to remove the widget from the page and return a disabled JSON response from the chat API.

## API

Request:

```json
{
  "message": "petlens는 어떤 서비스야?",
  "history": [
    {"role": "user", "content": "안녕"},
    {"role": "assistant", "content": "안녕하세요. THESYSM 서비스 안내를 도와드릴게요."}
  ]
}
```

Response:

```json
{
  "ok": true,
  "reply": "petlens는 PET 병 형태 분류를 위한 AI 운영 서비스입니다.",
  "model": "llama3.2-vision:11b"
}
```

## Data Policy

- Chat history is not saved to the database.
- Browser JavaScript memory keeps recent messages only until refresh.
- `localStorage` and `sessionStorage` are not used.

## Security

- The API keeps Django CSRF protection.
- The widget sends `X-CSRFToken`.
- User and assistant messages are rendered with `textContent`.
- Client-provided `system` roles are ignored; the server inserts the system prompt.
- Internal exceptions and stack traces are not exposed.

## Failure Handling

Ollama timeout, connection errors, and invalid responses return a friendly JSON error. This does not affect petlens, `/api/predict/`, or any petlens model/vision fallback behavior.

## Future Improvements

- Streaming responses
- Image attachment
- Chat-specific lightweight model
- Rate limiting
- Admin setting UI
