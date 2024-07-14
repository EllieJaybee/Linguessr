from dataclasses import dataclass

import crescent
import hikari
import miru

from bot.env import secret


@dataclass
class Model:
    miru: miru.Client
    table: dict


def main():
    intents = hikari.Intents.ALL_UNPRIVILEGED
    bot = hikari.GatewayBot(
        token=secret.TOKEN, banner=None, intents=intents, force_color=True
    )
    miru_client = miru.Client(bot)
    crescent_client = crescent.Client(bot, Model(miru_client, {}))
    crescent_client.plugins.load_folder("bot.plugins")
    bot.run()


if __name__ == "__main__":
    main()
