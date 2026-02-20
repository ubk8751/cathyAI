"""cathyAI - Multi-character AI companion web application.

This module provides the main Chainlit application with multi-character support,
live model switching, and optional emotion detection via external APIs.
"""

import os
import httpx
import chainlit as cl
import json
import time
import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Configuration
CHAT_API_URL = os.getenv("CHAT_API_URL")
MODELS_API_URL = os.getenv("MODELS_API_URL")
EMOTION_API_URL = os.getenv("EMOTION_API_URL")
CHAR_API_URL = os.getenv("CHAR_API_URL", "").rstrip("/")
IDENTITY_API_URL = os.getenv("IDENTITY_API_URL", "").rstrip("/")
CHAT_API_KEY = os.getenv("CHAT_API_KEY")
MODELS_API_KEY = os.getenv("MODELS_API_KEY")
EMOTION_API_KEY = os.getenv("EMOTION_API_KEY")
CHAR_API_KEY = os.getenv("CHAR_API_KEY")
IDENTITY_API_KEY = os.getenv("IDENTITY_API_KEY")
CHAT_TIMEOUT = int(float(os.getenv("CHAT_TIMEOUT", "120")))
MODELS_TIMEOUT = int(float(os.getenv("MODELS_TIMEOUT", "10")))
EMOTION_TIMEOUT = int(float(os.getenv("EMOTION_TIMEOUT", "10")))
EMOTION_ENABLED = os.getenv("EMOTION_ENABLED", "0") == "1"
CHAR_CACHE_PATH = Path("/tmp/characters_cache.json")
CHAR_CACHE_ETAG_PATH = Path("/tmp/characters_cache.etag")
STATE_DIR = Path(os.getenv("STATE_DIR", "/state"))

# HTTP client
client = httpx.AsyncClient()

def char_headers():
    """Generate headers for character API requests.
    
    :return: Dictionary with API key header if configured
    :rtype: dict
    """
    return {"x-api-key": CHAR_API_KEY} if CHAR_API_KEY else {}

async def fetch_characters_list():
    """Fetch character list from API with ETag caching.
    
    :return: List of character dictionaries from API
    :rtype: list[dict]
    :raises Exception: If API is not configured or request fails
    """
    if not CHAR_API_URL:
        raise Exception("CHAR_API_URL not configured")

    url = f"{CHAR_API_URL}/characters"
    headers = char_headers()
    etag = load_cached_etag()
    if etag:
        headers["If-None-Match"] = etag

    resp = await client.get(url, headers=headers, timeout=10)

    if resp.status_code == 304:
        logger.info("Characters list unchanged (304); using cache")
        return load_cached_characters()

    resp.raise_for_status()

    new_etag = resp.headers.get("etag", "")
    save_cached_etag(new_etag)

    data = resp.json()
    chars = data.get("characters", [])
    CHAR_CACHE_PATH.write_text(json.dumps(chars), encoding="utf-8")
    logger.info(f"Fetched {len(chars)} characters from API (etag={new_etag})")
    return chars

def load_cached_characters():
    """Load characters from local cache file.
    
    :return: List of cached character dictionaries
    :rtype: list[dict]
    """
    if CHAR_CACHE_PATH.exists():
        return json.loads(CHAR_CACHE_PATH.read_text(encoding="utf-8"))
    return []

def load_cached_etag():
    """Load cached ETag from file.
    
    :return: Cached ETag string or empty string
    :rtype: str
    """
    return CHAR_CACHE_ETAG_PATH.read_text(encoding="utf-8").strip() if CHAR_CACHE_ETAG_PATH.exists() else ""

def save_cached_etag(etag: str):
    """Save ETag to cache file.
    
    :param etag: ETag value to cache
    :type etag: str
    """
    if etag:
        CHAR_CACHE_ETAG_PATH.write_text(etag.strip(), encoding="utf-8")

