import chainlit as cl
import json
import time
from pathlib import Path
import ollama
from transformers import pipeline

# Your emotion pipeline (unchanged)
emotion_pipeline = pipeline(
    "text-classification",
    model="bhadresh-savani/distilbert-base-uncased-emotion",
    return_all_scores=False
)

# Load characters dynamically (full customizability—add DB later if you want)
CHARACTERS = {}
for f in Path("characters").glob("*.json"):
    char_data = json.load(open(f))
    # Load system prompt from file if it's a filename
    if "system_prompt" in char_data and not char_data["system_prompt"].startswith("You"):
        prompt_path = Path("characters/system_prompt") / char_data["system_prompt"]
        if prompt_path.exists():
            char_data["system_prompt"] = prompt_path.read_text().strip()
    CHARACTERS[f.stem] = char_data

# Track activity for shutdown (custom hook)
LAST_ACTIVITY = time.time()
with open("/tmp/last_activity", "w") as f: f.write(str(LAST_ACTIVITY))

@cl.on_chat_start
async def start():
    global LAST_ACTIVITY
    LAST_ACTIVITY = time.time()

    # Simple character selector (customize to dropdown or multi-select)
    char_id = "catherine"  # Or use cl.AskUserMessage for dynamic choice
    char = CHARACTERS[char_id]
    cl.user_session.set("char", char)
    cl.user_session.set("history", [{"role": "system", "content": char["system_prompt"]}])

    # Set avatar (looks great automatically)
    await cl.Avatar(name=char["name"], path=f"static/{char['avatar']}").send()
    await cl.Message(content=char.get("greeting", "Hello!")).send()

@cl.on_message
async def main(message: cl.Message):
    global LAST_ACTIVITY
    LAST_ACTIVITY = time.time()  # Update for watchdog
    with open("/tmp/last_activity", "w") as f: f.write(str(LAST_ACTIVITY))

    char = cl.user_session.get("char")
    history = cl.user_session.get("history")
    history.append({"role": "user", "content": message.content})

    # Ollama call (your options + unload for energy saving)
    reply = ""
    msg = cl.Message(content="", author=char["name"])
    await msg.send()
    for chunk in ollama.chat(
        model=char["model"],
        messages=history,
        stream=True,
        options={"num_gpu": 999, "keep_alive": 0}  # Custom: max GPU, immediate unload
    ):
        if "message" in chunk:
            token = chunk["message"]["content"]
            reply += token
            await msg.stream_token(token)
    await msg.update()

    # Your emotion detection (customize freely—e.g., add animations via JS injection)
    if reply:
        emotion = emotion_pipeline(reply)[0]
        await cl.Message(
            content=f"Emotion: {emotion['label'].capitalize()} (confidence: {emotion['score']:.2f}) # TODO: Animate 🐾",
            disable_human_feedback=True
        ).send()

    # Update history
    history.append({"role": "assistant", "content": reply})
    cl.user_session.set("history", history)

# Optional: Heartbeat route for advanced watchdog (custom endpoint)
@cl.action_callback("heartbeat")
async def heartbeat():
    global LAST_ACTIVITY
    LAST_ACTIVITY = time.time()
    return "Active"