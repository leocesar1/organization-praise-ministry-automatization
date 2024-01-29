from mongo.pymongo_get_database import get_database

from datetime import datetime

from mongo.music import *
from map.manager import *


dbname = get_database()

# # # creating a collection
collection_name = dbname["music-details"]
collection_map = dbname["music-mapping-details"]
collection_telegram = dbname["telegram-message-details"]
collection_name_singer = dbname["singer-details"]

mongoDBMusicAll = [
    item
    for item in collection_name.find(
        filter={},
        projection={
            "name": True,
            "_id": True,
            "oneDriveFolderId": True,
            "telegramAudioMessageId": True,
        },
    )
]

print(mongoDBMusicAll)
# from telegram.manager import TelegramBot

# bot = TelegramBot()
# # bot.setTopicId(bot.getDefaultsValues["message_thread_id_map"])

# from time import sleep

# n = 1
# bot.setTopicId(bot.getDefaultsValues["message_thread_id_map"])
# for item in collection_map.find(
#     filter={"sequence": {"$exists": True}},
#     projection={},
# ):
#     details = (
#         item
#         | collection_name.find_one({"_id": item["_id"]})
#         | (collection_telegram.find_one({"_id": "map" + item["_id"]}) or {})
#     )

#     updateMapFlow = (
#         "type" in details.keys() and not details["type"] == "map"
#     ) or "type" not in details.keys()

#     if updateMapFlow:
#         if n > 30:
#             sleep(50)
#             n = 1
#         else:
#             n += 1

#         try:
#             singer = [
#                 collection_name_singer.find_one({"_id": s})["name"]
#                 for s in details["singer"]
#             ]
#             details["singer"] = singer
#         except:
#             pass
#         mapFile = MapFile(**details)
#         # with open("teste_html.html", "w", encoding="utf-8") as f:
#         #     f.write(mapFile.makeFile())
#         content = bytes(mapFile.makeFile(), "utf-8")
#         # print(details["name"])
#         # print(f'{details["name"]}.html')

#         try:
#             details["messageId"] = bot.sendFile(details=details, content=content)

#             details["topicId"] = bot._topicId

#             telegramMap = TelegramMongo(**details)

#             telegramMapDic = telegramMap.__dict__
#             # print(telegramMusic.__dict__)

#             collection_telegram.update_one(
#                 {"_id": telegramMapDic["_id"]},
#                 {
#                     "$set": {"updatedAt": telegramMapDic.pop("updatedAt")},
#                     "$setOnInsert": telegramMapDic,
#                 },
#                 upsert=True,
#             )
#         except Exception as e:
#             print("error ", details["name"], e)
# folder = "A9BCF86E0D3403C2!405841"
# collection_telegram = dbname["telegram-message-details"]

# i = 0

# musicInfo = {
#     "oneDriveFolderId": "A9BCF86E0D3403C2!397362",
#     "_id": "A9BCF86E0D3403C2!397362",
#     "name": "A Bênção",
#     "elite": False,
#     "key": "Bb",
#     "bpm": 70.0,
#     "compass": "4/4",
#     "singer": ["Gabriel Guedes", "Nivea Soares"],
#     "duration": "6:00",
#     "year": "2020",
#     "scriptures": ["Números 6:24-26", "Salmos 103:17-18"],
#     "genre": ["Contemporâneo", "Dueto"],
# }


# music = Music(**musicInfo)
# musicDict = music.__dict__

# [
#     musicDict.pop(existingItem)
#     for existingItem in collection_name.find_one(
#         filter={"_id": musicDict["_id"]},
#     ).keys()
#     if existingItem in ["_id", "createdAt", "updatedAt"]
#     and existingItem in musicInfo.keys()
# ]

# collection_name.find_one_and_update(
#     filter={"_id": musicDict["_id"]},
#     update={
#         "$setOnInsert": {"createdAt": musicDict.pop("createdAt")},
#         "$set": musicDict,
#     },
#     upsert=True,
# )

# print(musicDict.pop("_id"))
# print(musicDict)
# print(
# updatedAt = musicDict.pop("updatedAt")
# update = collection_name.find_one_and_update(
#     filter={"_id": "A9BCF86E0D3403C2!397362"},
#     update={
#         "$setOnInsert": musicDict,
#         "$set": {"updatedAt": updatedAt},
#     },
#     upsert=True,
# )
# collection_name.bulk_write(update)
# )
# from telegram.manager import *

