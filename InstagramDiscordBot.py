# Importing libraries and modules
import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
from instagrapi import Client


# Load environment variables for tokens and credentials
# YOU NEED A '.env' FILE TO READ THESE ATTRIBUTES FROM
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
IG_USERNAME = os.getenv("IG_USERNAME")
IG_PASSWORD = os.getenv("IG_PASSWORD")

# Setup of intents. Intents are permissions the bot has on the server
intents = discord.Intents.default()
intents.message_content = True

# Bot setup
bot = commands.Bot(command_prefix="!", intents=intents)

# Initialize Instagrapi client and login
ig_client = Client()
try:
    # OPTIONAL - you can set a proxy here
    ig_client.login(IG_USERNAME, IG_PASSWORD)
    print("Instagram client logged in successfully.")
except Exception as e:
    print(f"Failed to login Instagram client: {e}")

# Bot ready-up event
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"{bot.user} is online and ready!")


# Helper function to create an embed for a Media object
def create_media_embeds(media):
    caption = getattr(media, 'caption_text', None) or '(No caption)'
    base_url = f"https://www.instagram.com/p/{media.code}/"
    embeds = []

    # Handle carousel/albums
    if media.media_type == 8 and hasattr(media, 'resources'):
        for resource in media.resources:
            embed = discord.Embed(description=caption)
            embed.set_image(url=resource.thumbnail_url)
            embed.add_field(name="Instagram", value=base_url, inline=False)
            embeds.append(embed)
        return embeds

    # Single image or video: show thumbnail
    embed = discord.Embed(description=caption)
    embed.set_image(url=media.thumbnail_url)

    if media.media_type == 2 and getattr(media, 'video_url', None):
        # Include video URL as a field since Discord embeds don't autoplay
        embed.add_field(name="Video", value="(Video in Instagram post)", inline=False)

    embed.add_field(name="Instagram", value=base_url, inline=False)
    embeds.append(embed)
    return embeds


# Command: Get the last N posts from a specified Instagram user
@bot.tree.command(name="insta_last", description="Fetch the last N posts from an Instagram user.")
@app_commands.describe(username="Instagram username", amount="Number of posts to fetch")
async def insta_last(interaction: discord.Interaction, username: str, amount: int):
    await interaction.response.defer()

    try:
        user_id = ig_client.user_id_from_username(username)
        medias = ig_client.user_medias(user_id, amount)
    except Exception as e:
        await interaction.followup.send(f"Error fetching posts for {username}: {e}")
        return
    
    if not medias:
        await interaction.followup.send(f"No posts found for user {username}.")
        return
    
    for media in medias:
        embeds = create_media_embeds(media)
        for embed in embeds:
            await interaction.followup.send(embed=embed)


# Command: Search Instagram for posts by keyword and fetch N results
@bot.tree.command(name="insta_search", description="Search Instagram posts by keyword and fetch N results.")
@app_commands.describe(query="Search query (keyword or hashtag)", amount="Number of posts to fetch")
async def insta_search(interaction: discord.Interaction, query: str, amount: int):
    await interaction.response.defer()

    try:
        medias = ig_client.hashtag_medias_recent(query, amount)
    except Exception as e:
        await interaction.followup.send(f"Error searching for '{query}': {e}")
        return
    
    if not medias:
        await interaction.followup.send(f"No results found for '{query}'.")
        return
    
    for media in medias:
        embeds = create_media_embeds(media)
        for embed in embeds:
            await interaction.followup.send(embed=embed)


# Run the bot
bot.run(TOKEN)