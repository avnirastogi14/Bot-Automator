import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

TOKEN = os.getenv("TOKEN")
CLIENT_ID = os.getenv("CLIENT_ID")
GUILD_ID = os.getenv("GUILD_ID")

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/codejam")
if not MONGODB_URI:
    print("MongoDB connection string is undefined. Check your environment variables.")
    exit(1)

mongo_client = MongoClient(MONGODB_URI)
db = mongo_client["codejam"]
roles_collection = db["roles"]  
intents = discord.Intents.default()
intents.members = True  

bot = commands.Bot(command_prefix="!", intents=intents)

def get_role_by_name(guild: discord.Guild, role_name: str) -> discord.Role:
    return discord.utils.get(guild.roles, name=role_name)

@bot.tree.command(
    name="addroledata",
    description="Add additional data for a specific role",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(
    role_name="Team Name (The role associated)",
    github_repo="The GitHub repository associated with the role",
    github_usernames="Comma-separated list of GitHub usernames",
    status="Status of the team",
)
async def addroledata(
    interaction: discord.Interaction,
    role_name: str,
    github_repo: str = None,
    github_usernames: str = None,
    status: str = None
):
    """Adds or updates data for a specific role in the MongoDB."""
    await interaction.response.defer(thinking=True) 
    guild = interaction.guild
    if not guild:
        await interaction.followup.send("Could not find the guild context.")
        return

    role = get_role_by_name(guild, role_name)
    if not role:
        await interaction.followup.send(f'The role "{role_name}" does not exist in this guild.')
        return

    member = interaction.user
    has_admin = member.guild_permissions.administrator
    has_ct25 = any(r.name == "CT25" for r in member.roles)
    has_target_role = role in member.roles

    if not (has_admin or has_ct25 or has_target_role):
        await interaction.followup.send(
            "You do not have permission to use this command. "
            "You must be an admin, have the 'CT25' role, or have the role you're updating."
        )
        return

    github_usernames_list = []
    if github_usernames:
        github_usernames_list = [u.strip() for u in github_usernames.split(",") if u.strip()]

    existing_data = roles_collection.find_one({"name": role_name})
    if existing_data:
        update_data = {}
        if github_repo is not None:
            update_data["githubRepo"] = github_repo
        if github_usernames_list:
            update_data["githubUsernames"] = github_usernames_list
        if status is not None:
            update_data["status"] = status

        if update_data:
            roles_collection.update_one({"name": role_name}, {"$set": update_data})
            await interaction.followup.send(f'Role data for "{role_name}" has been updated.')
        else:
            await interaction.followup.send(f"No updates were provided for \"{role_name}\".")
    else:
        role_document = {
            "name": role_name,
            "githubRepo": github_repo if github_repo else "",
            "githubUsernames": github_usernames_list,
            "status": status if status else "",
            "marks": []  
        }
        roles_collection.insert_one(role_document)
        await interaction.followup.send(f'Role data for "{role_name}" has been added.')


@bot.tree.command(
    name="showroledata",
    description="Show additional data for a specific role",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(role_name="The name of the role")
async def showroledata(interaction: discord.Interaction, role_name: str):
    """Shows the stored data for a given role."""
    await interaction.response.defer(thinking=True)

    guild = interaction.guild
    if not guild:
        await interaction.followup.send("Could not find the guild context.")
        return

    member = interaction.user
    has_admin = member.guild_permissions.administrator
    has_ct25 = any(r.name == "CT25" for r in member.roles)

    role = get_role_by_name(guild, role_name)
    if not role:
        await interaction.followup.send(f'Role "{role_name}" not found in this guild.')
        return

    has_target_role = role in member.roles

    if not (has_admin or has_ct25 or has_target_role):
        await interaction.followup.send(
            "You do not have permission to use this command or you do not have the specified role."
        )
        return

    role_data = roles_collection.find_one({"name": role_name})
    if not role_data:
        await interaction.followup.send(f'No data found for role "{role_name}".')
        return

    members_with_role = [m for m in guild.members if role in m.roles]
    member_names = ", ".join(m.display_name for m in members_with_role) or "No members with this role."

    github_repo_value = role_data.get("githubRepo", "")
    github_repo_link = f"https://github.com/{github_repo_value}" if github_repo_value else None
    github_usernames_list = role_data.get("githubUsernames", [])
    if github_usernames_list:
        # Format each username as a link
        formatted_usernames = ", ".join(
            f"[{uname}](https://github.com/{uname})" for uname in github_usernames_list
        )
    else:
        formatted_usernames = "No usernames available"

    status_value = role_data.get("status", "") or "No status available"

    embed = discord.Embed(
        title=f'Role Data for "{role_name}"',
        description=f'Here are the details for the role "{role_name}"',
        color=0xFF6A00
    )

    if github_repo_value:
        embed.add_field(
            name="GitHub Repository:",
            value=f"[{github_repo_value}]({github_repo_link})",
            inline=False
        )
    else:
        embed.add_field(
            name="GitHub Repository:",
            value="Not specified",
            inline=False
        )

    embed.add_field(
        name="GitHub Usernames:",
        value=formatted_usernames,
        inline=False
    )
    embed.add_field(
        name="Status:",
        value=status_value,
        inline=False
    )
    embed.add_field(
        name="Members with this Role:",
        value=member_names,
        inline=False
    )

    await interaction.followup.send(embed=embed)


@bot.tree.command(
    name="setstatus",
    description="Set the status for a specific role",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(
    role_name="The name of the role",
    status="New status for the role"
)
async def setstatus(interaction: discord.Interaction, role_name: str, status: str):
    """Updates the 'status' field for the given role in MongoDB."""
    await interaction.response.defer(thinking=True)

    guild = interaction.guild
    if not guild:
        await interaction.followup.send("Could not find the guild context.")
        return

    role = get_role_by_name(guild, role_name)
    if not role:
        await interaction.followup.send(f'The role "{role_name}" does not exist in this guild.')
        return

    member = interaction.user
    has_admin = member.guild_permissions.administrator
    has_ct25 = any(r.name == "CT25" for r in member.roles)
    has_target_role = role in member.roles

    if not (has_admin or has_ct25 or has_target_role):
        await interaction.followup.send(
            "You do not have permission to use this command, and you do not have the specified role."
        )
        return

    role_data = roles_collection.find_one({"name": role_name})
    if not role_data:
        await interaction.followup.send(
            f'No data found for role "{role_name}". Please use /addroledata first.'
        )
        return

    roles_collection.update_one({"name": role_name}, {"$set": {"status": status}})

    await interaction.followup.send(f'Status for role "{role_name}" has been updated to: "{status}".')


@bot.tree.command(
    name="setmarks",
    description="Set marks (up to 3) for a specific role",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(
    role_name="The name of the role",
    marks="Comma-separated list of up to 3 marks"
)
async def setmarks(interaction: discord.Interaction, role_name: str, marks: str):
    """Sets or updates the 'marks' field for the given role."""
    await interaction.response.defer(thinking=True)

    guild = interaction.guild
    if not guild:
        await interaction.followup.send("Could not find the guild context.")
        return

    member = interaction.user
    has_admin = member.guild_permissions.administrator
    has_ct25 = any(r.name == "CT25" for r in member.roles)

    if not (has_admin or has_ct25):
        await interaction.followup.send("You do not have permission to use this command.")
        return

    role = get_role_by_name(guild, role_name)
    if not role:
        await interaction.followup.send(f'The role "{role_name}" does not exist in this guild.')
        return

    parsed_marks = [m.strip() for m in marks.split(",") if m.strip()]
    int_marks = []
    for mark in parsed_marks:
        try:
            int_marks.append(int(mark))
        except ValueError:
            int_marks.append(None)

    while len(int_marks) < 3:
        int_marks.append(None)
    final_marks = int_marks[:3]

    role_data = roles_collection.find_one({"name": role_name})
    if not role_data:
        await interaction.followup.send(
            f'No data found for role "{role_name}". Please add role data first with /addroledata.'
        )
        return

    roles_collection.update_one({"name": role_name}, {"$set": {"marks": final_marks}})
    display_marks = ", ".join(str(m) if m is not None else "None" for m in final_marks)
    await interaction.followup.send(f'Marks for role "{role_name}" have been updated to: {display_marks}.')


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}!")
    try:
        guild_obj = discord.Object(id=GUILD_ID)
        synced = await bot.tree.sync(guild=guild_obj)
        print(f"Successfully synced {len(synced)} slash commands to guild {GUILD_ID}.")
    except Exception as e:
        print("Error syncing slash commands:", e)

    guild = bot.get_guild(int(GUILD_ID)) if GUILD_ID else None
    if guild:
        await guild.chunk() 
        print(f"Fetched {guild.member_count} members from the guild.")

@bot.event
async def on_member_join(member: discord.Member):
    print(f"New member joined: {member.name}")



if __name__ == "__main__":
    try:
        print("Connecting to MongoDB...")
        # Test the MongoDB connection
        mongo_client.admin.command("ping")
        print("MongoDB connected successfully.")
    except Exception as e:
        print("MongoDB connection error:", e)
        exit(1)

    # Finally, run the bot
    bot.run(TOKEN)