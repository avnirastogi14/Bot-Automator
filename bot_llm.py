import asyncio
import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
from pymongo import MongoClient
import nest_asyncio
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
import shlex  # Import shlex for argument parsing

# Load environment variables
load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
TOKEN = os.getenv("TOKEN")
CLIENT_ID = int(os.getenv("CLIENT_ID"))
GUILD_ID = int(os.getenv("GUILD_ID"))

# MongoDB Connection Check
if not MONGODB_URI:
    print("MongoDB connection string is undefined. Check your environment variables.")
    exit(1)

mongo_client = MongoClient(MONGODB_URI)
try:
    mongo_client.admin.command("ping")
    print("MongoDB connected successfully.")
except Exception as e:
    print("MongoDB connection error:", e)
    exit(1)

db = mongo_client["codejam"]
roles_collection = db["roles"]

# Intents
intents = discord.Intents.all()
intents.members = True

# Bot Initialization
bot = commands.Bot(command_prefix="/", intents=intents)

# Load Transformer Model
tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased-finetuned-sst-2-english")
model = AutoModelForSequenceClassification.from_pretrained("distilbert-base-uncased-finetuned-sst-2-english")
intent_recognition_pipeline = pipeline("text-classification", model=model, tokenizer=tokenizer)

# Slash Commands


# Command Mapping (with functions)
command_mapping = {
    "add role data": ["addroledata", "Adds role information.", None],
    "show role data": ["showroledata", "Displays role information.", None],
    "set role status": ["setstatus", "Updates the status of a role.", None],
}

# String Similarity
def string_similarity(a, b):
    from difflib import SequenceMatcher
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

# Semantic Similarity
def calculate_semantic_similarity(text1, text2, pipeline):
    prompt = f"Compare if these are similar: '{text1}' and '{text2}'"
    result = pipeline(prompt)[0]
    return float(result["score"])

# Best Command Matching
def get_best_command(user_input):
    command_scores = []

    for command_key, command_list in command_mapping.items():
        aliases = command_list[:1]
        description = command_list[1]

        alias_scores = []
        for alias in aliases:
            string_sim = string_similarity(user_input, alias)
            semantic_sim = calculate_semantic_similarity(user_input, alias, intent_recognition_pipeline)
            combined_score = (0.3 * string_sim) + (0.7 * semantic_sim)
            alias_scores.append(combined_score)

        best_alias_score = max(alias_scores) if alias_scores else 0
        command_scores.append({
            'command': command_key,
            'score': best_alias_score,
            'description': description
        })

    command_scores.sort(key=lambda x: x['score'], reverse=True)

    if command_scores and command_scores[0]['score'] > 0.5:
        return command_scores[0]['command'], command_scores[0]['description']
    return "", ""


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if bot.user.mentioned_in(message):
        user_input = message.content.lower().replace(f"<@!{bot.user.id}>", "").strip()

        if not user_input:
            await message.channel.send("Please provide text after mentioning me.")
            return

        best_command, description = get_best_command(user_input)

        if best_command:
            await message.channel.send(f"Did you mean: !{command_mapping[best_command][0]}?\nDescription: {description}")
            await message.channel.send("Type 'yes' to confirm.")

            def check(m):
                return m.author == message.author and m.channel == message.channel and m.content.lower() == 'yes'

            try:
                confirmation_message = await bot.wait_for('message', check=check, timeout=15.0)
            except asyncio.TimeoutError:
                await message.channel.send("Confirmation timed out.")
                return

            if confirmation_message:

                try:
                    args = shlex.split(user_input)  # Use shlex for argument parsing
                except ValueError:  # If shlex can not split the user input
                    args = user_input.split()[1:]  # Use the old method

                try:
                    # await command_function(message, *args)  # Execute the command
                    await message.channel.send(f"!{command_mapping[best_command][0]} " + ' '.join(args))
                except Exception as e:
                    await message.channel.send(f"Error executing command: {e}")
                    raise e
            else:
                await message.channel.send("Command canceled.")

        else:  # No matching command found; use LLM
            try:
                prompt = f"Process this natural language input:\n{user_input}"
                result = await model.generateContent(prompt)  # Adapt to your LLM API
                geminiResponse = await result.response
                llm_response = geminiResponse.text()

                await message.channel.send(f"LLM Response:\n{llm_response}")

            except Exception as e:
                print(f"Error processing with LLM: {e}")
                await message.channel.send("Error processing your request with the LLM.")

    await bot.process_commands(message)  # VERY IMPORTANT

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}!")
    try:
        guild_obj = discord.Object(id=GUILD_ID)
        synced = await bot.tree.sync(guild=guild_obj)
        print(f"Successfully synced {len(synced)} slash commands to guild {GUILD_ID}.")
    except Exception as e:
        print("Error syncing slash commands:", e)

    guild = bot.get_guild(GUILD_ID)
    if guild:
        await guild.chunk()
        print(f"Fetched {guild.member_count} members from the guild.")

bot.run(TOKEN)
