import hikari
import miru

class GameView(miru.View):
    def __init__(self):
        super().__init__(timeout=600)

    async def on_timeout(self):
        await self.message.edit(components=None)


class GameButton(miru.Button):
    def __init__(self, label: str, answer: str, author_id: hikari.Snowflake):
        self.label = label
        self.answer = answer
        self.author_id = author_id
        super().__init__(label=label)

    async def callback(self, ctx: miru.ViewContext):
        if ctx.user.id != self.author_id:
            return
        await ctx.edit_response(components=None)
        embed = ctx.message.embeds[0]
        if self.label in self.answer:
            await ctx.respond(f"{ctx.member.display_name} got {self.label} correct!")
            embed.color = "00ff00"
        else:
            await ctx.respond(
                f"{ctx.member.display_name} got it wrong, the answer is {self.answer.split(",")[0].split("(")[0].strip()}"
            )
            embed.color = "ff0000"
        embed.set_footer(
            text=f"{ctx.member.display_name} guessed {self.label}!",
            icon=ctx.member.display_avatar_url,
        )
        await ctx.edit_response(embed=embed)
        self.view.stop()

