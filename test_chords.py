from services.onedrive import OneDriveClient
from core.reaper_parser import parse_rpp_chords

onedrive = OneDriveClient()
onedrive.authenticate()
file_list = onedrive.get_file_list()
for item in file_list:
    if "primeira essencia" in item.get("name", "").lower():
        name, content = onedrive.get_rpp_file(item["id"])
        text = content.decode("utf-8", errors="ignore")
        chords = parse_rpp_chords(text, 69.0)
        print("Chords extracted:", len(chords))
        print("Tracks with names:")
        for line in text.splitlines():
            if "NAME" in line and '"' in line:
                print(line.strip())
        break
