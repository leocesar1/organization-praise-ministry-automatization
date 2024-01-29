from onedrive.manager import OneDrive

from telegram.manager import TelegramBot
from googleConnection.manager import GoogleSheet
from json import loads, dumps, load, dump
from requests import get
from sys import stdout
from tqdm import tqdm

stdout.reconfigure(encoding="utf-8")

onedrive = OneDrive()
bot = TelegramBot()
bot.setTopicId(bot.getDefaultsValues["message_thread_id"])

lista = onedrive.getFileList()


with open("message/sucessos.json", "r", encoding="utf-8") as file:
    successList = load(file)["data"]

erros = []
sucessos = []
for i in tqdm(range(len(lista))):
    item = lista[i]
    try:
        # if True:
        if "file" not in item.keys() and item["name"] not in successList.keys():
            name = item["name"]  # .encode("utf-8")#.decode("utf-8"))
            folder = item["id"]
            url = f"https://graph.microsoft.com/v1.0/drives/a9bcf86e0d3403c2/items/{folder}/children"

            getFolder = loads(get(url, headers=onedrive.HEADERS).text)["value"]
            getFolder = [i for i in getFolder if i["name"] == "1 - Renders"][0]["id"]
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
            sucessos.append(bot.sendMultiplesAudios(name, downloadList))

    except Exception as errorDetails:
        print(errorDetails)

        erros.append(name)

print("quantidade de erros = " + str(len(erros)))
print("erros = " + str(erros))
erros = {"data": erros}
json_object = dumps(erros, indent=4)
with open("erros.json", "w", encoding="utf-8") as file:
    file.write(json_object)

print("quantidade de sucessos = " + str(len(sucessos)))
print("sucessos = " + str(sucessos))


with open("message/sucessos.json", "r", encoding="utf-8") as file:
    sucessosNew = load(file)

for item in sucessos:
    for key, value in item.items():
        sucessosNew["data"][key] = value

json_object = dumps(sucessosNew, indent=4)
with open("message/sucessos.json", "w", encoding="utf-8") as file:
    file.write(json_object)

# sheet = GoogleSheet()
# detailsOfCategories = sheet.getAllMusicDetails()

# for key, value in detailsOfCategories.items():
#     # pega id da mensagem
#     id = sucessosNew["data"][key]
#     # print(id)
#     # monta novo caption

#     newCaption = bot.makeCaption(bot.getAudioDetails(key)) + f"{value}"
#     # print(newCaption)
#     # inclui detalhes (value)
#     print(bot.updateCaption(id, newCaption))

# # print(detailsOfCategories)

# print(sucessosNew["data"].keys())
