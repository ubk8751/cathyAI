import chainlit as cl
import json
import time
from pathlib import Path
import ollama
from transformers import pipeline

# Emotion pipeline
emotion_pipeline = pipeline(
    "text-classification",
    model="bhadresh-savani/distilbert-base-uncased-emotion",
    return_all_scores=False
)

# Load characters dynamically
CHARACTERS = {}
for f in Path("characters").glob("*.json"):
    char_data = json.load(open(f))
    # Load system prompt from external file if specified as filename
    if "system_prompt" in char_data and not char_data["system_prompt"].startswith("You"):
        prompt_path = Path("characters/system_prompt") / char_data["system_prompt"]
        if prompt_path.exists():
            char_data["system_prompt"] = prompt_path.read_text().strip()
    CHARACTERS[f.stem] = char_data

# Activity tracking
LAST_ACTIVITY = time.time()
Path("/tmp/last_activity").write_text(str(int(LAST_ACTIVITY)))

@cl.set_chat_profiles
async def chat_profiles():
    profiles = []
    for char_id, char in CHARACTERS.items():
        profiles.append(
            cl.ChatProfile(
                name=char["name"],
                icon=f"/public/avatars/{char['avatar']}",
                markdown_description=char.get("description", ""),
                starters=[cl.Starter(label="Greet me", message=char.get("greeting", "Nyaa~ Hello there! 🐾"))]
            )
        )
    return profiles

@cl.on_chat_start
async def start():
    global LAST_ACTIVITY
    LAST_ACTIVITY = time.time()
    Path("/tmp/last_activity").write_text(str(int(LAST_ACTIVITY)))

    # Get current profile (set by Chainlit)
    current_profile_name = cl.user_session.get("chat_profile")
    char = next((c for c in CHARACTERS.values() if c["name"] == current_profile_name), list(CHARACTERS.values())[0] if CHARACTERS else None)

    if char:
        cl.user_session.set("char", char)
        # System prompt always in history
        cl.user_session.set("history", [{"role": "system", "content": char["system_prompt"]}])

    # Model selection sidebar
    try:
        model_list = ollama.list()
        # Robust key access – Ollama uses "name" for tag
        model_names = []
        for m in model_list.get("models", []):
            model_names.append(m.get("name") or m.get("model", "unknown"))
    except Exception as e:
        print(f"Ollama list error: {e}")
        model_names = ["llama3.1:8b"]

    if model_names:
        await cl.ChatSettings(
            [
                cl.input_widget.Select(
                    id="Model",
                    label="Ollama Model",
                    values=model_names,
                    initial_value=model_names[0] if model_names else "llama3.1:8b"
                )
            ]
        ).send()

@cl.on_settings_update
async def update_settings(settings):
    pass

@cl.on_message
async def main(message: cl.Message):
    global LAST_ACTIVITY
    LAST_ACTIVITY = time.time()
    Path("/tmp/last_activity").write_text(str(int(LAST_ACTIVITY)))

    char = cl.user_session.get("char")
    if not char:
        await cl.Message(content="No character selected!").send()
        return

    settings = cl.user_session.get("settings", {})
    selected_model = settings.get("Model", char.get("model", "llama3.1:8b"))

    history = cl.user_session.get("history", [{"role": "system", "content": char["system_prompt"]}])
    history.append({"role": "user", "content": message.content})

    author_label = char.get("nickname", char["name"].split(" ", 1)[0] if " " in char["name"] else char["name"])

    reply = ""
    msg = cl.Message(content="", author=author_label)
    await msg.send()

    try:
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
    except Exception as e:
        await msg.update()
        await cl.Message(content=f"Ollama error: {str(e)}").send()
        return

    await msg.update()

    if reply.strip():
        emotion_result = emotion_pipeline(reply)[0]
        await cl.Message(
            content=f"Emotion: {emotion_result['label'].capitalize()} (confidence: {emotion_result['score']:.2f}) # TODO: Animate 🐾",
            disable_human_feedback=True
        ).send()

    history.append({"role": "assistant", "content": reply})
    cl.user_session.set("history", history)

@cl.action_callback("heartbeat")
async def heartbeat():
    global LAST_ACTIVITY
    LAST_ACTIVITY = time.time()
    Path("/tmp/last_activity").write_text(str(int(LAST_ACTIVITY)))
    return "Active"