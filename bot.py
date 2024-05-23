import discord
from discord.ext import commands, tasks
from discord import Embed
from github import Github
import os

# Initialize the bot with a command prefix
bot = commands.Bot(command_prefix="!")

# Dictionary to store the channel ID for GitHub updates
github_update_channel_id = None

# Dictionary to store the latest commit SHA for each repository
latest_commit_shas = {}

# GitHub personal access token
GITHUB_TOKEN = os.environ['GITHUB_TOKEN']
github = Github(GITHUB_TOKEN)

# Bot token
DISCORD_TOKEN = os.environ['DISCORD_BOT_TOKEN']

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    check_github_updates.start()

# Command to set the channel for GitHub updates
@bot.command()
async def setup_github_updates(ctx, channel: discord.TextChannel):
    global github_update_channel_id
    github_update_channel_id = channel.id
    await ctx.send(f'GitHub updates will be posted in {channel.mention}')

# Task to check for GitHub updates
@tasks.loop(minutes=5)
async def check_github_updates():
    if github_update_channel_id is None:
        return

    channel = bot.get_channel(github_update_channel_id)
    if channel is None:
        return

    user = github.get_user()
    for repo in user.get_repos():
        print(f"Checking for changes in repository: {repo.full_name}")
        default_branch = repo.default_branch
        latest_commit = repo.get_commit(sha=default_branch).sha

        # Check for new commits
        if repo.full_name not in latest_commit_shas or latest_commit_shas[repo.full_name] != latest_commit:
            commit = repo.get_commit(sha=latest_commit)
            author = commit.commit.author.name
            url = commit.html_url
            message = commit.commit.message

            embed = Embed(
                title=f"New Commit in {repo.full_name}",
                description=message,
                url=url,
                color=0x00ff00
            )
            embed.set_author(name=author)
            await channel.send(embed=embed)

            latest_commit_shas[repo.full_name] = latest_commit

# Command to get the contents of a file from a repository
@bot.command()
async def get_file(ctx, repo_name: str, file_path: str):
    repo = github.get_repo(repo_name)
    file_content = repo.get_contents(file_path).decoded_content.decode()
    await ctx.send(f'```{file_content}```')

# Run the bot with the token
bot.run(DISCORD_TOKEN)
