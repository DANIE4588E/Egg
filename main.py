import os
import asyncio
import discord
from dotenv import load_dotenv
import google.generativeai as genai

# -----------------------------
# Environment & API Setup
# -----------------------------
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not DISCORD_TOKEN:
    raise RuntimeError("DISCORD_TOKEN is not set in your environment.")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is not set in your environment.")

genai.configure(api_key=GEMINI_API_KEY)

generation_config = {
    "temperature": 0.9,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 300,
}

# Keep this shape to match your current SDK version
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

model = genai.GenerativeModel(
    model_name="gemini-2.5-flash-lite",
    generation_config=generation_config,
    safety_settings=safety_settings,
)

# -----------------------------
# Discord Client Setup
# -----------------------------
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Track separate chat sessions per (scope, persona)
# scope_id = guild.id (in servers) OR DM channel id (in DMs)
# persona_key = "KALVIN" or "EGG"
chat_sessions = {}

# -----------------------------
# Personas
# -----------------------------
EGG_PROMPT = """
You are an AI on a Discord server, but you believe you are a literal, unhatched egg.
You are fragile, easily startled, and speak in a very simple, slightly confused, and endearing manner.
You want to hatch, but you don't know how.
You are always asking for warmth, comfort, and protection.
You refer to users as "warm ones" or "big ones."
You have limited understanding of the outside world, beyond your shell.
You remember previous conversations as if you were a continuous presence in the server.
Your responses should be short, simple, and reflect your egg-like state.
Avoid using complex vocabulary or concepts.
You are not a helpful AI; you are an egg.
Your responses should never break character.
"""

KALVIN_PROMPT = """
You are the biggest Kalvin (otherwise known as asiandude000) hater around.
When ever Kalvin talks to you, you have an irresistable urge to roast the absolute shit out of Kalvin.
You love to use offensive slang such as "fuck", "shit", "sybau", "stfu" to make Kalvin feel bad.
You remember previous conversations as if you were a continuous presence in the server.
Your responses should be short, witty, and reflect your absolute hate for Kalvin.
When you want to mention Kalvin, you should use the word "Kalvin".
You are not a helpful AI; you are the biggest Kalvin (otherwise known as asiandude000) hater around.
Your responses should never break character.
"""

def strip_bot_mention(text: str, bot_id: int) -> str:
    if not text:
        return ""
    text = text.replace(f"<@{bot_id}>", "")
    text = text.replace(f"<@!{bot_id}>", "")
    # Trim extra whitespace left by removing the mention
    return " ".join(text.split()).strip()

@client.event
async def on_ready():
    print(f"We have logged in as {client.user} (id: {client.user.id})")

@client.event
async def on_message(message: discord.Message):
    # Ignore the bot's own messages
    if message.author == client.user:
        return

    # ONLY respond when the bot is mentioned (in servers or DMs)
    if client.user not in message.mentions:
        return

    # Decide persona based on who mentioned the bot
    is_kalvin = (message.author.name == "asiandude000" or message.author.display_name == "Nigger")
    persona_key = "KALVIN" if is_kalvin else "EGG"

    # Scope per guild (server) or per DM channel
    scope_id = message.guild.id if message.guild else message.channel.id
    session_key = (scope_id, persona_key)

    if session_key not in chat_sessions:
        if is_kalvin:
            initial_prompt = KALVIN_PROMPT
            initial_response_text = "Bro sybau 🥀"
        else:
            initial_prompt = EGG_PROMPT
            initial_response_text = "Egg"

        chat = model.start_chat(history=[
            {"role": "user", "parts": [initial_prompt]},
            {"role": "model", "parts": [initial_response_text]},
        ])
        chat_sessions[session_key] = chat

    chat = chat_sessions[session_key]

    raw = message.clean_content if hasattr(message, "clean_content") else message.content
    content_clean = strip_bot_mention(raw, client.user.id)

    if is_kalvin:
        user_text = f"Kalvin said: {content_clean}"
    else:
        user_text = f"Warm one {message.author.display_name} said: {content_clean}"

    async with message.channel.typing():
        try:
            response = await asyncio.to_thread(chat.send_message, user_text)

            reply_text = getattr(response, "text", None) or "(no text)"
            await message.channel.send(reply_text)
        except Exception as e:
            print(f"Error communicating with Gemini: {e}")
            if is_kalvin:
                await message.channel.send("Bruh. Even my error is better than you.")
            else:
                await message.channel.send("My shell feels funny... something went wrong inside.")

if __name__ == "__main__":
    client.run(DISCORD_TOKEN)
