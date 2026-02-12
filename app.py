import chainlit as cl
import json
import time
import logging
from pathlib import Path
import ollama
from transformers import pipeline

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Emotion pipeline with error handling
try:
    emotion_pipeline = pipeline(
        "text-classification",
        model="bhadresh-savani/distilbert-base-uncased-emotion",
        return_all_scores=False
    )
    logger.info("Emotion pipeline loaded successfully")
except Exception as e:
    logger.error(f"Failed to load emotion pipeline: {e}")
    emotion_pipeline = None

# Load characters dynamically with validation
CHARACTERS = {}
char_dir = Path("characters")
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
                prompt_path = Path("characters/system_prompt") / char_data["system_prompt"]
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

# Activity tracking with error handling
def update_activity():
    try:
        Path("/tmp/last_activity").write_text(str(int(time.time())))
    except Exception as e:
        logger.error(f"Failed to update activity timestamp: {e}")

update_activity()

@cl.set_chat_profiles
async def chat_profiles():
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
        model_list = ollama.list()
        model_names = []
        for m in model_list.get("models", []):
            model_names.append(m.get("name") or m.get("model", "unknown"))
        
        if model_names:
            # Use first available model as default
            default_model = model_names[0]
            logger.info(f"Found {len(model_names)} Ollama models, using {default_model} as default")
        else:
            logger.warning("No Ollama models found")
            model_names = ["No models available"]
            default_model = None
    except Exception as e:
        logger.error(f"Failed to fetch Ollama models: {e}")
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
    pass

@cl.on_message
async def main(message: cl.Message):
    update_activity()

    char = cl.user_session.get("char")
    if not char:
        await cl.Message(content="⚠️ No character selected. Please restart the chat.").send()
        return

    # Check if models are available
    model_available = cl.user_session.get("model_available", False)
    if not model_available:
        author_label = char.get("nickname", char["name"].split(" ", 1)[0] if " " in char["name"] else char["name"])
        await cl.Message(content="⚠️ No model loaded. Please check Ollama configuration.", author=author_label).send()
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
        logger.info(f"Calling Ollama with model: {selected_model}")
        stream = ollama.chat(
            model=selected_model,
            messages=history,
            stream=True,
            options={"num_gpu": 999, "keep_alive": 0}
        )
        for chunk in stream:
            if chunk.get("message", {}).get("content"):
                token = chunk["message"]["content"]
                reply += token
                await msg.stream_token(token)
    except ollama.ResponseError as e:
        logger.error(f"Ollama model error: {e}")
        if "not found" in str(e).lower() or "does not exist" in str(e).lower():
            reply = "⚠️ No model loaded. Please check Ollama configuration."
            await msg.stream_token(reply)
        else:
            await msg.update()
            await cl.Message(content=f"❌ Ollama error: {str(e)}").send()
            return
    except Exception as e:
        logger.error(f"Ollama connection error: {e}")
        reply = "⚠️ No model loaded. Cannot connect to Ollama server."
        await msg.stream_token(reply)

    await msg.update()

    # Emotion detection with error handling
    if reply.strip() and emotion_pipeline:
        try:
            emotion_result = emotion_pipeline(reply)[0]
            await cl.Message(
                content=f"Emotion: {emotion_result['label'].capitalize()} (confidence: {emotion_result['score']:.2f})",
                disable_human_feedback=True
            ).send()
        except Exception as e:
            logger.error(f"Emotion detection error: {e}")

    history.append({"role": "assistant", "content": reply})
    cl.user_session.set("history", history)

@cl.action_callback("heartbeat")
async def heartbeat():
    update_activity()
    return "Active"