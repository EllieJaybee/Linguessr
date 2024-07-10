from bs4 import BeautifulSoup as bs
import crescent
import detectlanguage
import hikari
import miru

import aiohttp
import random

from bot.__main__ import Model
from bot.env.secret import LANGKEY

Plugin = crescent.Plugin[hikari.GatewayBot, Model]
plugin = Plugin()

detectlanguage.configuration.api_key = LANGKEY

language_table: dict[str, str] = {}


@plugin.include
@crescent.event
async def fetch_language_table(_: hikari.StartedEvent):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://en.wikipedia.org/wiki/List_of_ISO_639_language_codes"
        ) as response:
            soup = bs(await response.read(), "html.parser")
            table = soup.find(id="Table", class_="wikitable sortable")
            rows = table.find_all("tr")[1:]
            for row in rows:
                name = row.find_all("td")[0].get_text().strip()
                code = row.find_all("td")[1].get_text().strip()
                language_table[code] = name


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
        if self.label in self.answer:
            await ctx.respond(f"{ctx.member.display_name} got {self.label} correct!")
            embed = ctx.message.embeds[0]
            embed.color = "00ff00"
            await ctx.edit_response(embed=embed)
        else:
            await ctx.respond(
                f"{ctx.member.display_name} got it wrong, the answer is {self.answer.split(",")[0].split("(")[0].strip()}"
            )
            embed = ctx.message.embeds[0]
            embed.color = "ff0000"
            await ctx.edit_response(embed=embed)
        self.view.stop()


@plugin.include
@crescent.command(name="play", description="Start playing linguessr", dm_enabled=False, default_member_permissions=hikari.Permissions.USE_APPLICATION_COMMANDS)
class Game:
    difficulty = crescent.option(
        int,
        "Difficulty of the game",
        default=2,
        choices=[("easy", 2), ("normal", 4)],
    )

    async def callback(self, ctx: crescent.Context):
        await ctx.defer()
        words, englishes = await self.get_words()
        language_code: str = await self.get_language_code(words)
        choice_languages: list[str] = []
        filtered_table_keys = list(language_table.keys())
        filtered_table_keys.remove(language_code)

        for _ in range(self.difficulty):
            choice_languages.append(
                language_table[random.choice(filtered_table_keys)]
                .split(",")[0]
                .split("(")[0]
                .strip()
            )
        language: str = language_table[language_code]
        embed = await self.build_embed(words, englishes)
        gameview = GameView()
        choice_languages.append(language.split(",")[0].split("(")[0].strip())
        choice_languages.sort()

        for choice_language in choice_languages:
            gameview.add_item(GameButton(choice_language, language, ctx.user.id))

        await ctx.respond(embed=embed, components=gameview)
        plugin.model.miru.start_view(gameview)

        await gameview.wait()

    async def build_embed(self, words: list[str], englishes: list[str]):
        embed = hikari.Embed(title="Guess the language!", color="C721B1")
        for word, english in zip(words, englishes):
            embed.add_field(name=word, value=english)
        return embed

    async def get_words(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://baltoslav.eu/adhadaj/index.php?co=g&mova=en"
            ) as response:
                soup = bs(await response.read(), "html.parser")
                words: list[str] = [_.get_text() for _ in soup.find_all(class_="prawy")]
                englishes: list[str] = [
                    _.get_text() for _ in soup.find_all(class_="lewy")
                ]
                return (words, englishes)

    async def get_language_code(self, words: list[str]):
        for word in words:
            detected_languages = detectlanguage.detect(word)
            for detected_language in detected_languages:
                if detected_language["isReliable"]:
                    return detected_language["language"]