# bot = TelegramBot()


# for item in collection_telegram.find({}):
#     i += 1
#     # print(collection_name.find_one({"_id": item["_id"].replace("music", "")}))
#     print(i)
#     newcaption = bot.makeNewCaption(
#         details=collection_name.find_one(
#             {"_id": item["_id"].replace("music", "")}, {"_id": 0}
#         )
#     )
#     print(newcaption)
#     print(bot.updateCaption(messageId=item["messageId"], newCaption=newcaption))


# mongoDBMusicAll = [
#     item
#     for item in collection_name.find(
#         filter={},
#         projection={
#             "name": True,
#             "_id": True,
#             "oneDriveFolderId": True,
#             "telegramAudioMessageId": True,
#         },
#     )
# ]

# mongoDBTelegram = [
#     item
#     for item in collection_telegram.find(
#         filter={"musicId": {"$exists": True}},
#         projection={"_id": True, "musicId": True},
#     )
# ]

# print(mongoDBTelegram)

# print(mongoDBMusicAll)
# from deep_translator import GoogleTranslator

# for item in mongoDBMusicAll:
#     print(GoogleTranslator(source="auto", target="pt").translate(item["name"]))
# for item in mongoDBMusicAll:
#     now = datetime.now().timestamp()

#     collection_name.update_one(
#         {"_id": item["_id"]},
#         {
#             "$unset": {"telegramAudioMessageId": ""},
#             "$set": {"updatedAt": now},
#         },
#         upsert=True,
#     )


# from datetime import datetime

# expiry_date = datetime.now()
# expiry = expiry_date.timestamp()
# item = {
#     "_id": 1,
#     "originalName": "test",
#     "update_date": expiry,
# }

# # insert
# collection_name.insert_one(item)

# for item in collection_name.find({"_id": 1}):
#     print(item)

