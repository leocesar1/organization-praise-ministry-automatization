from json import load
import speech_recognition as sr


def get_Credentials(service="onedrive"):
    with open("credentials.json", "r") as credentials:
        credentials = load(credentials)

    return {f"{service}": credentials[service]}


class Metaclass(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Metaclass, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


# from pydub import AudioSegment
# from pydub.silence import split_on_silence
# import os

# class RecognizerParser(metaclass=Metaclass):
#     def __init__(self):
#         self._recognizer = sr.Recognizer()

#     def saveFile(self, contentFile):
#         with open('temp.wav', "wb") as file:
#             file.write(contentFile)

#     def getTextFromAudio(self, contentFile):
#         self.saveFile(contentFile)
#         return self.get_large_audio_transcription('temp.wav')

#     def get_large_audio_transcription(self, path):
#         """
#         Splitting the large audio file into chunks
#         and apply speech recognition on each of these chunks
#         """
#         # open the audio file using pydub
#         sound = AudioSegment.from_wav(path)
#         # split audio sound where silence is 700 miliseconds or more and get chunks
#         chunks = split_on_silence(sound,
#             # experiment with this value for your target audio file
#             min_silence_len = 700,
#             # adjust this per requirement
#             silence_thresh = sound.dBFS-14,
#             # keep the silence for 1 second, adjustable as well
#             keep_silence=500,
#         )
#         folder_name = "audio-chunks"
#         # create a directory to store the audio chunks
#         if not os.path.isdir(folder_name):
#             os.mkdir(folder_name)
#         whole_text = []
#         # process each chunk
#         for i, audio_chunk in enumerate(chunks, start=1):
#             # export audio chunk and save it in
#             # the `folder_name` directory.
#             chunk_filename = os.path.join(folder_name, f"chunk{i}.wav")
#             audio_chunk.export(chunk_filename, format="wav")
#             # recognize the chunk
#             with sr.AudioFile(chunk_filename) as source:
#                 audio_listened = self._recognizer.record(source)
#                 # try converting it to text
#                 try:
#                     text = self._recognizer.recognize_google(audio_listened)
#                 except sr.UnknownValueError as e:
#                     # print("Error:", str(e))
#                     whole_text.append("?????")
#                 else:
#                     text = f"{text.capitalize()}. "
#                     # print(chunk_filename, ":", text)
#                     whole_text.append(text)
#         # return the text for all chunks detected
#         return whole_text
