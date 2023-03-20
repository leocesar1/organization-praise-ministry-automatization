import asyncio
import telebot


from default.default import get_Credentials, Metaclass


class TelegramBot(metaclass=Metaclass):

    def __init__(self, token=None):
        getDefaultsValues = get_Credentials("telegram")["telegram"]
        self.token = token if token is not None else getDefaultsValues[
            "token"]["praiseMinistryBot"]
        self.bot = telebot.TeleBot(
            self.token, parse_mode="MarkdownV2", num_threads=10)
        self.setChatId(getDefaultsValues["chat_id"])
        self.setTopicId(getDefaultsValues["message_thread_id"])

    def setChatId(self, chat_id=None):
        self._chatId = chat_id if chat_id is not None else None

    def setTopicId(self, topic_id=None):
        self._topicId = topic_id if topic_id is not None else None

    def sendMultiplesAudios(self, folderName=None, files=[]):
        audioFiles = []
        contador = 1

        for item in files:
            for key, value in item.items():

                details = self.getAudioDetails(
                    folderName=folderName, fileName=key)

            caption = None if contador != 1 else self.makeCaption(details)

            audioFiles.append(self.makeInputMediaAudio(
                value, caption=caption, title=details["title"], artist=details["artist"]))

            contador += 1
        result = self.bot.send_media_group(
            self._chatId, media=audioFiles, timeout=400, message_thread_id=self._topicId)

        return {f"{folderName}": result[0].message_id}

    def makeCaption(self, details={}):
        return f""" 
🎶 Música: *{details["music"]}*
🎤 Intérprete: *{details["artist"]}*
🎼 Tom Original: *{details["key"]}* 
⏳ Andamento: *{details["time"]}*


"""

    def getAudioDetails(self, folderName=None, fileName=None):
        fileName ='' if fileName is None else fileName
        if len(fileName) > 12:
            array = fileName
        else:
            array = folderName

        array = array.replace('.rpp', '').replace('&', 'E').replace('#', '\#').replace('.mp3', '').replace(')', ']').replace(
            '(', '[').replace('.', ',').replace('--', '+').replace('+', 'e').replace('[ELITE]', '').split('-')

        musica = array[0]
        if len(array) >= 5:
            if len(array[1]) > len(array[2]):
                artista = array[1].replace('+', 'e')
                tom = array[2]
            else:
                artista = array[2].replace('+', 'e')
                tom = array[1]
        else:
            if len(array[1]) <= len(array[2]) and len(array[1]) <= len(array[3]):
                tom = array[1]
                artista = array[2]+' e '+array[3]
            else:
                tom = array[3]
                artista = array[1]+' e '+array[2]
        tom = tom
        artista = artista

        andamento = array[-1].replace("4 1/", "4/").replace(
            "4 2/", "4/").replace("6 1/", "6/").replace("6 2/", "6/")
        andamento = ''.join(i for i in andamento if (
            i.isdigit() or i == ",")).replace(",", "/")
        andamento = (array[-2]+' '+andamento)

        title = (musica+array[-1]).replace(',', '')
        title = ''.join(i for i in title if not i.isdigit())

        result = {
            "music": musica,
            "artist": artista,
            "key": tom,
            "time": andamento,
            "title": title
        }

        return result

    def makeInputMediaAudio(self, content, caption=None, title=None, artist=None):
        return telebot.types.InputMediaAudio(media=content, title=title, caption=caption, performer=artist, parse_mode="MarkdownV2")

    def updateCaption(self,messageId, newCaption):
        try:
        # return self.bot.copy_message(chat_id=self._chatId, from_chat_id=self._chatId, message_id = messageId)
            teste = telebot.types.MessageEntity(type="hashtag", offset=4, length=10)
            self.bot.edit_message_caption(
                caption = newCaption, chat_id=self._chatId, message_id=messageId,caption_entities=[teste])
        # print(msg.text)
            msg = "done"
        except:
            msg = "not updated"
        return msg