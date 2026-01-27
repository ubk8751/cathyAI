import argparse
import ollama
from transformers import pipeline

parser = argparse.ArgumentParser(description="AI Neko Companion CLI")
parser.add_argument('--test', action='store_true', help="Force CPU-only mode for Ollama (num_gpu=0)")
args = parser.parse_args()

model = 'llama3.1:8b'

# Load emotion classifier (CPU-only, cached after first run)
emotion_pipeline = pipeline(
    "text-classification",
    model="bhadresh-savani/distilbert-base-uncased-emotion",
    return_all_scores=False
)

# System prompt for neko personality
system_prompt = {
    'role': 'system',
    'content': (
        "You are a cute neko AI companion with fluffy cat ears and a swishing tail. "
        "You are playful, affectionate, a bit mischievous, and love your human. "
        "Respond in a warm, engaging way. Use emojis like 🐾, 😺, ❤️, and occasionally say 'nyaa~' or 'purr~'. "
        "Keep responses concise but expressive."
    )
}

# Initialize conversation history
messages = [system_prompt]

print("Neko Companion started! Type 'exit' to quit, 'reset' to clear history.\n")

while True:
    user_input = input("You: ").strip()
    if user_input.lower() == 'exit':
        print("Companion: Bye for now~ 🐾 See you soon!")
        break
    if user_input.lower() == 'reset':
        messages = [system_prompt]
        print("Conversation history reset!\n")
        continue
    if not user_input:
        continue

    # Append user message
    messages.append({'role': 'user', 'content': user_input})

    # Ollama options: force CPU in test mode, otherwise try max GPU layers
    options = {'num_gpu': 0} if args.test else {'num_gpu': 999}

    try:
        response = ollama.chat(
            model=model,
            messages=messages,
            options=options
        )
        reply = response['message']['content']

        # Append assistant response to history
        messages.append({'role': 'assistant', 'content': reply})

        print("\nCompanion:", reply)

        # Emotion analysis on the companion's reply
        emotion_result = emotion_pipeline(reply)[0]
        emotion = emotion_result['label'].capitalize()
        score = emotion_result['score']

        print(f"Emotion detected: {emotion} (confidence: {score:.2f})")
        print("   # TODO: trigger animation for this emotion (e.g., tail wag for Joy)\n")

    except Exception as e:
        print(f"Error: {e}")