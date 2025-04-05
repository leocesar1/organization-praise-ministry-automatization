import asyncio
import telebot


from default.default import get_Credentials, Metaclass


class TelegramBot(metaclass=Metaclass):
    def __init__(self, token=None):
        self.getDefaultsValues = get_Credentials("telegram")["telegram"]
        self.token = (
            token
            if token is not None
            else self.getDefaultsValues["token"]["praiseMinistryBot"]
        )
        self.bot = telebot.TeleBot(self.token, parse_mode="MarkdownV2", num_threads=1)
        self.setChatId(self.getDefaultsValues["chat_id"])
        self.setTopicId(self.getDefaultsValues["message_thread_id"])

    def setChatId(self, chat_id=None):
        self._chatId = chat_id if chat_id is not None else None

    def setTopicId(self, topic_id=None):
        self._topicId = topic_id if topic_id is not None else None

    def sendFile(self, content: bytes, details: dict):
        # details = self.getAudioDetails(folderName=folderName)
        caption = self.makeNewCaption(details)
        # print(caption)
        result = self.bot.send_document(
            self._chatId,
            visible_file_name=details["name"] + ".html",
            caption=caption,
            document=content,
            timeout=400,
            message_thread_id=self._topicId,
        )
        # print(result)

        return result.message_id

    def sendMultiplesAudios(self, folderName=None, files=[]):
        # self.setTopicId(self.getDefaultsValues["message_thread_id"])
        audioFiles = []
        contador = 1

        for item in files:
            for key, value in item.items():
                details = self.getAudioDetails(
                    folderName=folderName, fileName=key.replace("+", r"\+")
                )

            caption = None if contador != 1 else self.makeCaption(details)
            # print(caption)

            audioFiles.append(
                self.makeInputMediaAudio(
                    value,
                    caption=caption,
                    title=details["title"],
                    artist=details["artist"],
                )
            )
            # print(audioFiles)
            contador += 1
        try:
            result = self.bot.send_media_group(
                self._chatId, media=audioFiles, timeout=900000, message_thread_id=self._topicId
            )
        except:
            for item in audioFiles:
                result = self.bot.send_media_group(
                self._chatId, media=[item], timeout=900000, message_thread_id=self._topicId
            )

        # print(result)

        return result[0].message_id

    def makeCaption(self, details={}):
        return f""" 
🎶 Música: *{details["music"]}*
🎤 Intérprete: *{details["artist"]}*
🎼 Tom Original: *{details["key"]}* 
⏳ Andamento: *{details["time"]}*


"""

    def makeNewCaption(self, details={}):
        for key, value in details.items():
            details[key] = (
                [
                    item.replace(".", "\.").replace("-", "\-").replace("+", "\+")
                    if isinstance(item, str)
                    else item
                    for item in value
                ]
                if isinstance(value, list)
                else str(value).replace(".", "\.").replace("-", "\-").replace("+", "\+")
                if not isinstance(value, dict)
                else value
            )

        return f""" 
🎶 Música: *{details["name"]}*
{'🎤 Intérprete: *'+ str(chr(92)+'''
                         ''').join(details["singer"])+'*'if 'singer' in details.keys() else ''}
🎼 Tom Original: *{details["key"]}* 
⏳ Andamento: *{details["bpm"]}*
{'📕 Escrituras: *' + str(chr(92)+'''
                         ''').join(details["scriptures"] if isinstance(details["scriptures"],list) else [details["scriptures"]] )+'*' if 'scriptures' in details.keys() else ''} 
{'📅 Ano: *' + details["year"]+'*' if "year" in details.keys() else '' }
{'⏱ Duração: *' + details["duration"]+'*' if "year" in details.keys() else ''}
{' '.join([chr(92)+"#"+item for item in details['theme']]) if "theme" in details.keys() else ''}
"""

    def getAudioDetails(self, folderName=None, fileName=None):
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
            .replace("_", "\_")
            .replace(".", ",")
            .replace("--", "+")
            .replace("+", "e")
            .replace("[ELITE]", "")
            .split("-")
        )

        musica = array[0]
        if len(array) >= 5:
            if len(array[1]) > len(array[2]):
                artista = array[1]  # .replace("+", "e")
                tom = array[2]
            else:
                artista = array[2]  # .replace("+", "e")
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

    def makeInputMediaAudio(self, content, caption=None, title=None, artist=None):
        return telebot.types.InputMediaAudio(
            media=content,
            title=title,
            caption=caption,
            performer=artist,
            parse_mode="MarkdownV2",
        )

    def updateCaption(self, messageId, newCaption):
        try:
            # return self.bot.copy_message(chat_id=self._chatId, from_chat_id=self._chatId, message_id = messageId)
            teste = telebot.types.MessageEntity(type="hashtag", offset=4, length=10)
            self.bot.edit_message_caption(
                caption=newCaption,
                chat_id=self._chatId,
                message_id=messageId,
                caption_entities=[teste],
            )
            # print(msg.text)
            msg = "done"
        except:
            msg = "not updated"
        return msg

    def makeMap(self, folderName="", fileName="", array=[]):
        result = self.getAudioDetails(fileName=fileName)
        text = self.makeCaption(result) + "*MAPA*\n\n"
        text += "\n".join(array)

        return text.replace(".", "")

    def sendMap(self, folderName="", fileName="", array=[]):
        self.setTopicId(652)
        text = self.makeMap(fileName=fileName, array=array)
        result = self.bot.send_message(
            self._chatId,
            text=text,
            parse_mode="Markdownv2",
            message_thread_id=self._topicId,
        )

        return result
