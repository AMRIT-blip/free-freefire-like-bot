    @commands.hybrid_command(name="setchannel", description="Set Like Command Channel")
    @commands.has_permissions(administrator=True)
    async def set_channel(self, ctx, channel: discord.TextChannel):

        guild_id = str(ctx.guild.id)

        if guild_id not in self.config_data["servers"]:
            self.config_data["servers"][guild_id] = {
                "like_channels": []
            }

        self.config_data["servers"][guild_id]["like_channels"] = [str(channel.id)]

        with open(CONFIG_FILE, "w") as f:
            json.dump(self.config_data, f, indent=4)

        await ctx.reply(
            f"✅ Like command set to {channel.mention}"
        )


    @commands.hybrid_command(name="removechannel", description="Remove Like Channel")
    @commands.has_permissions(administrator=True)
    async def remove_channel(self, ctx):

        guild_id = str(ctx.guild.id)

        if guild_id in self.config_data["servers"]:
            self.config_data["servers"][guild_id]["like_channels"] = []

            with open(CONFIG_FILE, "w") as f:
                json.dump(self.config_data, f, indent=4)

        await ctx.reply(
            "✅ Channel restriction removed"
        )


    @commands.hybrid_command(name="listchannels", description="Show Allowed Channels")
    async def list_channels(self, ctx):

        guild_id = str(ctx.guild.id)

        channels = self.config_data["servers"].get(
            guild_id, {}
        ).get("like_channels", [])

        if not channels:
            await ctx.reply(
                "No channels set"
            )
            return

        mentions = [f"<#{c}>" for c in channels]

        await ctx.reply(
            "Allowed Channels:\n" + "\n".join(mentions)
        )