async def fetch_character_private(char_id: str):
    """Fetch full character data with prompts from API with ETag caching.
    
    :param char_id: Character identifier
    :type char_id: str
    :return: Character data with resolved prompts
    :rtype: dict
    :raises Exception: If API request fails
    """
    global CHAR_PRIVATE_ETAGS, CHAR_PRIVATE_CACHE
    url = f"{CHAR_API_URL}/characters/{char_id}?view=private"
    headers = char_headers()
    etag = CHAR_PRIVATE_ETAGS.get(char_id)
    if etag:
        headers["If-None-Match"] = etag

    resp = await client.get(url, headers=headers, timeout=10)
    if resp.status_code == 304:
        cached = CHAR_PRIVATE_CACHE.get(char_id)
        if cached:
            logger.info(f"Character {char_id} not modified (ETag cache hit); using cached private data")
            return cached
        # cache miss: fall back to a normal fetch
        resp = await client.get(url, headers=char_headers(), timeout=10)

    resp.raise_for_status()
    CHAR_PRIVATE_ETAGS[char_id] = resp.headers.get("etag") or ""
    data = resp.json()
    CHAR_PRIVATE_CACHE[char_id] = data
    return data

async def fetch_models():
    """Fetch available models from external API.
    
    :return: List of model names available from the API
    :rtype: list[str]
    """
    if not MODELS_API_URL:
        logger.error("MODELS_API_URL not configured")
        return []
    
    try:
        headers = {"Authorization": f"Bearer {MODELS_API_KEY}"} if MODELS_API_KEY else {}
        response = await client.get(MODELS_API_URL, headers=headers, timeout=MODELS_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        models = data.get("models", [])
        logger.info(f"Fetched {len(models)} models from API")
        return models
    except Exception as e:
        logger.error(f"Failed to fetch models: {e}")
        return []

async def stream_chat(model, messages):
    """Stream chat responses from external API (Ollama-compatible).
    
    :param model: Name of the model to use for chat
    :type model: str
    :param messages: List of message dictionaries with role and content
    :type messages: list[dict]
    :yield: Token strings from the streaming response
    :rtype: str
    :raises Exception: If API request fails or times out
    """
    if not CHAT_API_URL:
        raise Exception("CHAT_API_URL not configured")
    
    headers = {"Content-Type": "application/json"}
    if CHAT_API_KEY:
        headers["Authorization"] = f"Bearer {CHAT_API_KEY}"
    
    payload = {"model": model, "messages": messages, "stream": True}
    
    try:
        async with client.stream("POST", CHAT_API_URL, json=payload, headers=headers, timeout=CHAT_TIMEOUT) as response:
            response.raise_for_status()
            last = ""
            async for line in response.aiter_lines():
                if not line.strip():
                    continue
                if line.startswith("data: "):
                    line = line[6:]
                if line == "[DONE]":
                    break
                
                try:
                    chunk = json.loads(line)
                except json.JSONDecodeError:
                    continue
                
                # Ollama NDJSON: {"message":{"content":"..."}, "done":false}
                msg = (chunk.get("message") or {})
                content = msg.get("content")
                if content is not None:
                    # emit only new part
                    if content.startswith(last):
                        delta = content[len(last):]
                    else:
                        delta = content
                    last = content
                    if delta:
                        yield delta
                    continue
                
                # fallback if some other format appears
                if "token" in chunk:
                    yield chunk["token"]
    except httpx.TimeoutException:
        logger.error("Chat API timeout")
        raise Exception("Request timed out")
    except httpx.HTTPStatusError as e:
        logger.error(f"Chat API error: {e}")
        # Fallback to non-streaming
        try:
            payload["stream"] = False
            response = await client.post(CHAT_API_URL, json=payload, headers=headers, timeout=CHAT_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            if "reply" in data:
                yield data["reply"]
        except Exception as fallback_error:
            logger.error(f"Non-streaming fallback failed: {fallback_error}")
            raise

async def detect_emotion(text):
    """Detect emotion from text using external API.
    
    :param text: Text content to analyze for emotion
    :type text: str
    :return: Dictionary with emotion label and confidence score, or None if disabled/failed
    :rtype: dict or None
    """
    if not EMOTION_ENABLED or not EMOTION_API_URL:
        return None
    
    try:
        headers = {"Content-Type": "application/json"}
        if EMOTION_API_KEY:
            headers["Authorization"] = f"Bearer {EMOTION_API_KEY}"
        
        response = await client.post(EMOTION_API_URL, json={"text": text}, headers=headers, timeout=EMOTION_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        return {"label": data.get("label"), "score": data.get("score")}
    except Exception as e:
        logger.warning(f"Emotion detection failed: {e}")
        return None

async def identity_resolve(external_id: str):
    """Resolve external user ID to identity data.
    
    :param external_id: External identifier (e.g. chainlit:username:alice)
    :type external_id: str
    :return: Identity data with person_id and preferred_name, or empty dict if unavailable
    :rtype: dict
    """
    if not IDENTITY_API_URL:
        return {}
    headers = {"x-api-key": IDENTITY_API_KEY} if IDENTITY_API_KEY else {}
    try:
        r = await client.get(
            f"{IDENTITY_API_URL}/identity/resolve",
            params={"external_id": external_id},
            headers=headers,
            timeout=10,
        )
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.warning(f"Identity resolve failed for {external_id}: {e}")
        return {}

# Load characters from API or cache
CHAR_INDEX = {}
CHAR_LIST = []
CHAR_PRIVATE_ETAGS = {}
CHAR_PRIVATE_CACHE = {}
PROFILE_NAME_TO_ID = {}

# Validate configuration
if not CHAR_API_URL:
    logger.warning("CHAR_API_URL not configured")
if not CHAR_API_KEY:
    logger.warning("CHAR_API_KEY not configured (character-api may reject requests)")

@cl.password_auth_callback
def auth_callback(username: str, password: str):
    """Authenticate user against SQLite database.
    
    :param username: Username to authenticate
    :type username: str
    :param password: Password to verify
    :type password: str
    :return: User object if authenticated, None otherwise
    :rtype: cl.User or None
    """
    from users import verify_user
    
    ok, role = verify_user(username, password)
    if not ok:
        return None
    
    return cl.User(identifier=username, metadata={"role": role})

@cl.set_chat_profiles
async def chat_profiles():
    """Define available chat profiles from character API.
    
    :return: List of ChatProfile objects for character selection
    :rtype: list[cl.ChatProfile]
    """
    global CHAR_INDEX, CHAR_LIST, PROFILE_NAME_TO_ID
    
    try:
        CHAR_LIST = await fetch_characters_list()
    except Exception as e:
        logger.warning(f"Failed to fetch characters from API: {e}, using cache")
        CHAR_LIST = load_cached_characters()
    
    if not CHAR_LIST:
        logger.error("No characters available")
        return []
    
    CHAR_INDEX = {char["id"]: char for char in CHAR_LIST}
    PROFILE_NAME_TO_ID = {char["name"]: char["id"] for char in CHAR_LIST if "name" in char and "id" in char}
    
    profiles = []
    for char in CHAR_LIST:
        try:
            icon = char.get("avatar_url") or f"{CHAR_API_URL}/avatars/{char.get('avatar', '')}" if CHAR_API_URL else ""
            profiles.append(
                cl.ChatProfile(
                    name=char["name"],
                    icon=icon,
                    markdown_description=char.get("description", ""),
                    starters=[cl.Starter(label="Greet me", message=char.get("greeting", "Hello there!"))]
                )
            )
        except Exception as e:
            logger.error(f"Failed to create profile for {char.get('id')}: {e}")
    return profiles

@cl.on_chat_start
async def start():
    """Initialize chat session with selected character and model settings.
    
    Sets up user session with character data, conversation history,
    and model selection dropdown in sidebar.
    """
    global CHAR_LIST, CHAR_INDEX, PROFILE_NAME_TO_ID

    if not CHAR_LIST:
        try:
            CHAR_LIST = await fetch_characters_list()
        except Exception as e:
            logger.warning(f"Failed to fetch characters from API in start(): {e}, using cache")
            CHAR_LIST = load_cached_characters()
        CHAR_INDEX = {c["id"]: c for c in CHAR_LIST} if CHAR_LIST else {}
        PROFILE_NAME_TO_ID = {c["name"]: c["id"] for c in CHAR_LIST if "name" in c and "id" in c}

    if not CHAR_LIST:
        await cl.Message(content="⚠️ No characters loaded. Please check configuration.").send()
        return

    current_profile_name = cl.user_session.get("chat_profile")
    char_id = PROFILE_NAME_TO_ID.get(current_profile_name)
    
    if not char_id:
        char_id = CHAR_LIST[0]["id"]
        logger.warning(f"Profile '{current_profile_name}' not found, using {CHAR_LIST[0]['name']}")

    try:
        char = await fetch_character_private(char_id)
        logger.info(f"Fetched full character data for: {char['name']}")
    except Exception as e:
        logger.error(f"Failed to fetch character details: {e}")
        await cl.Message(content="⚠️ Failed to load character. Please try again.").send()
        return

    cl.user_session.set("char", char)
    cl.user_session.set("char_id", char_id)
    
    # Resolve user identity
    app_user = cl.user_session.get("user")
    username = getattr(app_user, "identifier", None) if app_user else None
    external_user_id = f"chainlit:username:{username}" if username else "chainlit:anonymous"
    cl.user_session.set("external_user_id", external_user_id)
    
    ident = await identity_resolve(external_user_id)
    cl.user_session.set("person_id", ident.get("person_id"))
    preferred_name = ident.get("preferred_name") or username or "there"
    cl.user_session.set("preferred_name", preferred_name)
    
    # Inject identity hint into system prompt
    identity_hint = f"The user's preferred name is {preferred_name}. Address them by this name when natural.\n\n"
    system_text = (char.get("prompts") or {}).get("system") or ""
    cl.user_session.set("history", [{"role": "system", "content": identity_hint + system_text}])
    logger.info(f"Chat started with character: {char['name']} for user: {username} (preferred: {preferred_name})")

    # Model selection sidebar with error handling
    try:
        model_names = await fetch_models()
        
        if model_names:
            default_model = model_names[0]
            logger.info(f"Found {len(model_names)} models, using {default_model} as default")
        else:
            logger.warning("No models available")
            model_names = ["No models available"]
            default_model = None
    except Exception as e:
        logger.error(f"Failed to fetch models: {e}")
        model_names = ["No models available"]
        default_model = None

    # Store whether models are available
    cl.user_session.set("model_available", default_model is not None)
    if default_model:
        cl.user_session.set("default_model", default_model)

    try:
        await cl.ChatSettings(
            [
                cl.input_widget.Select(
                    id="Model",
                    label="Ollama Model",
                    values=model_names,
                    initial_value=default_model or model_names[0]
                )
            ]
        ).send()
    except Exception as e:
        logger.error(f"Failed to send chat settings: {e}")

@cl.on_settings_update
async def update_settings(settings):
    """Handle model selection changes from sidebar settings.
    
    :param settings: Updated settings dictionary from user interaction
    :type settings: dict
    """
    cl.user_session.set("settings", settings)

@cl.on_message
async def main(message: cl.Message):
    """Process incoming user messages and generate AI responses.
    
    Handles message streaming, emotion detection, and conversation history.
    
    :param message: Incoming message from user
    :type message: cl.Message
    """
    
    # Debug command: /whoami
    if message.content.strip().lower() == "/whoami":
        await cl.Message(
            content=(
                f"external_user_id: {cl.user_session.get('external_user_id')}\n"
                f"person_id: {cl.user_session.get('person_id')}\n"
                f"preferred_name: {cl.user_session.get('preferred_name')}"
            )
        ).send()
        return

    char = cl.user_session.get("char")
    if not char:
        await cl.Message(content="⚠️ No character selected. Please restart the chat.").send()
        return

    model_available = cl.user_session.get("model_available", False)
    if not model_available:
        author_label = char.get("nickname", char["name"].split(" ", 1)[0] if " " in char["name"] else char["name"])
        await cl.Message(content="⚠️ No models available. Please check API configuration.", author=author_label).send()
        return

    settings = cl.user_session.get("settings", {})
    default_model = cl.user_session.get("default_model")
    selected_model = settings.get("Model", default_model)

    history = cl.user_session.get("history")
    if not history:
        preferred_name = cl.user_session.get("preferred_name", "there")
        identity_hint = f"The user's preferred name is {preferred_name}. Address them by this name when natural.\n\n"
        history = [{"role": "system", "content": identity_hint + char.get("prompts", {}).get("system", "")}]
    history.append({"role": "user", "content": message.content})
    append_event("user", message.content)

    author_label = char.get("nickname", char["name"].split(" ", 1)[0] if " " in char["name"] else char["name"])

    reply = ""
    msg = cl.Message(content="", author=author_label)
    await msg.send()

    try:
        logger.info(f"Calling chat API with model: {selected_model}")
        async for token in stream_chat(selected_model, history):
            reply += token
            await msg.stream_token(token)
    except Exception as e:
        logger.error(f"Chat API error: {e}")
        reply = f"⚠️ Chat API error: {str(e)}"
        await msg.stream_token(reply)

    await msg.update()

    # Emotion detection with error handling
    if reply.strip() and EMOTION_ENABLED:
        emotion_result = await detect_emotion(reply)
        if emotion_result and emotion_result.get("label"):
            await cl.Message(
                content=f"Emotion: {emotion_result['label'].capitalize()} (confidence: {emotion_result['score']:.2f})",
                disable_human_feedback=True
            ).send()

    history.append({"role": "assistant", "content": reply})
    cl.user_session.set("history", history)
    append_event("assistant", reply)

def session_id() -> str:
    """Get current session ID.
    
    :return: Session identifier with chainlit prefix
    :rtype: str
    """
    sid = cl.user_session.get("id") or "unknown"
    return f"chainlit:{sid}"

def append_event(sender: str, text: str):
    """Append conversation event to session log.
    
    Creates NDJSON log files in /state/sessions/<person_id>/<char_id>/<session_id>.ndjson
    for persistent conversation history. Gracefully handles failures without disrupting chat.
    
    :param sender: Message sender (user or assistant)
    :type sender: str
    :param text: Message content
    :type text: str
    """
    try:
        pid = cl.user_session.get("person_id") or "unknown_person"
        cid = cl.user_session.get("char_id") or "unknown_char"
        sid = session_id()
        p = STATE_DIR / "sessions" / pid / cid
        p.mkdir(parents=True, exist_ok=True)
        f = p / f"{sid.replace(':', '_')}.ndjson"
        evt = {
            "ts": int(time.time()),
            "source": "chainlit",
            "session_id": sid,
            "person_id": pid,
            "char_id": cid,
            "sender": sender,
            "text": text,
        }
        with f.open("a", encoding="utf-8") as w:
            w.write(json.dumps(evt, ensure_ascii=False) + "\n")
    except Exception as e:
        logger.warning(f"Failed to append event: {e}")

@cl.on_chat_end
async def on_chat_end():
    """Clean up resources when chat session ends.
    
    Closes the global HTTP client to prevent connection leaks.
    Logs warning if cleanup fails but does not raise exceptions.
    """
    try:
        await client.aclose()
    except Exception as e:
        logger.warning(f"Failed to close HTTP client: {e}")

@cl.action_callback("heartbeat")
async def heartbeat():
    """Handle heartbeat action to maintain activity status.
    
    :return: Status string indicating active state
    :rtype: str
    """
    return "Active"