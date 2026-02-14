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
CHAT_API_KEY = os.getenv("CHAT_API_KEY")
MODELS_API_KEY = os.getenv("MODELS_API_KEY")
EMOTION_API_KEY = os.getenv("EMOTION_API_KEY")
CHAT_TIMEOUT = int(float(os.getenv("CHAT_TIMEOUT", "120")))
MODELS_TIMEOUT = int(float(os.getenv("MODELS_TIMEOUT", "10")))
EMOTION_TIMEOUT = int(float(os.getenv("EMOTION_TIMEOUT", "10")))
EMOTION_ENABLED = os.getenv("EMOTION_ENABLED", "0") == "1"

# HTTP client
client = httpx.AsyncClient()

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

# Load characters dynamically with validation
CHARACTERS = {}
char_dir = Path("../characters")
if not char_dir.exists():
    logger.error("Characters directory not found")
else:
    for f in char_dir.glob("*.json"):
        try:
            with open(f, 'r') as file:
                char_data = json.load(file)
            
            # Validate required fields
            required_fields = ["name", "avatar", "model", "system_prompt", "greeting"]
            missing = [field for field in required_fields if field not in char_data]
            if missing:
                logger.error(f"Character {f.name} missing fields: {missing}")
                continue
            
            # Load system prompt from external file if specified
            if "system_prompt" in char_data and not char_data["system_prompt"].startswith("You"):
                prompt_path = Path("../characters/system_prompt") / char_data["system_prompt"]
                if prompt_path.exists():
                    char_data["system_prompt"] = prompt_path.read_text().strip()
                else:
                    logger.error(f"System prompt file not found: {prompt_path}")
                    continue
            
            CHARACTERS[f.stem] = char_data
            logger.info(f"Loaded character: {char_data['name']}")
        except Exception as e:
            logger.error(f"Failed to load character {f.name}: {e}")

if not CHARACTERS:
    logger.error("No characters loaded! App may not function correctly.")

def update_activity():
    """Update activity timestamp for watchdog monitoring.
    
    Writes current Unix timestamp to /tmp/activity.last for container
    shutdown monitoring by watchdog.sh script.
    """
    try:
        Path("/tmp/activity.last").write_text(str(int(time.time())))
    except Exception as e:
        logger.error(f"Failed to update activity timestamp: {e}")

update_activity()

@cl.set_chat_profiles
async def chat_profiles():
    """Define available chat profiles from loaded characters.
    
    :return: List of ChatProfile objects for character selection
    :rtype: list[cl.ChatProfile]
    """
    if not CHARACTERS:
        logger.warning("No characters available for profiles")
        return []
    
    profiles = []
    for char_id, char in CHARACTERS.items():
        try:
            profiles.append(
                cl.ChatProfile(
                    name=char["name"],
                    icon=f"/public/avatars/{char['avatar']}",
                    markdown_description=char.get("description", ""),
                    starters=[cl.Starter(label="Greet me", message=char.get("greeting", "Hello there!"))]
                )
            )
        except Exception as e:
            logger.error(f"Failed to create profile for {char_id}: {e}")
    return profiles

@cl.on_chat_start
async def start():
    """Initialize chat session with selected character and model settings.
    
    Sets up user session with character data, conversation history,
    and model selection dropdown in sidebar.
    """
    update_activity()

    if not CHARACTERS:
        await cl.Message(content="⚠️ No characters loaded. Please check configuration.").send()
        return

    # Get current profile (set by Chainlit)
    current_profile_name = cl.user_session.get("chat_profile")
    char = next((c for c in CHARACTERS.values() if c["name"] == current_profile_name), None)
    
    # Fallback to first character if profile not found
    if not char:
        char = list(CHARACTERS.values())[0]
        logger.warning(f"Profile '{current_profile_name}' not found, using {char['name']}")

    cl.user_session.set("char", char)
    cl.user_session.set("history", [{"role": "system", "content": char["system_prompt"]}])
    logger.info(f"Chat started with character: {char['name']}")

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
    update_activity()

    char = cl.user_session.get("char")
    if not char:
        await cl.Message(content="⚠️ No character selected. Please restart the chat.").send()
        return

    # Check if models are available
    model_available = cl.user_session.get("model_available", False)
    if not model_available:
        author_label = char.get("nickname", char["name"].split(" ", 1)[0] if " " in char["name"] else char["name"])
        await cl.Message(content="⚠️ No models available. Please check API configuration.", author=author_label).send()
        return

    settings = cl.user_session.get("settings", {})
    default_model = cl.user_session.get("default_model")
    selected_model = settings.get("Model", default_model)

    history = cl.user_session.get("history", [{"role": "system", "content": char["system_prompt"]}])
    history.append({"role": "user", "content": message.content})

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

@cl.action_callback("heartbeat")
async def heartbeat():
    """Handle heartbeat action to maintain activity status.
    
    :return: Status string indicating active state
    :rtype: str
    """
    update_activity()
    return "Active"