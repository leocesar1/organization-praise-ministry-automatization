from onedrive.manager import OneDrive
from map.manager import *
from telegram.manager import TelegramBot
from googlesearch import search

# from googleConnection.manager import GoogleSheet
from json import loads, dumps, load, dump
from requests import get
from sys import stdout
from tqdm import tqdm

import re, time


def getSearchableName(name):
    return " ".join(
        [
            "BPM: " + item.replace("BPM", "")
            if len(re.findall("BPM", item)) > 0
            else item.strip()
            for item in name.replace(".", "/").split("-")
        ]
    )


stdout.reconfigure(encoding="utf-8")

onedrive = OneDrive()
bot = TelegramBot()
bot.setTopicId(bot.getDefaultsValues["message_thread_id_map"])
scraper = Scraper()

lista = onedrive.getFileList()  # [200:]

with open("message/sucessos-map.json", "r", encoding="utf-8") as file:
    successList = load(file)["data"]

erros = []
sucessos = []

# print(lista)
for i in tqdm(range(len(lista))):
    item = lista[i]
    query = getSearchableName(item["name"]) + " multitracks.com"

    # print(query)
    name = item["name"]  # .encode("utf-8")#.decode("utf-8"))

    try:
        if "file" not in item.keys() and name not in successList.keys():
            # url = f"https://www.google.com/search?q={searchableName}"
            # soap = scraper.get_soap(url=url)
            # time.sleep(2)
            # musicUrl = soap.find("div", id="search").find_all("a")[0]["href"]
            for i in search(query, tld="co.in", num=1, stop=1, pause=2):
                musicUrl = i
            scraperMusic = MultitracksScraper(url=musicUrl)

            content = bytes(scraperMusic.makeFile(), "utf-8")
            print(name)
            print(f"{item['name']}.html")
            sucessos.append(bot.sendFile(name, content))

    except:
        erros.append(name)

print("quantidade de erros = " + str(len(erros)))
print("erros = " + str(erros))
erros = {"data": erros}
json_object = dumps(erros, indent=4)
with open("erros-map.json", "w", encoding="utf-8") as file:
    file.write(json_object)

print("quantidade de sucessos = " + str(len(sucessos)))
print("sucessos = " + str(sucessos))


with open("message/sucessos-map.json", "r", encoding="utf-8") as file:
    sucessosNew = load(file)

for item in sucessos:
    for key, value in item.items():
        sucessosNew["data"][key] = value

json_object = dumps(sucessosNew, indent=4)
with open("message/sucessos-map.json", "w", encoding="utf-8") as file:
    file.write(json_object)


# print(sucessosNew["data"].keys())
