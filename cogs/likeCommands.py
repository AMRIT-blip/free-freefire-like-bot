import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
from datetime import datetime
import json
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
CONFIG_FILE = "like_channels.json"

class LikeCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_host = "https://free-fire-like-api-bay.vercel.app"
        self.config_data = self.load_config()
        self.cooldowns = {}
        self.session = aiohttp.ClientSession()

        self.headers = {}
        if RAPIDAPI_KEY:
            self.headers = {
                'x-rapidapi-key': RAPIDAPI_KEY,
                'x-rapidapi-host': "free-fire-like1.p.rapidapi.com"
            }

    def load_config(self):
        default_config = {
            "servers": {}
        }
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    loaded_config = json.load(f)
                    loaded_config.setdefault("servers", {})
                    return loaded_config
            except json.JSONDecodeError:
                print(f"WARNING: '{CONFIG_FILE}' corrupt. Resetting.")
        self.save_config(default_config)
        return default_config

    def save_config(self, config_to_save=None):
        data_to_save = config_to_save if config_to_save else self.config_data
        temp_file = CONFIG_FILE + ".tmp"
        with open(temp_file, 'w') as f:
            json.dump(data_to_save, f, indent=4)
        os.replace(temp_file, CONFIG_FILE)

    async def check_channel(self, ctx):
        if ctx.guild is None:
            return True
        guild_id = str(ctx.guild.id)
        like_channels = self.config_data["servers"].get(guild_id, {}).get("like_channels", [])
        return not like_channels or str(ctx.channel.id) in like_channels

    @commands.hybrid_command(name="like", description="Send likes to Free Fire player")
    @app_commands.describe(uid="Player UID")
    async def like_command(self, ctx: commands.Context, uid: str):

        is_slash = ctx.interaction is not None

        if not await self.check_channel(ctx):
            await ctx.reply(
                "This command is not allowed in this channel.",
                ephemeral=is_slash
            )
            return

        user_id = ctx.author.id
        cooldown = 30

        if user_id in self.cooldowns:
            last = self.cooldowns[user_id]
            remaining = cooldown - (datetime.now() - last).seconds
            if remaining > 0:
                await ctx.reply(
                    f"⏳ Wait {remaining}s before using again.",
                    ephemeral=is_slash
                )
                return

        self.cooldowns[user_id] = datetime.now()

        if not uid.isdigit() or len(uid) < 6:
            await ctx.reply(
                "❌ Invalid UID",
                ephemeral=is_slash
            )
            return

        try:
            async with ctx.typing():
                async with self.session.get(
                    f"{self.api_host}/like?uid={uid}"
                ) as response:

                    if response.status == 404:
                        await self._send_player_not_found(ctx, uid)
                        return

                    if response.status == 429:
                        await self._send_api_limit(ctx)
                        return

                    if response.status != 200:
                        await self._send_api_error(ctx)
                        return

                    data = await response.json()

                    embed = discord.Embed(
                        title="🔥 FREE FIRE LIKE",
                        color=0x00ffcc,
                        timestamp=datetime.now()
                    )

                    if data.get("status") == 1:

                        embed.description = (
                            f"┌ ACCOUNT INFO\n"
                            f"├ Nickname : {data.get('PlayerNickname')}\n"
                            f"├ UID : {data.get('UID')}\n"
                            f"├ Region : {data.get('Region')}\n"
                            f"└ RESULT\n"
                            f"   ├ Added : +{data.get('LikesGivenByAPI')}\n"
                            f"   ├ Before : {data.get('LikesbeforeCommand')}\n"
                            f"   └ After : {data.get('LikesafterCommand')}\n"
                        )

                    else:
                        embed.description = (
                            "⚠️ Max likes reached for today"
                        )

                    embed.set_footer(
                        text="Developed By Thug"
                    )

                    await ctx.reply(
                        embed=embed,
                        mention_author=False
                    )

        except asyncio.TimeoutError:
            await self._send_error(
                ctx,
                "Timeout",
                "Server took too long"
            )

        except Exception as e:
            print(e)
            await self._send_error(
                ctx,
                "Error",
                "Something went wrong"
            )

    async def _send_player_not_found(self, ctx, uid):
        embed = discord.Embed(
            title="❌ Player Not Found",
            description=f"UID {uid} not found",
            color=0xff0000
        )
        await ctx.reply(embed=embed)

    async def _send_api_limit(self, ctx):
        embed = discord.Embed(
            title="⚠️ API Limit Reached",
            description="Too many requests. Try later.",
            color=0xff9900
        )
        await ctx.reply(embed=embed)

    async def _send_api_error(self, ctx):
        embed = discord.Embed(
            title="⚠️ API Error",
            description="Server not responding",
            color=0xff0000
        )
        await ctx.reply(embed=embed)

    async def _send_error(self, ctx, title, desc):
        embed = discord.Embed(
            title=title,
            description=desc,
            color=0xff0000
        )
        await ctx.reply(embed=embed)

    def cog_unload(self):
        self.bot.loop.create_task(
            self.session.close()
        )


async def setup(bot):
    await bot.add_cog(LikeCommands(bot))
