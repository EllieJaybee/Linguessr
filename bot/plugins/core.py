from bs4 import BeautifulSoup as bs
import crescent
import detectlanguage
import hikari

import aiohttp
import random

from bot.__main__ import Model
from bot.env.secret import LANGKEY
from bot.component import GameButton, GameView

Plugin = crescent.Plugin[hikari.GatewayBot, Model]
plugin = Plugin()

detectlanguage.configuration.api_key = LANGKEY

class UnknownLanguageError(ValueError):
    pass

@plugin.include
@crescent.command(
    name="play",
    description="Start playing linguessr",
    dm_enabled=False,
    default_member_permissions=hikari.Permissions.USE_APPLICATION_COMMANDS,
)
class Game:
    difficulty = crescent.option(
        int,
        "Difficulty of the game",
        default=2,
        choices=[("easy", 2), ("normal", 3), ("hard", 4), ("insane", 8)],
    )

    async def callback(self, ctx: crescent.Context):
        await ctx.defer()
        self.ctx = ctx
        words, englishes = await self.get_words()
        language_code: str = await self.get_language_code(words)
        choice_languages = await self.get_wrong_languages(language_code)
        language: str = plugin.model.table[language_code]
        choice_languages.append(language.split(",")[0].split("(")[0].strip())
        random.shuffle(choice_languages)
        await self.send_message(words, englishes, choice_languages, language)

    async def send_message(self, words, englishes, choice_languages, language):
        embed = await self.build_embed(words, englishes)
        gameview = GameView()
        for choice_language in choice_languages:
            gameview.add_item(GameButton(choice_language, language, self.ctx.user.id))
        await self.ctx.respond(embed=embed, components=gameview)
        plugin.model.miru.start_view(gameview)
        await gameview.wait()

    async def get_wrong_languages(self, code):
        choice_languages: list[str] = []
        filtered_table_keys = list(plugin.model.table.keys())
        try:
            filtered_table_keys.remove(code)
        except ValueError as e:
            print(f"Offending langcode is {code}")
            raise e
        for wrong_key in random.sample(filtered_table_keys, self.difficulty):
            choice_languages.append(
                plugin.model.table[wrong_key].split(",")[0].split("(")[0].strip()
            )
        return choice_languages

    async def build_embed(self, words: list[str], englishes: list[str]):
        embed = hikari.Embed(title="Guess the language!", color="C721B1")
        embed.set_footer(
            text=f"{self.ctx.member.display_name} is playing",
            icon=self.ctx.member.display_avatar_url,
        )
        await self.build_fields(words, englishes, embed)
        return embed

    async def build_fields(
        self, words: list[str], englishes: list[str], embed: hikari.Embed
    ):
        for word, english in zip(words, englishes):
            if self.difficulty >= 4:
                english = random.choice([english, "???"])
            if (self.difficulty >= 6) and (random.randint(1, 6) >= 3):
                obfuscated_characters = []
                for char in list(word):
                    if random.randint(1, 6) >= 5:
                        char = "\\*"
                    obfuscated_characters.append(char)
                word = "".join(obfuscated_characters)
            embed.add_field(name=word, value=english, inline=True)

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
        detected_languages = detectlanguage.detect(" ".join(words))
        for detected_language in detected_languages:
            if detected_language["isReliable"]:
                return detected_language["language"]

@plugin.include
@crescent.catch_command(UnknownLanguageError)
async def on_unknown_lang(exc: UnknownLanguageError, ctx: crescent.Context):
    await ctx.respond("Error occured, please report this to bot maintainer")