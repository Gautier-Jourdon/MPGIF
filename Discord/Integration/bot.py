import discord
from discord import app_commands
from discord.ext import commands
import os
import aiohttp

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️ python-dotenv not installed. Environment variables might not load from .env file.")

TOKEN = os.getenv('DISCORD_BOT_TOKEN') 
SERVER_URL = os.getenv('SERVER_URL', 'http://localhost:5000')

if not TOKEN:
    print("❌ ERROR: DISCORD_BOT_TOKEN not found in environment variables or .env")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'🤖 Logged in as {bot.user}!')
    if SERVER_URL == 'http://localhost:5000':
        print("⚠️ Warning: SERVER_URL is set to localhost. Discord won't be able to access image links unless you are just testing the bot logic locally.")
    else:
        print(f"🔗 Connected to MPGIF Server: {SERVER_URL}")

    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"❌ Error syncing commands: {e}")

async def get_or_create_webhook(channel, bot_user):
    """
    Finds a webhook in the channel owned by the bot, or creates one.
    Ensures publishing goes to the *current* active channel.
    """
    try:
        webhooks = await channel.webhooks()
        # reusing existing webhook owned by us
        for wh in webhooks:
            if wh.user == bot_user and wh.token: 
                return wh
        
        # If max webhooks reached (10), try to use ANY we have access to
        if len(webhooks) >= 10:
             for wh in webhooks:
                 if wh.token: return wh
                 
        return await channel.create_webhook(name="MPGIF Proxy")
    except Exception as e:
        print(f"❌ Webhook Error in #{channel.name}: {e}")
        raise e

@bot.tree.command(name="catalogue", description="Open the Visual Web Gallery")
async def catalogue(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True) 
    
    try:
        if not isinstance(interaction.channel, discord.TextChannel):
            await interaction.followup.send("❌ This command works best in server text channels (needs Webhook support).")
            return

        base_url = SERVER_URL.rstrip('/')
            
        webhook = await get_or_create_webhook(interaction.channel, interaction.client.user)
        
        user_id = str(interaction.user.id)
        username = interaction.user.name
        
        channel_name = interaction.channel.name
        guild_id = str(interaction.guild_id)
        
        # We pass guild_id so the server can list channels for this guild
        gallery_url = f"{base_url}/browse?wh={webhook.url}&uid={user_id}&user={username}&channel={channel_name}&gid={guild_id}"
        
        embed = discord.Embed(
            title="🖼️ MPGIF Visual Gallery",
            description=f"Browse and post MPGIFs as {interaction.user.mention}!",
            color=0x00ff00
        )
        
        view = discord.ui.View()
        button = discord.ui.Button(label="Open Gallery 🚀", style=discord.ButtonStyle.link, url=gallery_url)
        view.add_item(button)
        
        await interaction.followup.send(embed=embed, view=view)
        
    except Exception as e:
        await interaction.followup.send(f"❌ Error setting up gallery: {e}")


if __name__ == "__main__":
    if not TOKEN:
         print("❌ Cannot start bot: DISCORD_BOT_TOKEN is missing.")
    else:
        bot.run(TOKEN)
