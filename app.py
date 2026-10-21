import discord
from discord.ext import commands , tasks 
import os
import traceback
from flask import Flask
import threading
import sys
import aiohttp
import time

from dotenv import load_dotenv


app = Flask(__name__)
bot_name = "None"



@app.route('/')
def home():
    return f"Bot {bot_name} is active"


def run_flask():
    port = int(os.environ.get("PORT", 10000))
    if os.name == 'nt':
        from waitress import serve
        serve(app, host="0.0.0.0", port=port)
    else:
        app.run(host='0.0.0.0', port=port)


flask_thread = threading.Thread(target=run_flask, daemon=True)
flask_thread.start()

if os.path.exists(".env"):
    load_dotenv()

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("TOKEN not found in environment variables")

extensions = [
    "cogs.likeCommands"
]


class Seemu(commands.Bot):
    def __init__(self, command_prefix: str, intents: discord.Intents, **kwargs):
        super().__init__(command_prefix=command_prefix, intents=intents, **kwargs)
        self.session = None
        self.initialized = False

    async def setup_hook(self) -> None:
        self.session = aiohttp.ClientSession()

        for ext in extensions:
            try:
                await self.load_extension(ext)
                print(f"✅ {ext} loaded successfully")
            except Exception as e:
                print(f"❌ Failed to load {ext}: {e}")
                traceback.print_exc()

        await self.tree.sync()
        print("✔ All cogs loaded")
        self.initialized = True
        self.update_activity_task.start()

    async def on_ready(self):
        global bot_name
        if not self.initialized:
            return

        server_count = len(self.guilds) #
        activity = discord.Game(name=f"Sharing likes on {server_count} servers")
        await self.change_presence(activity=activity)
        bot_name = f"{self.user}"
        print(f"\n🔗 Connected as {bot_name}")
        print(f"🌐 Flask running on port {os.environ.get('PORT', 10000)}\n")

    @tasks.loop(minutes=5) 
    
    async def update_activity_task(self):

        try:
            server_count = len(self.guilds) #
            activity = discord.Game(name=f"Sharing likes on {server_count} servers !! ")
            await self.change_presence(activity=activity)
            print(f"Activité mise à jour : Partage de likes sur {server_count} serveurs")

        except Exception as e:
            print(f"⚠️ Erreur lors de la mise à jour de l'activité : {e}")
            traceback.print_exc()

    @update_activity_task.before_loop
    async def before_update_activity_task(self):
       
        await self.wait_until_ready()
        print("Bot ready, starting activity update loop.")
    async def close(self):
        if self.session:
            await self.session.close()
        await super().close()

    

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Global error handler for all commands"""
        if isinstance(error, commands.MissingPermissions):
            try:
                msg = "❌ You need to be an administrator to use this command."
                if ctx.interaction and ctx.interaction.response.is_done():
                    await ctx.followup.send(msg, ephemeral=True)
                else:
                    await ctx.send(msg, ephemeral=True)
            except:
                pass
            return

        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("⚠️ Missing required argument.", ephemeral=True)
            return

        elif isinstance(error, commands.CommandNotFound):
            return

        print(f"Unhandled error: {error}")
        traceback.print_exc()
        await ctx.send("⚠️ An unexpected error occurred. [1214]", ephemeral=True)


if __name__ == "__main__":
    retry_delay = 15 * 60

    while True:
        try:
            intents = discord.Intents.all()
            bot = Seemu(command_prefix="!", intents=intents)
            bot.run(TOKEN)
            break
        except discord.errors.LoginFailure:
            print("❌ Discord rejected the bot token. Check the TOKEN environment variable.")
            sys.exit(1)
        except discord.HTTPException as e:
            # Cloudflare 1015 is an IP-based rate limit. Rapid Render restarts
            # can repeat the login request and prolong the block, so retry slowly.
            response_text = str(getattr(e, "text", ""))
            if e.status == 429 and ("1015" in response_text or "cloudflare" in response_text.lower()):
                print(
                    f"⚠️ Discord/Cloudflare rate-limited this connection (HTTP 429, 1015). "
                    f"Check that only one instance uses this token. Retrying in {retry_delay // 60} minutes."
                )
                time.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 60 * 60)
                continue
            print(f"⚠️ Discord HTTP error (status {e.status}): {e}")
            traceback.print_exc()
            sys.exit(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping bot...")
            sys.exit(0)
        except Exception as e:
            print(f"⚠️ Unexpected error: {e}")
            traceback.print_exc()
            sys.exit(1)
