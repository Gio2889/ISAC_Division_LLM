from discord.ext import commands

class CommandGroup(commands.Cog):
    """
    Handle Reddit monitoring and interaction through Discord.

    Args:
        authorised_channel: The Discord channel authorized for bot interaction.

    Returns:
        None
    """

    def __init__(self, authorised_channel):
        self.authorised_channel = authorised_channel

    @commands.command()
    async def checknow(self, ctx):
        """
            example for commanf 
        """
        if ctx.channel.id != self.authorised_channel.id:
            await ctx.send("Im not authorized to publish in this channel")
            return
        await self.execute_checknow(ctx)