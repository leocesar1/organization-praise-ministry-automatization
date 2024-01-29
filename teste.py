from map.manager import *

# scraper = MultitracksScraper(
#     url="https://www.multitracks.com.br/songs/fhop-music/Infindavel/Ruja-o-Leao/"
# )

# with open(f"{scraper.getTitle()}.html", "w", encoding="utf-8") as file:
#     file.write(scraper.makeFile())

# url = "https://www.google.com/search?q=A Bênção Gabriel Guedes + Nívea Soares Bb BPM:  70  4/4"

# scraper = Scraper()
# soap = scraper.get_soap(
#     url=url,
# )

# result = soap.find("div", id="search").find_all("a")
# print(result[0]["href"])
# from telegram.manager import TelegramBot

# bot = TelegramBot()
# bot.setTopicId(bot.getDefaultsValues["message_thread_id_map"])
# name = "A Bênção - Gabriel Guedes + Nívea Soares - Bb - 70BPM - 4.4"
# with open(f"{name}.html", "rb") as file:
#     content = file.read()
# bot.sendFile(name, content)

from googlesearch import search

query = (
    "A Bênção - Gabriel Guedes + Nívea Soares - Bb - 70BPM - 4.4" + " multitracks.com"
)

print(search(query, tld="co.in", num=1, stop=1, pause=2))
