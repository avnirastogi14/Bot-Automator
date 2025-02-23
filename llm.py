from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline

# Load the classification model (DistilBERT for this example)
tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased-finetuned-sst-2-english")
model = AutoModelForSequenceClassification.from_pretrained("distilbert-base-uncased-finetuned-sst-2-english")
intent_recognition_pipeline = pipeline("text-classification", model=model, tokenizer=tokenizer)

#command mapping with descriptions
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

# Helper function to get the best matching command
def get_best_command(user_input):
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
