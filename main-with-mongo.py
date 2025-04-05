from onedrive.manager import OneDrive

from telegram.manager import TelegramBot
from googleConnection.manager import GoogleSheet
from json import loads, dumps, load, dump
from requests import get
from sys import stdout
from tqdm import tqdm

from mongo.music import *
from mongo.pymongo_get_database import get_database

from datetime import datetime

from map.manager import *
from googlesearch import search

from deep_translator import GoogleTranslator

from time import sleep

dbname = get_database()


def getSearchableName(name):
    return " ".join(
        [
            "BPM: " + item.replace("BPM", "")
            if len(re.findall("BPM", item)) > 0
            else item.strip()
            for item in name.replace(".", "/").split("-")
        ]
    )


def updateAndReturnId(collection, informations: dict, collectionItemId: str):
    id = informations[collectionItemId].upper().replace(" ", "")
    del informations[collectionItemId]
    collection.update_one(
        {
            "_id": id,
        },
        {"$set": informations},
        upsert=True,
    )

    return collection.find_one(
        {
            "_id": id,
        }
    )["_id"]


def enrichMusicInfoWithDetails(target="key", details={}):
    if target in details.keys():
        return details[target]
    return None


# creating a collection
collection_name = dbname["music-details"]
collection_name_singer = dbname["singer-details"]
collection_map = dbname["music-mapping-details"]
collection_telegram = dbname["telegram-message-details"]

stdout.reconfigure(encoding="utf-8")

onedrive = OneDrive()
bot = TelegramBot()
bot.setTopicId(bot.getDefaultsValues["message_thread_id"])

scraper = Scraper()

lista = onedrive.getFileList()#[200:215]

mongoMusicList = collection_name.find(filter={}, limit=0)

mongoDBMusicAll = [
    item["oneDriveFolderId"]
    for item in collection_name.find(
        filter={}, projection={"_id": True, "oneDriveFolderId": True}, limit=0
    ).limit(0)
]

mongoDBTelegramMusic = {}
for item in collection_telegram.find(
    filter={"musicId": {"$exists": True}},
    projection={"_id": True, "musicId": True},
    limit=0,
).limit(0):
    mongoDBTelegramMusic[item["_id"]] = item["_id"]

mongoDBMapAll = [
    item["_id"]
    for item in collection_map.find(filter={}, projection={"_id": True}).limit(0)
]

