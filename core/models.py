from dataclasses import dataclass

@dataclass
class MusicMetadata:
    name: str           # nome limpo da música
    artist: str         # artista(s)
    key: str            # tom (ex: "Bb", "D#m")
    bpm: float          # BPM numérico
    compass: str        # compasso normalizado (ex: "4/4", "6/8")
    elite: bool         # True se tiver [Elite] no nome
    instrument: str | None = None  # instrumento, se padrão B

@dataclass
class TelegramRecord:
    folder_id: str
    message_id: int
    music_name: str     # nome para ordenação alfabética
    arrangement_message_id: int | None = None

