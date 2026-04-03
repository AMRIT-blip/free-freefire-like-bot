import discord
from discord.ext import commands
import aiohttp
from datetime import datetime
import asyncio
from dotenv import load_dotenv

load_dotenv()

class LikeCommands(commands.Cog):

    # Allowed Server & Channel
    ALLOWED_SERVER_ID = 1320706753490452520
    ALLOWED_CHANNEL_ID = 1489714786483830836

    def __init__(self, bot):
        self.bot = bot
        self.api_host = "https://free-fire-like-api-bay.vercel.app"
        self.cooldowns = {}
        self.session = aiohttp.ClientSession()

    async def check_channel(self, ctx):
        if ctx.guild is None:
            return False

        if ctx.guild.id != self.ALLOWED_SERVER_ID:
            return False

        if ctx.channel.id != self.ALLOWED_CHANNEL_ID:
            return False

        return True


    @commands.hybrid_command(name="like", description="Send Free Fire Likes")
    async def like_command(self, ctx: commands.Context, uid: str):

        is_slash = ctx.interaction is not None

        if not await self.check_channel(ctx):
            await ctx.reply(
                "⚠️ This command only works in official SpectraX channel",
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

                    likes_added = data.get("LikesGivenByAPI", 0)

                    # Maximum Likes Reached
                    if likes_added == 0:
                        embed = discord.Embed(
                            title="⚠️ SpectraX | Maximum Likes Reached",
                            description="This UID has already received maximum likes for today.",
                            color=0xff4757,
                            timestamp=datetime.now()
                        )

                        embed.add_field(
                            name="✦ Player UID",
                            value=f"`{uid}`",
                            inline=False
                        )

                        embed.set_image(
                            url="https://i.imgur.com/WEZ0Pbk.gif"
                        )

                        embed.set_footer(
                            text="Developed by SpectraX-Community"
                        )

                        await ctx.reply(embed=embed)
                        return

                    # Success Embed
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

                    embed.set_image(
                        url="https://i.imgur.com/WEZ0Pbk.gif"
                    )

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
