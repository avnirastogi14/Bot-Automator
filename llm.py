from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
<<<<<<< HEAD
from difflib import SequenceMatcher
import numpy as np

# loads distilbert - this is the AI model that helps understand user text
=======

# Load the classification model (DistilBERT for this example)
>>>>>>> 6f99cb7859159118d8813420ea3c10616ad0d738
tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased-finetuned-sst-2-english")
model = AutoModelForSequenceClassification.from_pretrained("distilbert-base-uncased-finetuned-sst-2-english")
intent_recognition_pipeline = pipeline("text-classification", model=model, tokenizer=tokenizer)

<<<<<<< HEAD
# all the bot commands and their variations
# last item in each list is the description
=======
#command mapping with descriptions
>>>>>>> 6f99cb7859159118d8813420ea3c10616ad0d738
command_mapping = {
    "show stats": ["/about", "bot stats", "server stats", "show bot info", "Shows bot statistics"],
    "disable attachment spam": ["/attachmentspam disable", "block attachments", "no file spam", "Disables attachment spam"],
    "list autofeeds": ["/autofeeds list", "show autofeeds", "display autofeeds", "Lists all autofeeds"],
    "add autoresponse": ["/autoresponse create trigger response", "new autoresponse", "create autoresponse", "Adds an autoresponse"],
    "set welcome message": ["/banmessage message", "welcome message", "greeting message", "Sets a welcome message"],
    "flip a coin": ["/fun coinflip", "coin toss", "heads or tails", "Flips a coin"],
    "whitelist roles or channels": ["/automod whitelist choice roles_or_channels", "automod whitelist", "add to whitelist", "Manages the automod whitelist"],
    "remove autoresponse": ["/autoresponse remove trigger", "remove trigger", "delete autoresponse", "Removes an autoresponse trigger"],
}

# basic string matching
def calculate_string_similarity(str1, str2):
    """Calculate string similarity using SequenceMatcher"""
    return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()

def calculate_semantic_similarity(text1, text2, pipeline):
    """Calculate semantic similarity using the transformer model"""
    prompt = f"Compare if these are similar: '{text1}' and '{text2}'"
    result = pipeline(prompt)[0]
    return float(result["score"])

# matching user input to the right command
# uses both exact matching and AI to figure out what command they probably want
def get_best_command(user_input):
<<<<<<< HEAD
    """Get the best matching command using multiple similarity metrics"""
    command_scores = []

    for command_key, command_list in command_mapping.items():
        aliases = command_list[:-1]
        description = command_list[-1]

        alias_scores = []
        for alias in aliases:
            # tried different weights, 30-70 split works best
            string_sim = calculate_string_similarity(user_input, alias)
            semantic_sim = calculate_semantic_similarity(user_input, alias, intent_recognition_pipeline)
            combined_score = (0.3 * string_sim) + (0.7 * semantic_sim)
            alias_scores.append(combined_score)

        best_alias_score = max(alias_scores)
        command_scores.append({
            'command': command_key,
            'score': best_alias_score,
            'description': description
        })

    command_scores.sort(key=lambda x: x['score'], reverse=True)

    # only return matches above 0.5 score to avoid weird suggestions
    if command_scores and command_scores[0]['score'] > 0.5:
        return command_scores[0]['command'], command_scores[0]['description']
    return "", ""

def simulate_user_input():
    """Simulate user input and command matching with continuous operation"""
    print("\nWelcome to the Command Interface!")
    print("Type 'exit' to quit the program")
    print("Type 'help' to see available commands")

    while True:
        print("\nEnter your command (in plain English): ")
        user_input = input().strip().lower()

        # Handle special commands
        if user_input == 'exit':
            print("Goodbye!")
            break

        if user_input == 'help':
            print("\nAvailable commands:")
            for cmd, details in command_mapping.items():
                print(f"- {cmd}: {details[-1]}")
            continue

        if not user_input:
            print("Please enter a command.")
            continue

        # Find the best matching command
        best_command, description = get_best_command(user_input)

        if best_command:
            print(f"\nDid you mean to run '{best_command}'?")
            print(f"Description: {description}")
            print("Type 'yes' to confirm or anything else to cancel.")

            confirmation = input().strip().lower()
            if confirmation == "yes":
                print(f"\nExecuting '{best_command}'... (simulated)")
                # Here you would actually execute the command
                print("Command executed successfully!")
            else:
                print("Command canceled.")
        else:
            print("\nSorry, I couldn't understand your request.")
            print("Type 'help' to see available commands")

if __name__ == "__main__":
    simulate_user_input()
=======
    best_match = ""
    highest_similarity = 0.0
    description = ""

    # Iterate over all commands and their synonyms
    for key, commands in command_mapping.items():
        for command in commands[:-1]:
            prompt = f"User wants to: {user_input}. Command meaning: {command}."
            result = intent_recognition_pipeline(prompt)[0]
            similarity = float(result["score"])

            if similarity > highest_similarity:
                highest_similarity = similarity
                best_match = commands[0]  # Return the primary command
                description = commands[-1]  # The last item is the description

    return best_match, description

# Simulate user input for testing
def simulate_user_input():
    while True:
        print("Enter your command (in plain English): ")
        user_input = input().strip().lower()

        # Find the best matching command
        best_command, description = get_best_command(user_input)

        if best_command:
            print(f"Did you mean to run '{best_command}'? ({description}) Type 'yes' to confirm or 'no' to cancel.")

            confirmation = input().strip().lower()
            if confirmation == "yes":
                print(f"Executing '{best_command}'... (simulated)")
                break
            else:
                print("Command canceled.")
                break
        else:
            print("Sorry, I couldn't understand your request. Please try again.")
            retry = input("Do you want to try again? (yes/no): ").strip().lower()
            if retry != "yes":
                break

# Run the simulation
simulate_user_input()
>>>>>>> 6f99cb7859159118d8813420ea3c10616ad0d738