for i in tqdm(range(len(lista))):
    item = lista[i]
    try:
        if "file" not in item.keys():
            name = item["name"]
            folder = item["id"]

            musicInfo = {}

            details = bot.getAudioDetails(name, name)
            musicInfo["oneDriveFolderId"] = folder
            musicInfo["_id"] = folder
            musicInfo["name"] = (
                details["music"]
                .replace("(Elite)", "")
                .replace("[Elite]", "")
                .replace("(ELITE)", "")
                .replace("(elite)", "")
                .replace("[ELITE]", "")
                .replace("[elite]", "")
                .strip()
            )
            singers = [
                {"singer": singerItem.strip()}
                for singerItem in details["artist"].split("+")
            ]

            musicInfo["singer"] = [
                updateAndReturnId(collection_name_singer, singer, "singer")
                for singer in singers
            ]

            musicInfo["elite"] = True if "ELITE" in name.upper() else False
            musicInfo["key"] = details["key"].strip()
            try:
                musicInfo["bpm"] = float(
                    details["time"].upper().split("BPM")[0].strip().replace(",", ".")
                )
            except:
                musicInfo["bpm"] = (
                    details["time"].upper().split("BPM")[0].strip().replace(",", ".")
                )
            try:
                musicInfo["compass"] = (
                    details["time"].upper().split("BPM")[1].strip()
                    if len(details["time"].upper().split("BPM")) > 0
                    else "4/4 ou 6/8"
                )
            except:
                "compass error"

            # if (
            #     collection_map.count_documents(
            #         {"_id": folder, "sequence": {"$exists": True}}
            #     )
            #     == 0
            # ):
            #     bot.setTopicId(bot.getDefaultsValues["message_thread_id_map"])

            #     query = getSearchableName(item["name"]) + " multitracks.com.br"
            #     try:
            #         for iSearch in search(query, tld="co.in", num=1, stop=1, pause=2):
            #             if "multitracks.com" in iSearch:
            #                 musicUrl = iSearch.replace("multitracks/", "")
            #                 # print(musicUrl)
            #                 scraperMusic = MultitracksScraper(url=musicUrl)
            #                 musicInfo = musicInfo | {
            #                     "resumeMap": scraperMusic.getMiniMap(),
            #                     "map": {
            #                         k: v
            #                         if k != "regionList"
            #                         else [
            #                             {
            #                                 k1: v1
            #                                 if k1 != "lineList"
            #                                 else [
            #                                     {
            #                                         k2: v2
            #                                         if k2 != "sequenceList"
            #                                         else [
            #                                             {
            #                                                 k3: v3.__dict__
            #                                                 for k3, v3 in sequence.__dict__.items()
            #                                             }
            #                                             for sequence in v2
            #                                         ]
            #                                         for k2, v2 in line.__dict__.items()
            #                                     }
            #                                     for line in v1
            #                                 ]
            #                                 for k1, v1 in region.__dict__.items()
            #                             }
            #                             for region in v
            #                         ]
            #                         for k, v in scraperMusic.mapMusic.__dict__.items()
            #                     },
            #                     "nameMap": scraperMusic.getTitle(),
            #                     "details": {
            #                         k.lower(): GoogleTranslator(
            #                             source="auto", target="pt"
            #                         ).translate(v)
            #                         if (not isinstance(v, list))
            #                         and v not in ["Referência", "Temas", "Gêneros"]
            #                         else [
            #                             GoogleTranslator(
            #                                 source="auto", target="pt"
            #                             ).translate(itemV)
            #                             for itemV in v
            #                         ]
            #                         for k, v in scraperMusic.getDetails().items()
            #                     },
            #                     # "singer": scraperMusic.getSinger(),
            #                 }

            #                 musicInfo["duration"] = enrichMusicInfoWithDetails(
            #                     target="duração", details=musicInfo["details"]
            #                 )
            #                 musicInfo["year"] = enrichMusicInfoWithDetails(
            #                     target="ano", details=musicInfo["details"]
            #                 )
            #                 musicInfo["scriptures"] = enrichMusicInfoWithDetails(
            #                     target="referência", details=musicInfo["details"]
            #                 )
            #                 musicInfo["author"] = enrichMusicInfoWithDetails(
            #                     target="autores", details=musicInfo["details"]
            #                 )
            #                 musicInfo["genre"] = enrichMusicInfoWithDetails(
            #                     target="gêneros", details=musicInfo["details"]
            #                 )

            #                 musicInfo["theme"] = enrichMusicInfoWithDetails(
            #                     target="temas", details=musicInfo["details"]
            #                 )
            #                 # musicInfo["_id"] = folder

            #                 if "bpm" not in musicInfo.keys():
            #                     musicInfo["bpm"] = enrichMusicInfoWithDetails(
            #                         target="bpm", details=musicInfo["details"]
            #                     )

            #                 if "singer" not in musicInfo.keys():
            #                     singers = [
            #                         {"singer": singerItem.strip()}
            #                         for singerItem in musicInfo["singer"]
            #                     ]

            #                     musicInfo["singer"] = [
            #                         updateAndReturnId(
            #                             collection_name_singer, singer, "singer"
            #                         )
            #                         for singer in singers
            #                     ]

            #                 resumeMap = [
            #                     {
            #                         "name": item[0],
            #                         "abreviation": item[1],
            #                         "repetition": item[2],
            #                     }
            #                     for item in musicInfo["resumeMap"]
            #                 ]

            #                 mapping = musicInfo["map"]

            #                 for item in resumeMap:
            #                     if len(mapping["regionList"]) > 0:
            #                         if (
            #                             item["name"] == mapping["regionList"][0]["name"]
            #                             and item["abreviation"]
            #                             == mapping["regionList"][0]["abreviation"]
            #                         ):
            #                             item["lineList"] = mapping["regionList"][0][
            #                                 "lineList"
            #                             ]
            #                             mapping["regionList"].pop(0)
            #                 musicInfo["sequence"] = resumeMap
            #                 musicInfo["musicId"] = folder
            #     except:
            #         print("error - get map", name)
            #         pass

            if collection_telegram.count_documents({"_id": "music" + folder}) == 0:
                # print("music" + folder)
                # print(mongoDBTelegramMusic.keys())
                bot.setTopicId(bot.getDefaultsValues["message_thread_id"])
                url = f"https://graph.microsoft.com/v1.0/drives/a9bcf86e0d3403c2/items/{folder}/children"

                getFolder = loads(get(url, headers=onedrive.HEADERS).text)["value"]
                # print(getFolder)
                getFolder = [i for i in getFolder if i["name"] == "1 - Renders"][0][
                    "id"
                ]
                url = f"https://graph.microsoft.com/v1.0/drives/a9bcf86e0d3403c2/items/{getFolder}/children"
                getFiles = loads(get(url, headers=onedrive.HEADERS).text)["value"]
                filename = {}

                for file in getFiles:
                    filename[file["id"]] = file["name"]

                downloadList = []
                for key, value in filename.items():
                    downloadUrl = f"https://graph.microsoft.com/v1.0/drives/a9bcf86e0d3403c2/items/{key}/content"
                    download = onedrive.downloadFile(downloadUrl)
                    downloadList.append({value: download})
                    print("download was done")
                try:
                    # print(downloadList.keys())
                    telegramMessageId = bot.sendMultiplesAudios(
                        name.replace("+", r" e "), downloadList
                    )

                    # print(telegramMessageId)

                    musicInfo["messageId"] = telegramMessageId
                    musicInfo["topicId"] = bot._topicId

                    telegramMusic = TelegramMongo(**musicInfo)
                    telegramMusicDict = telegramMusic.__dict__

                    # print(telegramMusic.__dict__)

                    collection_telegram.update_one(
                        {"_id": telegramMusic._id},
                        {
                            "$set": {"updatedAt": telegramMusicDict.pop("updatedAt")},
                            "$setOnInsert": telegramMusicDict,
                        },
                        upsert=True,
                    )
                except Exception as e:
                    print(f"error on sending to Telegram - {filename} - {repr(e)}")

            music = Music(**musicInfo)
            musicDict = music.__dict__

            oldItem = collection_name.find_one(
                filter={"_id": musicDict["_id"]},
            )
            oldItem = oldItem if oldItem is not None else {"default": ""}

            [
                musicDict.pop(existingItem, None)
                for existingItem in (oldItem).keys()
                if existingItem not in ["_id", "createdAt", "updatedAt"]
                and existingItem in musicDict.keys()
            ]

            collection_name.find_one_and_update(
                filter={"_id": musicDict["_id"]},
                update={
                    "$setOnInsert": {"createdAt": musicDict.pop("createdAt")},
                    "$set": musicDict,
                },
                upsert=True,
            )

            musicMap = Map(**musicInfo)
            musicMapDict = musicMap.__dict__

            oldItem = collection_map.find_one(
                filter={"_id": musicMapDict["_id"]},
            )
            oldItem = oldItem if oldItem is not None else {"default": ""}
            [
                musicMapDict.pop(existingItem, None)
                for existingItem in (oldItem).keys()
                if existingItem not in ["_id", "createdAt", "updatedAt"]
                and existingItem in musicMapDict.keys()
            ]

            collection_map.find_one_and_update(
                filter={"_id": musicMapDict["_id"]},
                update={
                    "$setOnInsert": {"createdAt": musicMapDict.pop("createdAt")},
                    "$set": musicMapDict,
                },
                upsert=True,
            )

    except Exception as errorDetails:
        print(errorDetails)
