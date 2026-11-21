import json
import logging
from urllib import error, request

from django.conf import settings

logger = logging.getLogger(__name__)

USER_ERROR_MESSAGE = "지금은 AI 챗봇 응답이 지연되고 있습니다. 잠시 후 다시 시도해 주세요."
ALLOWED_HISTORY_ROLES = {"user", "assistant"}


class LlamaChatValidationError(Exception):
    pass


class LlamaChatServiceError(Exception):
    pass


def build_chat_response(message, history=None):
    clean_message = validate_message(message)
    clean_history = normalize_history(history)
    model = getattr(settings, "CHAT_OLLAMA_MODEL", "llama3.2-vision:11b")
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": getattr(settings, "CHAT_SYSTEM_PROMPT", "")},
            *clean_history,
            {"role": "user", "content": clean_message},
        ],
        "stream": False,
    }
    raw_response = call_ollama_chat(payload)
    return {
        "ok": True,
        "reply": extract_reply(raw_response),
        "model": model,
    }


def validate_message(message):
    if not isinstance(message, str):
        raise LlamaChatValidationError("message is required.")
    clean_message = message.strip()
    if not clean_message:
        raise LlamaChatValidationError("message is required.")
    max_length = int(getattr(settings, "CHAT_MESSAGE_MAX_LENGTH", 1000))
    if len(clean_message) > max_length:
        raise LlamaChatValidationError(f"message must be {max_length} characters or fewer.")
    return clean_message


def normalize_history(history):
    if history in (None, ""):
        return []
    if not isinstance(history, list):
        raise LlamaChatValidationError("history must be a list.")
    clean_history = []
    for item in history:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        content = item.get("content")
        if role not in ALLOWED_HISTORY_ROLES or not isinstance(content, str):
            continue
        clean_content = content.strip()
        if clean_content:
            clean_history.append({"role": role, "content": clean_content})
    max_messages = int(getattr(settings, "CHAT_HISTORY_MAX_MESSAGES", 6))
    return clean_history[-max_messages:]


def call_ollama_chat(payload):
    base_url = getattr(settings, "CHAT_OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
    timeout = int(getattr(settings, "CHAT_OLLAMA_TIMEOUT_SECONDS", 30))
    req = request.Request(
        f"{base_url}/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except TimeoutError as exc:
        logger.warning("Ollama gateway chat timed out after %ss.", timeout)
        raise LlamaChatServiceError(USER_ERROR_MESSAGE) from exc
    except error.URLError as exc:
        logger.warning("Ollama gateway chat connection failed: %s", exc.reason)
        raise LlamaChatServiceError(USER_ERROR_MESSAGE) from exc
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("Ollama gateway chat response failed: %s", exc)
        raise LlamaChatServiceError(USER_ERROR_MESSAGE) from exc


def extract_reply(raw_response):
    if not isinstance(raw_response, dict):
        raise LlamaChatServiceError(USER_ERROR_MESSAGE)
    message = raw_response.get("message")
    if not isinstance(message, dict):
        raise LlamaChatServiceError(USER_ERROR_MESSAGE)
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise LlamaChatServiceError(USER_ERROR_MESSAGE)
    return content.strip()
