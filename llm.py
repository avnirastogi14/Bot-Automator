import discord
from discord.ext import commands
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import nest_asyncio
import os
import asyncio

# Load the LLM for intent recognition
tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-3.2-1B")
model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-3.2-1B")
intent_recognition_pipeline = pipeline("text-classification", model=model, tokenizer=tokenizer)

HF_TOKEN = "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"

# Comprehensive command mapping with synonyms
command_mapping = {
    "show stats": ["/about", "bot stats", "server stats", "show bot info"],
    "disable attachment spam": ["/attachmentspam disable", "block attachments", "no file spam"],
    "list autofeeds": ["/autofeeds list", "show autofeeds", "display autofeeds"],
    "add autoresponse": ["/autoresponse create trigger response", "new autoresponse", "create autoresponse"],
    "set welcome message": ["/banmessage message", "welcome message", "greeting message"],
    "flip a coin": ["/fun coinflip", "coin toss", "heads or tails"],
    # Add more mappings with multiple synonyms for comprehensive coverage...
}

# Helper function to get the best matching command
def get_best_command(user_input):
    best_match = ""
    highest_similarity = 0.0

    # Iterate over all commands and their synonyms
    for key, commands in command_mapping.items():
        for command in commands:
            prompt = f"User wants to: {user_input}. Command meaning: {command}."
            result = intent_recognition_pipeline(prompt)[0]
            similarity = float(result["score"])

            if similarity > highest_similarity:
                highest_similarity = similarity
                best_match = commands[0]  # Return the primary command

    return best_match

# Discord bot setup
bot = commands.Bot(command_prefix="/")

@bot.event
async def on_ready():
    print(f"Bot is ready and logged in as {bot.user}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    user_input = message.content.lower()
    best_command = get_best_command(user_input)

    if best_command:
        #confirming if the bot and user are executing same prompt / command //
        await message.channel.send(f"Did you mean to run '{best_command}'? Type 'yes' to confirm or 'no' to cancel.")

        def check(msg):
            return msg.author == message.author and msg.content.lower() in ["yes", "no"]

        try:
            confirmation = await bot.wait_for("message", check=check, timeout=30.0)
            if confirmation.content.lower() == "yes":
                await message.channel.send(f"Executing '{best_command}'...")
            else:
                await message.channel.send("Command canceled.")
        except asyncio.TimeoutError:
            await message.channel.send("No response received. Command canceled.")
    else:
        await message.channel.send("Sorry, I couldn't understand your request. Please try again.")

# bot exec //
nest_asyncio.apply()
bot.run(os.getenv("CJn7FKYBJsouTTQR0fDhSREJO8TALa"))