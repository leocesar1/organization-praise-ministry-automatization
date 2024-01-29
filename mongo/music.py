from datetime import datetime
from default.default import get_Credentials


class Time:
    # now = datetime.now().timestamp()
    # updatedAt = now
    # createdAt = now
    # del now

    def __init__(self):
        now = datetime.now().timestamp()
        self.updatedAt = now
        self.createdAt = now


class Music(Time):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

        makeRemoveList = list(self.__dict__)
        for item in makeRemoveList:
            self.__dict__.pop(item) if (
                item
                not in [
                    "_id",
                    "name",
                    "theme",
                    "genre",
                    "singer",
                    "duration",
                    "bpm",
                    "scriptures",
                    "key",
                    "compass",
                    "quality",
                    "oneDriveFolderId",
                    "hasMinistrationTime",
                    "year",
                    "elite",
                ]
                or self.__dict__[item] is None
            ) else ""
        super().__init__()


class Map(Time):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

        makeRemoveList = list(self.__dict__)
        for item in makeRemoveList:
            self.__dict__.pop(item) if (
                item not in ["_id", "musicId", "sequence", "nameMap"]
                or self.__dict__[item] is None
            ) else ""
        super().__init__()


class TelegramMongo(Time):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

        makeRemoveList = list(self.__dict__)
        for item in makeRemoveList:
            self.__dict__.pop(item) if (
                item not in ["_id", "musicId", "messageId", "topicId"]
                or self.__dict__[item] is None
            ) else ""

        if self.topicId == get_Credentials("telegram")["telegram"]["message_thread_id"]:
            self.type = "music"
        elif (
            self.topicId
            == get_Credentials("telegram")["telegram"]["message_thread_id_map"]
        ):
            self.type = "map"

        super().__init__()
        self._id = self.type + self._id
