from bs4 import BeautifulSoup as bs
import crescent
import hikari

import aiohttp

from bot.__main__ import Model

Plugin = crescent.Plugin[hikari.GatewayBot, Model]
plugin = Plugin()
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
            rows = table.find_all("tr")[2:]
            for row in rows:
                name = row.find_all("td")[0].get_text().strip()
                code = row.find_all("td")[1].get_text().strip()
                plugin.model.table[code] = name
    plugin.model.table["bh"] = "Bihari"
    plugin.model.table["iw"] = "Hebrew"
    plugin.model.table["ji"] = "Yiddish"
    plugin.model.table["jw"] = "Javanese"
    plugin.model.table["mo"] = "Moldovan"
    plugin.model.table["sh"] = "Serbo-Croatian"