# teste = {
#     "resumeMap": [
#         ["Introdu\u00e7\u00e3o", "In", 1],
#         ["Verso", "V", 1],
#         ["Refr\u00e3o", "R", 1],
#         ["Verso", "V", 1],
#         ["Refr\u00e3o", "R", 1],
#         ["Ponte", "P", 4],
#         ["Ponte 2", "P2", 1],
#         ["Ponte 3", "P3", 1],
#         ["Repete", "Re", 4],
#         ["Refr\u00e3o", "R", 1],
#         ["Ponte", "P", 2],
#         ["Ponte 2", "P2", 1],
#         ["Ponte 3", "P3", 1],
#         ["Repete", "Re", 4],
#         ["Refr\u00e3o", "R", 1],
#         ["Final", "F", 1],
#     ],
#     "map": {
#         "name": "A B\u00ean\u00e7\u00e3o",
#         "regionList": [
#             {
#                 "repetition": 1,
#                 "name": "Verso",
#                 "lineList": [
#                     {
#                         "sequenceList": [
#                             {
#                                 "lyrics": {"lyrics": "Que o Senhor te  Aben\u00e7oe"},
#                                 "chords": {"chordStr": ""},
#                             }
#                         ]
#                     },
#                     {
#                         "sequenceList": [
#                             {
#                                 "lyrics": {
#                                     "lyrics": "E fa\u00e7a Brilhar seu rosto em Ti"
#                                 },
#                                 "chords": {"chordStr": ""},
#                             }
#                         ]
#                     },
#                     {
#                         "sequenceList": [
#                             {
#                                 "lyrics": {"lyrics": "Que conceda  sua gra\u00e7a"},
#                                 "chords": {"chordStr": ""},
#                             }
#                         ]
#                     },
#                     {
#                         "sequenceList": [
#                             {
#                                 "lyrics": {"lyrics": "E te d\u00ea Paz"},
#                                 "chords": {"chordStr": ""},
#                             }
#                         ]
#                     },
#                 ],
#                 "abreviation": "V",
#             },
#             {
#                 "repetition": 1,
#                 "name": "Refr\u00e3o",
#                 "lineList": [
#                     {
#                         "sequenceList": [
#                             {
#                                 "lyrics": {"lyrics": "Am\u00e9m, Am\u00e9m"},
#                                 "chords": {"chordStr": ""},
#                             }
#                         ]
#                     },
#                     {
#                         "sequenceList": [
#                             {
#                                 "lyrics": {"lyrics": "Am\u00e9m"},
#                                 "chords": {"chordStr": ""},
#                             }
#                         ]
#                     },
#                     {
#                         "sequenceList": [
#                             {
#                                 "lyrics": {"lyrics": "Am\u00e9m, Am\u00e9m"},
#                                 "chords": {"chordStr": ""},
#                             }
#                         ]
#                     },
#                     {
#                         "sequenceList": [
#                             {
#                                 "lyrics": {"lyrics": "Am\u00e9m"},
#                                 "chords": {"chordStr": ""},
#                             }
#                         ]
#                     },
#                 ],
#                 "abreviation": "R",
#             },
#             {
#                 "repetition": 1,
#                 "name": "Verso",
#                 "lineList": [
#                     {
#                         "sequenceList": [
#                             {
#                                 "lyrics": {"lyrics": "Que o Senhor te  Aben\u00e7oe"},
#                                 "chords": {"chordStr": ""},
#                             }
#                         ]
#                     },
#                     {
#                         "sequenceList": [
#                             {
#                                 "lyrics": {
#                                     "lyrics": "E fa\u00e7a Brilhar seu rosto em Ti"
#                                 },
#                                 "chords": {"chordStr": ""},
#                             }
#                         ]
#                     },
#                     {
#                         "sequenceList": [
#                             {
#                                 "lyrics": {"lyrics": "Que conceda  sua gra\u00e7a"},
#                                 "chords": {"chordStr": ""},
#                             }
#                         ]
#                     },
#                     {
#                         "sequenceList": [
#                             {
#                                 "lyrics": {"lyrics": "E te d\u00ea Paz"},
#                                 "chords": {"chordStr": ""},
#                             }
#                         ]
#                     },
#                 ],
#                 "abreviation": "V",
#             },
#             {
#                 "repetition": 1,
#                 "name": "Refr\u00e3o",
#                 "lineList": [
#                     {
#                         "sequenceList": [
#                             {
#                                 "lyrics": {"lyrics": "Am\u00e9m, Am\u00e9m"},
#                                 "chords": {"chordStr": ""},
#                             }
#                         ]
#                     },
#                     {
#                         "sequenceList": [
#                             {
#                                 "lyrics": {"lyrics": "Am\u00e9m"},
#                                 "chords": {"chordStr": ""},
#                             }
#                         ]
#                     },
#                     {
#                         "sequenceList": [
#                             {
#                                 "lyrics": {"lyrics": "Am\u00e9m, Am\u00e9m"},
#                                 "chords": {"chordStr": ""},
#                             }
#                         ]
#                     },
#                     {
#                         "sequenceList": [
#                             {
#                                 "lyrics": {"lyrics": "Am\u00e9m"},
#                                 "chords": {"chordStr": ""},
#                             }
#                         ]
#                     },
#                 ],
#                 "abreviation": "R",
#             },
#             {
#                 "repetition": 1,
#                 "name": "Ponte",
#                 "lineList": [
#                     {
#                         "sequenceList": [
#                             {
#                                 "lyrics": {
#                                     "lyrics": "Que a ben\u00e7\u00e3o se derrame"
#                                 },
#                                 "chords": {"chordStr": ""},
#                             }
#                         ]
#                     },
#                     {
#                         "sequenceList": [
#                             {
#                                 "lyrics": {"lyrics": "At\u00e9 mil gera\u00e7\u00f5es"},
#                                 "chords": {"chordStr": ""},
#                             }
#                         ]
#                     },
#                     {
#                         "sequenceList": [
#                             {
#                                 "lyrics": {"lyrics": "Tua familia e teus filhos"},
#                                 "chords": {"chordStr": ""},
#                             }
#                         ]
#                     },
#                     {
#                         "sequenceList": [
#                             {
#                                 "lyrics": {"lyrics": "E os filhos de teus filhos."},
#                                 "chords": {"chordStr": ""},
#                             }
#                         ]
#                     },
#                 ],
#                 "abreviation": "P",
#             },
#             {
#                 "repetition": 1,
#                 "name": "Ponte 2",
#                 "lineList": [
#                     {
#                         "sequenceList": [
#                             {
#                                 "lyrics": {"lyrics": "Sua Presen\u00e7a te acompanhe"},
#                                 "chords": {"chordStr": ""},
#                             }
#                         ]
#                     },
#                     {
#                         "sequenceList": [
#                             {
#                                 "lyrics": {"lyrics": "Por detr\u00e1s e por diante"},
#                                 "chords": {"chordStr": ""},
#                             }
#                         ]
#                     },
#                     {
#                         "sequenceList": [
#                             {
#                                 "lyrics": {"lyrics": "Do Teu Lado e Em Ti"},
#                                 "chords": {"chordStr": ""},
#                             }
#                         ]
#                     },
#                     {
#                         "sequenceList": [
#                             {
#                                 "lyrics": {"lyrics": "\u00c9 Contigo, \u00c9 em Ti"},
#                                 "chords": {"chordStr": ""},
#                             }
#                         ]
#                     },
#                 ],
#                 "abreviation": "P2",
#             },
#             {
#                 "repetition": 1,
#                 "name": "Ponte 3",
#                 "lineList": [
#                     {
#                         "sequenceList": [
#                             {
#                                 "lyrics": {"lyrics": "E de noite e de dia"},
#                                 "chords": {"chordStr": ""},
#                             }
#                         ]
#                     },
#                     {
#                         "sequenceList": [
#                             {
#                                 "lyrics": {"lyrics": "Tua entrada e sa\u00edda"},
#                                 "chords": {"chordStr": ""},
#                             }
#                         ]
#                     },
#                     {
#                         "sequenceList": [
#                             {
#                                 "lyrics": {"lyrics": "Em teu riso, em teu choro"},
#                                 "chords": {"chordStr": ""},
#                             }
#                         ]
#                     },
#                     {
#                         "sequenceList": [
#                             {
#                                 "lyrics": {"lyrics": "\u00c9 contigo, \u00c9 por Ti."},
#                                 "chords": {"chordStr": ""},
#                             }
#                         ]
#                     },
#                 ],
#                 "abreviation": "P3",
#             },
#             {
#                 "repetition": 1,
#                 "name": "Repete",
#                 "lineList": [
#                     {
#                         "sequenceList": [
#                             {
#                                 "lyrics": {"lyrics": "\u00c9 contigo, \u00c9 por Ti."},
#                                 "chords": {"chordStr": ""},
#                             }
#                         ]
#                     }
#                 ],
#                 "abreviation": "Re",
#             },
#             {
#                 "repetition": 1,
#                 "name": "Refr\u00e3o",
#                 "lineList": [
#                     {
#                         "sequenceList": [
#                             {
#                                 "lyrics": {"lyrics": "Am\u00e9m, Am\u00e9m"},
#                                 "chords": {"chordStr": ""},
#                             }
#                         ]
#                     },
#                     {
#                         "sequenceList": [
#                             {
#                                 "lyrics": {"lyrics": "Am\u00e9m"},
#                                 "chords": {"chordStr": ""},
#                             }
#                         ]
#                     },
#                     {
#                         "sequenceList": [
#                             {
#                                 "lyrics": {"lyrics": "Am\u00e9m, Am\u00e9m"},
#                                 "chords": {"chordStr": ""},
#                             }
#                         ]
#                     },
#                     {
#                         "sequenceList": [
#                             {
#                                 "lyrics": {"lyrics": "Am\u00e9m"},
#                                 "chords": {"chordStr": ""},
#                             }
#                         ]
#                     },
#                 ],
#                 "abreviation": "R",
#             },
#             {
#                 "repetition": 1,
#                 "name": "Ponte",
#                 "lineList": [
#                     {
#                         "sequenceList": [
#                             {
#                                 "lyrics": {
#                                     "lyrics": "Que a ben\u00e7\u00e3o se derrame"
#                                 },
#                                 "chords": {"chordStr": ""},
#                             }
#                         ]
#                     },
#                     {
#                         "sequenceList": [
#                             {
#                                 "lyrics": {"lyrics": "At\u00e9 mil gera\u00e7\u00f5es"},
#                                 "chords": {"chordStr": ""},
#                             }
#                         ]
#                     },
#                     {
#                         "sequenceList": [
#                             {
#                                 "lyrics": {"lyrics": "Tua familia e teus filhos"},
#                                 "chords": {"chordStr": ""},
#                             }
#                         ]
#                     },
#                     {
#                         "sequenceList": [
#                             {
#                                 "lyrics": {"lyrics": "E os filhos de teus filhos."},
#                                 "chords": {"chordStr": ""},
#                             }
#                         ]
#                     },
#                 ],
#                 "abreviation": "P",
#             },
#             {
#                 "repetition": 1,
#                 "name": "Ponte 2",
#                 "lineList": [
#                     {
#                         "sequenceList": [
#                             {
#                                 "lyrics": {"lyrics": "Sua Presen\u00e7a te acompanhe"},
#                                 "chords": {"chordStr": ""},
#                             }
#                         ]
#                     },
#                     {
#                         "sequenceList": [
#                             {
#                                 "lyrics": {"lyrics": "Por detr\u00e1s e por diante"},
#                                 "chords": {"chordStr": ""},
#                             }
#                         ]
#                     },
#                     {
#                         "sequenceList": [
#                             {
#                                 "lyrics": {"lyrics": "Do Teu Lado e Em Ti"},
#                                 "chords": {"chordStr": ""},
#                             }
#                         ]
#                     },
#                     {
#                         "sequenceList": [
#                             {
#                                 "lyrics": {"lyrics": "\u00c9 Contigo, \u00c9 em Ti"},
#                                 "chords": {"chordStr": ""},
#                             }
#                         ]
#                     },
#                 ],
#                 "abreviation": "P2",
#             },
#             {
#                 "repetition": 1,
#                 "name": "Ponte 3",
#                 "lineList": [
#                     {
#                         "sequenceList": [
#                             {
#                                 "lyrics": {"lyrics": "E de noite e de dia"},
#                                 "chords": {"chordStr": ""},
#                             }
#                         ]
#                     },
#                     {
#                         "sequenceList": [
#                             {
#                                 "lyrics": {"lyrics": "Tua entrada e sa\u00edda"},
#                                 "chords": {"chordStr": ""},
#                             }
#                         ]
#                     },
#                     {
#                         "sequenceList": [
#                             {
#                                 "lyrics": {"lyrics": "Em teu riso, em teu choro"},
#                                 "chords": {"chordStr": ""},
#                             }
#                         ]
#                     },
#                     {
#                         "sequenceList": [
#                             {
#                                 "lyrics": {"lyrics": "\u00c9 contigo, \u00c9 por Ti."},
#                                 "chords": {"chordStr": ""},
#                             }
#                         ]
#                     },
#                 ],
#                 "abreviation": "P3",
#             },
#             {
#                 "repetition": 1,
#                 "name": "Repete",
#                 "lineList": [
#                     {
#                         "sequenceList": [
#                             {
#                                 "lyrics": {"lyrics": "\u00c9 contigo, \u00c9 por Ti."},
#                                 "chords": {"chordStr": ""},
#                             }
#                         ]
#                     }
#                 ],
#                 "abreviation": "Re",
#             },
#             {
#                 "repetition": 1,
#                 "name": "Refr\u00e3o",
#                 "lineList": [
#                     {
#                         "sequenceList": [
#                             {
#                                 "lyrics": {"lyrics": "Am\u00e9m, Am\u00e9m"},
#                                 "chords": {"chordStr": ""},
#                             }
#                         ]
#                     },
#                     {
#                         "sequenceList": [
#                             {
#                                 "lyrics": {"lyrics": "Am\u00e9m"},
#                                 "chords": {"chordStr": ""},
#                             }
#                         ]
#                     },
#                     {
#                         "sequenceList": [
#                             {
#                                 "lyrics": {"lyrics": "Am\u00e9m, Am\u00e9m"},
#                                 "chords": {"chordStr": ""},
#                             }
#                         ]
#                     },
#                     {
#                         "sequenceList": [
#                             {
#                                 "lyrics": {"lyrics": "Am\u00e9m"},
#                                 "chords": {"chordStr": ""},
#                             }
#                         ]
#                     },
#                 ],
#                 "abreviation": "R",
#             },
#         ],
#     },
# }

# resumeMap = [
#     {"name": item[0], "abreviation": item[1], "repetition": item[2]}
#     for item in teste["resumeMap"]
# ]

# mapping = teste["map"]
# print(mapping["regionList"][0]["name"])
# for item in resumeMap:
#     if len(mapping["regionList"]) > 0:
#         if (
#             item["name"] == mapping["regionList"][0]["name"]
#             and item["abreviation"] == mapping["regionList"][0]["abreviation"]
#         ):
#             item["lineList"] = mapping["regionList"][0]["lineList"]
#             mapping["regionList"].pop(0)

# from json import dumps

# print(dumps(resumeMap))

# teste = Music()

# print(teste.__dict__)
