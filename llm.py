from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
from difflib import SequenceMatcher

# loads distilbert - this is the AI model that helps understand user text
tokenizer = AutoTokenizer.from_pretrained("MODEL NAME")
model = AutoModelForSequenceClassification.from_pretrained("MODEL NAME")
intent_recognition_pipeline = pipeline("text-classification", model=model, tokenizer=tokenizer)

# In-memory data store for roles
role_data_store = {}

# Discord slash commands from the bot
DISCORD_COMMANDS = {
    "addroledata": {
        "name": "addroledata",
        "description": "Add or update GitHub repository and team information for a role",
        "options": {
            "role_name": {"type": "string", "required": True, "description": "Team Name (The role associated)"},
            "github_repo": {"type": "string", "required": False, "description": "The GitHub repository URL or name"},
            "github_usernames": {"type": "string", "required": False, "description": "Comma-separated list of GitHub usernames"},
            "status": {"type": "string", "required": False, "description": "Current project status or milestone"}
        }
    },
    "showroledata": {
        "name": "showroledata",
        "description": "Display GitHub repository and team information for a role",
        "options": {
            "role_name": {"type": "string", "required": True, "description": "The name of the role or team"}
        }
    },
    "setstatus": {
        "name": "setstatus",
        "description": "Update the project status or milestone for a team",
        "options": {
            "role_name": {"type": "string", "required": True, "description": "The name of the role or team"},
            "status": {"type": "string", "required": True, "description": "Current project status or milestone"}
        }
    }
}

# Enhanced command mapping for natural language understanding
command_mapping = {
    "add role data": {
        "commands": [
            "add role data",
            "update role info",
            "set team information",
            "add team details",
            "link github repo",
            "connect repository",
            "assign github users",
            "update team repository",
            "set project repository",
            "add github members",
        ],
        "description": "Add or update GitHub repository and team information for a role",
        "keywords": [
            "add", "role", "data", "team", "information", "update", "github", "repo", "moderator", "leader",
            "repository", "link", "connect", "assign", "members", "contributors",
            "developers", "username", "project", "url", "connection"
        ],
        "context": "Managing GitHub repositories and team members, including linking repositories and assigning contributors.",
        "discord_command": "addroledata"
    },
    "show role data": {
        "commands": [
            "show role data",
            "display role info",
            "view team details",
            "get role information",
            "check github repo",
            "list team members",
            "show repository info",
            "view github details",
            "display project status",
            "check team progress"
        ],
        "description": "Display GitHub repository and team information for a role",
        "keywords": [
            "show", "display", "view", "get", "role", "team", "data", "info",
            "github", "repository", "members", "list", "check", "progress",
            "contributors", "status", "details", "repository"
        ],
        "context": "Retrieving information about team repositories, members, and project status.",
        "discord_command": "showroledata"
    },
    "set status": {
        "commands": [
            "set status",
            "update status",
            "change team status",
            "modify role status",
            "update project progress",
            "set milestone status",
            "update sprint status",
            "mark project phase",
            "set development stage",
            "update project milestone"
        ],
        "description": "Update the project status or milestone for a team",
        "keywords": [
            "set", "status", "update", "change", "project", "repository", "progress",
            "milestone", "phase", "stage", "sprint", "development", "completion",
            "progress", "state", "tracking"
        ],
        "context": "Managing project progress, milestones, and development stages for GitHub repositories.",
        "discord_command": "setstatus"
    }
}

def calculate_string_similarity(str1, str2):
    """Calculate string similarity using SequenceMatcher"""
    return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()

def calculate_semantic_similarity(text1, text2, pipeline):
    """Calculate semantic similarity using the transformer model"""
    context_prompt = f"Compare these two tasks: 1) {text1} 2) {text2}. Are they related to the same GitHub or project management operation?"
    result = pipeline(context_prompt)[0]
    return float(result["score"])

def extract_command_args(user_input, command_name):
    """Extract arguments from user input based on command requirements."""
    args = {}
    command = DISCORD_COMMANDS.get(command_name, {})
    words = user_input.split()  # Case-sensitive handling removed

    # Extract role name (general roles + teams/groups)
    role_keywords = ["role", "team", "project", "group", "leader"]
    detected_role = None
    for keyword in role_keywords:
        if keyword in words:
            idx = words.index(keyword)
            if idx + 1 < len(words):
                detected_role = words[idx + 1]
                args["role_name"] = detected_role
                break

    # If role_name is missing, prompt the user
    if "role_name" not in args or not args["role_name"].strip():
        args["role_name"] = input("Please enter the role/team name: ").strip()

    # Extract GitHub repo (more robust URL detection)
    repo_indicators = ["github", "repo", "repository", "project"]
    detected_repo = None
    for indicator in repo_indicators:
        if indicator in words:
            idx = words.index(indicator)
            if idx + 1 < len(words):
                potential_repo = words[idx + 1]
                if "github.com" in potential_repo or "/" in potential_repo:
                    detected_repo = potential_repo
                    args["github_repo"] = detected_repo
                    break

    # Extract status (supports multi-word statuses)
    status_keywords = ["status", "state", "progress", "milestone", "phase"]
    detected_status = []
    for keyword in status_keywords:
        if keyword in words:
            idx = words.index(keyword)
            current_idx = idx + 1
            while current_idx < len(words) and words[current_idx] not in repo_indicators + role_keywords:
                detected_status.append(words[current_idx])
                current_idx += 1
            if detected_status:
                args["status"] = " ".join(detected_status)
                break

    # Extract GitHub usernames (handles multiple names correctly)
    username_indicators = ["users", "usernames", "members", "contributors", "developers"]
    detected_users = []
    for indicator in username_indicators:
        if indicator in words:
            idx = words.index(indicator)
            current_idx = idx + 1
            while current_idx < len(words) and words[current_idx] not in repo_indicators + role_keywords + status_keywords:
                detected_users.append(words[current_idx])
                current_idx += 1
            if detected_users:
                args["github_usernames"] = ",".join(detected_users)
                break

    return args

