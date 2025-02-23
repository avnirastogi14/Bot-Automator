

import discord
from discord.ext import commands
from transformers import AutoTokenizer, AutoModelForCausalLM
import nest_asyncio

# Apply workaround for Jupyter's running event loop
nest_asyncio.apply()

# Discord bot setup
intents = discord.Intents.default()
intents.messages = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Tokens
huggingface_token = ""
discord_token = ""

# Llama 3.2 1B model name from Hugging Face
model_name = "meta/llama-3.2-1b"

# Load LLM
print("Loading Llama 3.2 1B model...")
try:
    tokenizer = AutoTokenizer.from_pretrained(model_name, token=huggingface_token)
    model = AutoModelForCausalLM.from_pretrained(model_name, token=huggingface_token)
    print("LLM model loaded successfully!")
except Exception as e:
    print(f"Error loading the model: {e}")
    exit()

# Function to query the LLM
def query_llm(prompt):
    inputs = tokenizer(prompt, return_tensors="pt")
    outputs = model.generate(**inputs, max_length=100)
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return response

# Discord bot events
@bot.event
async def on_ready():
    print(f"Bot is ready. Logged in as {bot.user}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    user_query = message.content
    print(f"Received message: {user_query}")

    llm_response = query_llm(user_query)
    await message.channel.send(f"LLM says: {llm_response}")

# Start the bot
bot.run(discord_token)
