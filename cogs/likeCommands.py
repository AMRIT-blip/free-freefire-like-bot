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
CONFIG_FILE = "like_channels.json"

class LikeCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_host = "https://free-fire-like-api-bay.vercel.app"
        self.config_data = self.load_config()
        self.cooldowns = {}
        self.session = aiohttp.ClientSession()

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
            except:
                pass

        return default_config

    async def check_channel(self, ctx):
        if ctx.guild is None:
            return True

        guild_id = str(ctx.guild.id)
        like_channels = self.config_data["servers"].get(guild_id, {}).get("like_channels", [])

        return not like_channels or str(ctx.channel.id) in like_channels

    @commands.hybrid_command(name="like", description="Send Free Fire Likes")
    async def like_command(self, ctx: commands.Context, uid: str):

        is_slash = ctx.interaction is not None

        if not await self.check_channel(ctx):
            await ctx.reply(
                "This command not allowed in this channel",
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
                    f"⏳ Wait {remaining}s",
                    ephemeral=is_slash
                )
                return

        self.cooldowns[user_id] = datetime.now()

        if not uid.isdigit():
            await ctx.reply(
                "Invalid UID",
                ephemeral=is_slash
            )
            return

        try:
            async with ctx.typing():
                async with self.session.get(
                    f"{self.api_host}/like?uid={uid}"
                ) as response:

                    if response.status != 200:
                        await ctx.reply("API Error")
                        return

                    data = await response.json()

                    embed = discord.Embed(
                        title="⚡ SpectraX | Likes Sent ⚡",
                        color=0x6c5ce7,
                        timestamp=datetime.now()
                    )

                    embed.add_field(
                        name="✦ Nickname",
                        value=f"`{data.get('PlayerNickname','Unknown')}`",
                        inline=True
                    )

                    embed.add_field(
                        name="✦ Region",
                        value=f"`{data.get('Region','IND')}`",
                        inline=True
                    )

                    embed.add_field(
                        name="✦ Player UID",
                        value=f"`{data.get('UID')}`",
                        inline=False
                    )

                    embed.add_field(
                        name="✦ Like Before",
                        value=f"`{data.get('LikesbeforeCommand')}`",
                        inline=True
                    )

                    embed.add_field(
                        name="✦ Likes Added",
                        value=f"`+{data.get('LikesGivenByAPI')}`",
                        inline=True
                    )

                    embed.add_field(
                        name="✦ Like After",
                        value=f"`{data.get('LikesafterCommand')}`",
                        inline=True
                    )

                    embed.add_field(
                        name="✦ Requests Remaining",
                        value="`Unlimited`",
                        inline=False
                    )

                    embed.set_thumbnail(
                        url="https://i.imgur.com/WEZ0Pbk.png"
                    )

                    # Footer GIF
                    embed.set_image(
                        url="https://i.imgur.com/WEZ0Pbk.gif"
                    )

                    # Footer Text Only
                    embed.set_footer(
                        text="Developed by SpectraX-Community"
                    )

                    await ctx.reply(
                        embed=embed,
                        mention_author=False
                    )

        except Exception as e:
            print(e)
            await ctx.reply("Error occurred")

    def cog_unload(self):
        self.bot.loop.create_task(
            self.session.close()
        )

async def setup(bot):
    await bot.add_cog(LikeCommands(bot))