def execute_discord_command(command_name, args):
    """Execute the Discord command with extracted arguments"""
    global role_data_store

    if command_name == "addroledata":
        role_name = args.get("role_name")
        if not role_name:
            print("Role name is required.")
            return
        if role_name not in role_data_store:
            role_data_store[role_name] = {}
        if "github_repo" in args:
            role_data_store[role_name]["github_repo"] = args["github_repo"]
        if "github_usernames" in args:
            role_data_store[role_name]["github_usernames"] = args["github_usernames"].split(",")
        print(f"Role data for '{role_name}' has been updated.")

    elif command_name == "showroledata":
        role_name = args.get("role_name")
        if not role_name:
            print("Role name is required.")
            return
        role_info = role_data_store.get(role_name)
        if role_info:
            print(f"Data for role '{role_name}':")
            print(f"  GitHub Repo: {role_info.get('github_repo', 'N/A')}")
            print(f"  GitHub Usernames: {', '.join(role_info.get('github_usernames', []))}")
        else:
            print(f"No data found for role '{role_name}'.")

    elif command_name == "setstatus":
        role_name = args.get("role_name")
        if not role_name:
            print("Role name is required.")
            return
        status = args.get("status")
        if not status:
            print("Status is required.")
            return
        if role_name not in role_data_store:
            role_data_store[role_name] = {}
        role_data_store[role_name]["status"] = status
        print(f"Status for role '{role_name}' has been updated to '{status}'.")

def get_best_command(user_input):
    """Get the best matching command using enhanced matching logic"""
    command_scores = []
    user_words = set(user_input.lower().split())

    for command_key, command_data in command_mapping.items():
        keywords = set(command_data["keywords"])
        keyword_matches = len(keywords.intersection(user_words))
        keyword_score = keyword_matches / len(keywords) if keywords else 0
        context_score = calculate_semantic_similarity(user_input, command_data["context"], intent_recognition_pipeline)
        command_similarities = [
            (0.3 * calculate_string_similarity(user_input, cmd)) + (0.7 * calculate_semantic_similarity(user_input, cmd, intent_recognition_pipeline))
            for cmd in command_data["commands"]
        ]
        command_score = max(command_similarities)
        final_score = (0.4 * keyword_score) + (0.3 * context_score) + (0.3 * command_score)
        command_scores.append({
            'command': command_key,
            'score': final_score,
            'description': command_data["description"],
            'discord_command': command_data["discord_command"]
        })
    command_scores.sort(key=lambda x: x['score'], reverse=True)
    return command_scores[0] if command_scores and command_scores[0]['score'] > 0.4 else None

def simulate_user_input():
    """Simulate user input and command matching with Discord command execution"""
    print("\nWelcome to the Discord Bot Command Interface!")
    print("Type 'exit' to quit the program")
    print("Type 'help' to see available commands")

    while True:
        print("\nEnter your command (in plain English): ")
        user_input = input().strip()
        if user_input.lower() == 'exit':
            print("Goodbye!")
            break
        if user_input.lower() == 'help':
            print("\nAvailable commands:")
            for cmd, data in command_mapping.items():
                print(f"- {cmd}: {data['description']}")
            continue
        if not user_input:
            print("Please enter a command.")
            continue
        best_match = get_best_command(user_input)
        if best_match:
            discord_command = best_match['discord_command']
            print(f"\nMatched Discord command: /{discord_command}")
            print(f"Description: {best_match['description']}")
            args = extract_command_args(user_input, discord_command)
            print("\nExtracted arguments:")
            for arg, value in args.items():
                print(f"  {arg}: {value}")
            print("\nType 'yes' to confirm or anything else to cancel.")
            confirmation = input().strip().lower()
            if confirmation == "yes":
                execute_discord_command(discord_command, args)
                print("Command executed successfully!")
            else:
                print("Command canceled.")
        else:
            print("\nSorry, I couldn't understand your request.")
            print("Type 'help' to see available commands")

if __name__ == "__main__":
    simulate_user_input()
