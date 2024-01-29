from discord.ext import commands
import discord, os, io, re

from onedrive.manager import OneDrive

from json import loads, dumps, load, dump
from requests import get
from sys import stdout
from tqdm import tqdm

stdout.reconfigure(encoding="utf-8")

onedrive = OneDrive()

# creates a bot instance with "$" as the command prefix
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot("$", intents=intents)
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD = os.getenv("DISCORD_GUILD")
#       ^^^^^^^ FILL IN THIS! This is the generated token for your bot from the Discord Developer Page


@bot.command(pass_context=True)
async def clearAll(ctx):
    message_channel = ctx.message.channel

    async for msg in ctx.channel.history(limit=200):
        await msg.delete()


async def getHistoricChannel(channel):
    result = {}
    async for msg in channel.history(limit=500):
        result[re.sub(r"[^A-Za-z0-9]+", "", msg.content).upper()] = msg.id

    return result


async def deleteCommand(msg):
    if "$" not in msg.content:
        pass
    else:
        await msg.delete()


def getAudioDetails(folderName=None, fileName=None):
    # print(fileName)
    # print(folderName)
    fileName = "" if fileName is None else fileName
    if len(fileName) > 12:
        array = fileName
    else:
        array = folderName

    array = (
        array.replace(".rpp", "")
        .replace("&", "E")
        .replace("#", "\#")
        .replace(".mp3", "")
        .replace(")", "]")
        .replace("(", "[")
        .replace(".", ",")
        .replace("--", "+")
        .replace("+", "e")
        .replace("[ELITE]", "")
        .split("-")
    )

    musica = array[0]
    if len(array) >= 5:
        if len(array[1]) > len(array[2]):
            artista = array[1].replace("+", "e")
            tom = array[2]
        else:
            artista = array[2].replace("+", "e")
            tom = array[1]
    else:
        if len(array[1]) <= len(array[2]) and len(array[1]) <= len(array[3]):
            tom = array[1]
            artista = array[2] + " e " + array[3]
        else:
            tom = array[3]
            artista = array[1] + " e " + array[2]
    tom = tom
    artista = artista

    andamento = (
        array[-1]
        .replace("4 1/", "4/")
        .replace("4 2/", "4/")
        .replace("6 1/", "6/")
        .replace("6 2/", "6/")
    )
    andamento = "".join(i for i in andamento if (i.isdigit() or i == ",")).replace(
        ",", "/"
    )
    andamento = array[-2] + " " + andamento

    title = (musica + array[-1]).replace(",", "")
    title = "".join(i for i in title if not i.isdigit())

    result = {
        "music": musica,
        "artist": artista,
        "key": tom,
        "time": andamento,
        "title": title,
    }

    return result


def makeCaption(details={}):
    details = (
        {"music": "", "artist": "", "key": "", "time": ""} if not details else details
    )

    return f""" 
🎶 Música: **{details["music"]}**
🎤 Intérprete: **{details["artist"]}**
🎼 Tom Original: **{details["key"]}** 
⏳ Andamento: **{details["time"]}**


"""


@bot.command(pass_context=True)
async def update(
    ctx,
):
    message_author = ctx.message.author
    message_channel = ctx.channel

    # prints "<username> said hello" to the console
    print("{} said {}".format(message_author, ctx.message.content))

    # messages = await ctx.channel.history(limit=200)
    oldMessages = await getHistoricChannel(message_channel)

    async for msg in message_channel.history(limit=200):
        await deleteCommand(msg)

    # bot.send_message(...) is a coroutine, so it must be awaited
    # this sends a message "Hello, <username>!" to the message channel

    lista = onedrive.getFileList()

    # with open("message/sucessos.json", "r", encoding="utf-8") as file:
    #     successList = load(file)["data"]

    erros = []
    sucessos = []
    for i in tqdm(range(len(lista))):
        item = lista[i]
        name = item["name"]
        try:
            if (
                re.sub(
                    r"[^A-Za-z0-9]+", "", makeCaption(getAudioDetails("", name))
                ).upper()
                not in oldMessages.keys()
            ):
                # if "file" not in item.keys() and item["name"] not in successList.keys():
                # .encode("utf-8")#.decode("utf-8"))
                folder = item["id"]
                url = f"https://graph.microsoft.com/v1.0/drives/a9bcf86e0d3403c2/items/{folder}/children"

                getFolder = loads(get(url, headers=onedrive.HEADERS).text)["value"]
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

                    caption = value if len(value) > 11 else name
                    downloadList.append(
                        discord.File(
                            fp=io.BytesIO(download),
                            filename=caption,
                        )
                    )

                result = await ctx.send(
                    makeCaption(getAudioDetails("", name)),
                    files=downloadList,
                )
            else:
                print("Já enviado, falta atualizar")
                result = ""

            sucessos.append(result)

        except:
            erros.append(name)
    print(erros)


@bot.event
async def on_ready():  # the event `on_ready` is triggered when the bot is ready to function
    print("The bot is READY!")
    print("Logged in as: {}".format(bot.user.name))


# starts the bot with the corresponding token
bot.run(TOKEN)
