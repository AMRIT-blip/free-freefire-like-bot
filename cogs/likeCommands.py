import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
from datetime import datetime
import json
import os
import asyncio

CONFIG_FILE = "like_channels.json"

class LikeCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_host = "https://free-fire-like-api-bay.vercel.app"
        self.config_data = self.load_config()
        self.cooldowns = {}
        self.session = aiohttp.ClientSession()

    def load_config(self):
        default_config = {"servers": {}}

        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
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
                "❌ Command not allowed here",
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
                    f"⏳ Wait **{remaining}s** before using again",
                    ephemeral=is_slash
                )
                return

        self.cooldowns[user_id] = datetime.now()

        try:
            async with ctx.typing():
                async with self.session.get(
                    f"{self.api_host}/like?uid={uid}"
                ) as response:

                    if response.status != 200:
                        await ctx.reply("⚠ API Error")
                        return

                    data = await response.json()

                    embed = discord.Embed(
                        title="✨⚡ 𝗦𝗣𝗘𝗖𝗧𝗥𝗔𝗫 𝗟𝗜𝗞𝗘𝗦 𝗦𝗘𝗡𝗧 ⚡✨",
                        description="💎 **Free Fire Auto Like System Activated**",
                        color=0x8A2BE2,
                        timestamp=datetime.now()
                    )

                    embed.add_field(
                        name="👤 𝗣𝗟𝗔𝗬𝗘𝗥 𝗜𝗡𝗙𝗢",
                        value=(
                            f"✦ **Nickname :** `{data.get('PlayerNickname','Unknown')}`\n"
                            f"✦ **UID :** `{data.get('UID')}`\n"
                            f"✦ **Region :** `{data.get('Region')}`"
                        ),
                        inline=False
                    )

                    embed.add_field(
                        name="💖 𝗟𝗜𝗞𝗘 𝗥𝗘𝗦𝗨𝗟𝗧",
                        value=(
                            f"✦ **Before :** `{data.get('LikesbeforeCommand')}`\n"
                            f"✦ **Added :** `+{data.get('LikesGivenByAPI')}`\n"
                            f"✦ **After :** `{data.get('LikesafterCommand')}`"
                        ),
                        inline=False
                    )

                    embed.add_field(
                        name="⚡ 𝗦𝗧𝗔𝗧𝗨𝗦",
                        value="`Unlimited Requests Available`",
                        inline=False
                    )

                    embed.set_thumbnail(
                        url="https://i.imgur.com/4M34hi2.png"
                    )

                    embed.set_image(
                        url="https://i.imgur.com/mYhG7zE.png"
                    )

                    embed.set_footer(
                        text="✨ Developed By SpectraX Community",
                        icon_url="https://i.imgur.com/4M34hi2.png"
                    )

                    await ctx.reply(
                        embed=embed,
                        mention_author=False
                    )

        except Exception as e:
            print(e)
            await ctx.reply("⚠ Error Occurred")

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())


async def setup(bot):
    await bot.add_cog(LikeCommands(bot))
