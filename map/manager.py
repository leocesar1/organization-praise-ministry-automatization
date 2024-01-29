from bs4 import BeautifulSoup
import bs4.element

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

import re


class Scraper:
    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(1)

    def close(self):
        self.driver.quit()

    def get_url(
        self,
        url="https://www.worshiptogether.com/songs/first-love-kari-jobe/#SongChords",
    ):
        self.driver.get(url)
        return self.driver.page_source

    def get_soap(
        self,
        url="https://www.worshiptogether.com/songs/first-love-kari-jobe/#SongChords",
    ):
        return BeautifulSoup(self.get_url(url), "html.parser")


class Sequence:
    def __init__(self, lyrics, chords):
        self.lyrics = Lyrics(lyrics)
        self.chords = Chords(chords)

    def __str__(self):
        return f"""<div class="chord-letter"><span class='chord'>{self.chords}</span>{self.lyrics}</div>"""


class Chords:
    def __init__(self, chords):
        self.chordStr = chords

    def __str__(self):
        return self.chordStr

    def __str__(self):
        if self.chordStr is None:
            return "&nbsp"
        return self.chordStr


class Lyrics:
    def __init__(self, lyrics):
        self.setLyrics(lyrics)

    def setLyrics(self, lyrics):
        self.lyrics = lyrics

    def __str__(self):
        if self.lyrics is None:
            return "&nbsp"
        return self.lyrics


class Line:
    def __init__(self, sequenceList=[]):
        self.sequenceList = []
        if isinstance(sequenceList, list):
            for sequence in sequenceList:
                self.append(sequence)

    def append(self, sequence):
        self.sequenceList.append(sequence)

    def __str__(self):
        return (
            '<div class="line">'
            + "\n".join([str(sequence) for sequence in self.sequenceList])
            + "</div>"
        )


class Region:
    repetitionMap = [
        r"[a-z]\d",
        r"\d[a-z]",
        # "repete",
        # "repetir",
        # "repeat",
        # "reptir",
        # "repitir",
    ]
    regionMap = {
        "repete": "Re",
        "intro": "I",
        "ponte 1": "P",
        "ponte 2": "P2",
        "ponte 3": "P3",
        "ponte 4": "P4",
        "ponte 5": "P5",
        "ponte": "P",
        "instrumental 1": "In",
        "instrumental 2": "In2",
        "instrumental 3": "In3",
        "instrumental 4": "In4",
        "instrumental 5": "In5",
        "instrumental": "In",
        "interlúdio 1": "It",
        "interlúdio 2": "It2",
        "interlúdio 3": "It3",
        "interlúdio 4": "It4",
        "interlúdio 5": "It5",
        "interlúdio": "It",
        "verso 1": "V",
        "verso 2": "V2",
        "verso 3": "V3",
        "verso 4": "V4",
        "verso 5": "V5",
        "verso": "V",
        "coro": "C",
        "coro 1": "C",
        "coro 2": "C2",
        "coro 3": "C3",
        "coro 4": "C4",
        "coro 5": "C5",
        "fim": "F",
        "final": "F",
        "pós-refrão": "Po",
        "pré-refrão": "Pr",
        "refrão": "R",
        "refrão 1": "R",
        "refrão 2": "R2",
        "refrão 3": "R3",
        "refrão 4": "R4",
        "refrão 5": "R5",
        "chorus": "C",
        "chorus 1": "C1",
        "chorus 2": "C2",
        "chorus 3": "C3",
        "chorus 4": "C4",
        "chorus 5": "C5",
        "tag": "Tg",
        "turnaround": "Tr",
        "vamp": "Va",
        "bridge 1": "B",
        "bridge 2": "B2",
        "bridge 3": "B3",
        "bridge 4": "B4",
        "bridge 5": "B5",
        "bridge": "B",
        "interlude 1": "It",
        "interlude 2": "It2",
        "interlude 3": "It3",
        "interlude 4": "It4",
        "interlude 5": "It5",
        "interlude": "It",
        "verse 1": "V",
        "verse 2": "V2",
        "verse 3": "V3",
        "verse 4": "V4",
        "verse 5": "V5",
        "verse": "V",
        "refrain": "R",
        "refrain 1": "R",
        "refrain 2": "R2",
        "refrain 3": "R3",
        "refrain 4": "R4",
        "refrain 5": "R5",
        "outro": "O",
    }

    def __init__(self, name="Region", lineList=[], repetition=None):
        self.setRepetition(
            repetition
        ) if repetition is not None else self.setRepetition(1)
        self.setName(name)
        self.lineList = []
        if isinstance(lineList, list):
            for line in lineList:
                self.append(line)
        self.treatRegion()

    def getResume(self):
        return (self.name, self.abreviation, self.repetition)

    def treatRegion(self):
        self.setRepetition(self.makeRepetitionNumber())
        self.clearName()
        self.makeRealNameAndAbreviation()

    def makeRealNameAndAbreviation(self):
        # if self.name.strip().lower() in self.regionMap.keys():
        self.setName(self.name.lower().capitalize())
        abrev = self.name.strip().lower()[0:2].capitalize()

        import string
        from unidecode import unidecode

        allowed_chars = string.ascii_letters + string.digits
        tempName = ""
        for letter in unidecode(self.name.strip().lower()):
            if letter in allowed_chars:
                tempName += letter
        for key, value in self.regionMap.items():
            if tempName == unidecode(key.lower().replace(" ", "").replace("-", "")):
                abrev = value

        self.setAbreviation(abrev)

    def setAbreviation(self, abrev):
        self.abreviation = abrev

    def setRepetition(self, repetition):
        self.repetition = repetition

    def makeRepetitionNumber(self):
        repetition = self.repetition
        if any(
            [
                re.search(item, self.name.strip().lower()) is not None
                for item in self.repetitionMap
            ]
        ):
            test = re.search(r"(\dx|x\d)", self.name.lower())
            if test is None:
                repetition = self.repetition
            else:
                repetition = re.search(r"\d", test.group()).group()
        return repetition

    def clearName(self):
        for item in self.repetitionMap:
            self.setName(re.sub(item, "", self.name.lower().strip()))
        self.setName(re.sub("1", "", self.name.lower().strip()).strip())

    def setName(self, name: str):
        self.name = name

    def append(self, sequence):
        self.lineList.append(sequence)

    def __str__(self):
        return (
            f'<fieldset  class="region column"> <legend><span class="region-title-abrev">{self.abreviation}</span><span class="region-title">{self.name}</span></legend><br>'
            + "".join([str(line) for line in self.lineList if len(self.lineList) > 0])
            + "</fieldset >"
        )

    def __repr__(self):
        return self.lineList


class MapMusic:
    def __init__(self, name="", regionList=[]):
        self.setName(name)
        self.regionList = []
        if isinstance(regionList, list):
            for region in regionList:
                self.append(region)

    def getResumeList(self):
        return [item.getResume() for item in self.regionList]

    def setName(self, name: str):
        self.name = name
        """
        region
        lines
        lyrics + chords
        """

    def append(self, region):
        self.regionList.append(region)

    def __str__(self):
        return "".join(
            [str(region) for region in self.regionList if len(region.lineList) > 0]
        )


class MultitracksScraper(Scraper):
    def __init__(
        self,
        url="https://www.multitracks.com.br/songs/Morada/Lembre-se-2000's/Diante-de-Ti/",
    ):
        super().__init__()
        self.getContent = super().get_url(url)
        self.url = url
        self.soap = self.get_soap()
        self.getMap()

    def get_soap(self):
        return super().get_soap(self.url)

    def getMap(self):
        self.mapMusic = MapMusic(self.getTitle())
        regions = self.soap.find_all("div", class_="section-expand--block")

        for region in regions:
            lines = region.find_all("p")
            for line in lines:
                if line.find("strong") is not None:
                    regionName = line.find("strong").get_text()
                else:
                    lyricsList = [
                        str(elem)
                        for elem in line.contents
                        if not isinstance(elem, bs4.element.Tag)
                    ]
                    lineList = [
                        Line(sequenceList=[Sequence(lyrics=lyric, chords="")])
                        for lyric in lyricsList
                    ]
            region = Region(name=regionName, lineList=lineList)
            self.mapMusic.append(region)

    def getTitle(self):
        return self.soap.find("h1", class_="song-banner--title").get_text()

    def getSinger(self):
        musicName = self.getTitle()
        step1 = self.soap.find("h2", class_="song-banner--artist")
        # print(step1)

        artists = step1.find_all("a")
        # print(artists)

        return [
            item.get_text()
            for item in artists
            if item.get_text().strip() != musicName.strip()
        ]

    def getDetails(self):
        response = {}
        findDetails = self.soap.find_all("div", class_="song-banner--meta-list--group")
        for item in findDetails:
            name = (
                item.find("dt", class_="song-banner--meta-list--term")
                .get_text()
                .replace("\n", "")
                .replace(":", "")
                .replace("\t", "")
                .replace(r"\n", "")
                .replace(r":", "")
                .replace(r"\t", "")
            )
            content = [
                x
                for x in (
                    item.find("dd", class_="song-banner--meta-list--desc")
                    .get_text()
                    .replace("\t", "")
                    .split("\n")
                )
                if x
            ]
            if len(content) > 0:
                response[name] = content if len(content) > 1 else content[0]

        findDetails = self.soap.find("dl", class_="song-details--meta-list")
        names = findDetails.find_all("dt", class_="song-details--meta-list--term")
        contents = findDetails.find_all("dd", class_="song-details--meta-list--desc")
        for item in range(0, len(contents)):
            name = (
                names[item]
                .get_text()
                .replace("\n", "")
                .replace(":", "")
                .replace("\t", "")
                .replace(r"\n", "")
                .replace(r":", "")
                .replace(r"\t", "")
            )
            content = [
                x for x in contents[item].get_text().replace("\t", "").split("\n") if x
            ]
            if len(content) > 0:
                response[name] = content if len(content) > 1 else content[0]

        return response


class MapFile:
    def __init__(self, **informations):
        self.setTitle(informations["name"])
        self.setSequence(informations["sequence"])
        self.setSinger(informations["singer"])
        self.setDetails(**informations)
        self.setRegionList(informations["sequence"])
        # [print(item) for item in self.regionList]

    def setSinger(self, singer):
        self.singer = singer

    def setRegionList(self, sequence):
        self.regionList = [
            Region(
                name=region["name"],
                lineList=[]
                if "lineList" not in region.keys()
                else [
                    Line(
                        sequenceList=[
                            Sequence(
                                lyrics=s["lyrics"]["lyrics"],
                                chords=s["chords"]["chordStr"],
                            )
                            for s in line["sequenceList"]
                        ]
                    )
                    for line in region["lineList"]
                ],
                repetition=region["repetition"],
            )
            for region in sequence
        ]

    def setDetails(self, **details):
        itemList = ["bpm", "compass", "key", "duration", "year", "scripture"]
        removeList = [
            key
            for key, value in details.items()
            if key not in itemList and key in details.keys()
        ]
        [details.pop(item) for item in removeList]
        self.details = details

    def getDetails(self):
        return self.details

    def getSinger(self):
        return self.singer

    def setTitle(self, title):
        self.title = title

    def getTitle(self):
        return self.title

    def setSequence(self, sequence):
        self.sequence = sequence

    def getSequence(self):
        return self.sequence

    def getScripts(self):
        return """ 
<script>
    var coll = document.getElementsByClassName("collapsible");
    var i;

    for (i = 0; i < coll.length; i++) {
      coll[i].addEventListener("click", function () {
        this.classList.toggle("active");
        var content = this.nextElementSibling;
        if (content.style.maxHeight) {
          content.style.maxHeight = null;
        } else {
          content.style.maxHeight = content.scrollHeight + "px";
        }
      });
    }
  </script>
"""

    def getStyle(self):
        return """
<style>
  h1 {
    font-family: "Ubuntu", sans-serif;
  }
  .info {
    border-radius: 1% 1%;
    background-color: #f1f1f1;
  }
  .info.legend {
    background-color: none;
  }
  .title {
    color: black;
    text-align: center;
    margin: 25px;
  }
  h2 {
  }
  fieldset {
    height: auto;
  }
  .subtitle {
    font-size: 30px;
    color: black;
    text-align: center;
    margin: -25px 0 50px 0px;
    font-style: italic;
    font-weight: normal;
  }
  body {
    padding: 20px;
    font-size: 30px;
    margin: 50px;
    font-family: "Lora", serif;
  }
  .content {
    position: relative;
    margin: auto;
    justify-content: center;
  }
  .region {
    margin-top: 30px;
    justify-content: center;
    margin-bottom: 30px;
    max-width: 95%;
    border: 1px black solid;
    border-radius: 0.4em;
  }
  .region-title {
    margin-left: 0.1em;
    padding: 0.5em 0.1em;
    color: black;
    background-color: #f1f1f1;
  }
  .region-title-abrev {
    background-color: rgb(0, 0, 0);
    color: white;
    font: bold 18px/16px Helvetica, Verdana, Tahoma;
    width: 40px;
    height: 40px;
    border: none;
    border-radius: 50%;
    margin-left: 0.6em;
    text-align: center;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 5px 5px;
  }
  .line {
    display: flex;
    align-items: flex-end;
    flex-wrap: wrap;
  }
  .chord-letter {
    display: flex;
    flex-direction: column;
    padding: 0 5px;
    align-items: center;
  }
  .chord {
    font-style: italic;
    font-weight: bold;
    font-size: 25px;
    color: rgb(0, 0, 118);
  }
  .theme-table {
    font: bold 15px/13px "Ubuntu", sans-serif;
  }
  .map {
    line-height: 1.2em;
    overflow-wrap: break-word;
    display: flex;
    flex-wrap: wrap;
    align-items: flex-start;
    row-gap: 10px;
    align-content: space-between;
  }
  .theme-column {
    line-height: 1.2em;
    display: -webkit-flex;
    display: -moz-flex;
    display: -ms-flex;
    display: -o-flex;
    display: flex;
    justify-content: space-around;
  }
  .theme-column-text {
    line-height: 1.2em;
    display: -webkit-flex;
    display: -moz-flex;
    display: -ms-flex;
    display: -o-flex;
    display: flex;
    justify-content: space-around;
    flex-direction: column;
  }
  .theme-values {
    border-radius: 20px;
    background-color: rgb(78, 87, 79);
    margin-right: 5px;
    color: white;
    font: bold 12px/10px Helvetica, Verdana, Tahoma;
    /* min-width: 14px; */
    padding: 4px 5px 6px 5px;
    text-align: center;
  }
  .map-values {
    position: relative;
    background-color: rgb(0, 0, 0);
    color: white;
    font: bold 18px/16px Helvetica, Verdana, Tahoma;
    width: 40px;
    height: 40px;
    border: none;
    border-radius: 50%;
    margin-right: 10px;
    text-align: center;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 5px 5px;
  }

  .map-values-legend {
    position: absolute;
    top: 0;
    right: 0;
    border: 2px solid rgb(0, 0, 0);
    background-color: rgb(255, 255, 255);
    color: rgb(7, 7, 7);
    font: bold 13px/10px Ubuntu, Verdana, Tahoma;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;

    margin: auto;
    width: 16px;
    height: 16px;
    text-align: center;
  }
  .collapsible {
    cursor: pointer;
    background-color: rgb(1, 84, 1);
    border: 2px solid white;
    border-radius: 12px; /* one half of ( (border * 2) + height + padding ) */
    box-shadow: 1px 1px 1px black;
    color: white;
    font: bold 15px/13px Helvetica, Verdana, Tahoma;
    height: 16px;
    min-width: 14px;
    padding: 4px 5px 3px 5px;
    text-align: center;
  }

  .collapsible:after {
    content: "+";
    background-color: rgb(1, 84, 1);
  }

  .active:after {
    content: "-";
    background-color: rgb(1, 84, 1);
  }

  .content-compress {
    max-height: 0;
    overflow: hidden;
    transition: max-height 0.2s ease-out;
    background-color: #f1f1f1;
  }

  .column {
    float: left;
    width: 100%;
    padding: 3px;
    margin: 1%;
  }

  .row:after {
    content: "";
    float: center;
    display: table;
    clear: both;
  }

  @media screen and (max-width: 700px) {
    .column {
      width: 98%;
    }
  }
</style>
"""

    def getHead(self):
        return f"""<head>
        <meta charset="UTF-8">
  <title>{self.getTitle()}</title>
</head>"""

    def getResumeMap(self):
        response = ""
        for mapElement in self.getSequence():
            response += (
                f'<div class="map-values" alt="{mapElement["name"].capitalize()}">'
            )
            if mapElement["repetition"] != 1:
                response += (
                    f'<div class="map-values-legend" >{mapElement["repetition"]}</div>'
                )
            response += f'<span>{mapElement["abreviation"]}</span></div>'
        return response

    # def getMiniMap(self):
    #     findMapList = self.soap.find(
    #         "span",
    #         id="songDetailsHeader_songMapContent",
    #     )
    #     return [
    #         Region(
    #             name=item.find(
    #                 "span",
    #                 class_="song-banner--tip",
    #             ).get_text(),
    #             repetition=int(item.attrs["data-repeat"])
    #             if "data-repeat" in item.attrs.keys()
    #             else None,
    #         ).getResume()
    #         for item in findMapList.children
    #     ]

    def makeFile(self):
        details = """<fieldset class="info">
    <legend align="right" class="legend collapsible active">
      Informações Gerais
    </legend>
    <div class="content-compress" style="max-height: 900000px;"><table class="theme-table"> """
        for key, value in self.getDetails().items():
            details += f"""
        <tr>
          <td>{key.capitalize()}</td>
          <td class="theme-column">{''.join(['<span class="theme-values">'+ item +'</span>' for item in value]) if isinstance(value,list) else value}</td>
        </tr>
"""
        details += "</table></div></fieldset>"
        return (
            """<!DOCTYPE html>
<html>"""
            + self.getStyle()
            + self.getHead()
            + f"""
        <body>
        <h1 class='title'>{self.getTitle()}</h1>
        <h2 class='subtitle'>{' - '.join(self.getSinger())}</h2>
        {details}<br>
        <fieldset class="info">
    <legend align="right" class="legend collapsible active">
      Mapa
    </legend>
    <div class="content-compress" style="max-height: 900000px;">
        <div class="content row"><div class="map">{self.getResumeMap()}</div></div></div>
        </fieldset><br><fieldset class="info">
    <legend align="right" class="legend collapsible active">
      Letra e Cifra
    </legend>
    <div class="content-compress" style="max-height: 900000px;">
        <div class="content row">{''.join([str(region)  for region in self.regionList])}</div></div>
        </fieldset>{self.getScripts()}
        </body></html>
        """
        )


class WorshiptogetherScraper(Scraper):
    def __init__(
        self,
        url="https://www.worshiptogether.com/songs/first-love-kari-jobe/#SongChords",
    ):
        super().__init__()
        self.getContent = super().get_url(url)
        self.url = url
        self.soap = self.get_soap()
        self.getMap()

    def get_soap(self):
        return super().get_soap(self.url)

    def getResumeMap(self):
        response = ""
        for mapElement in self.mapMusic.getResumeList():
            response += f'<div class="map-values" alt="{mapElement[0].capitalize()}">'
            if mapElement[2] != 1:
                response += f'<div class="map-values-legend" >{mapElement[2]}</div>'
            response += f"<span>{mapElement[1]}</span></div>"
        return response

    def getScripts(self):
        return """ 
<script>
    var coll = document.getElementsByClassName("collapsible");
    var i;

    for (i = 0; i < coll.length; i++) {
      coll[i].addEventListener("click", function () {
        this.classList.toggle("active");
        var content = this.nextElementSibling;
        if (content.style.maxHeight) {
          content.style.maxHeight = null;
        } else {
          content.style.maxHeight = content.scrollHeight + "px";
        }
      });
    }
  </script>
"""

    def getStyle(self):
        return """
<style>
  h1 {
    font-family: "Ubuntu", sans-serif;
  }
  .info {
    border-radius: 1% 1%;
    background-color: #f1f1f1;
  }
  .info.legend {
    background-color: none;
  }
  .title {
    color: black;
    text-align: center;
    margin: 25px;
  }
  h2 {
  }
  fieldset {
    height: auto;
  }
  .subtitle {
    font-size: 30px;
    color: black;
    text-align: center;
    margin: -25px 0 50px 0px;
    font-style: italic;
    font-weight: normal;
  }
  body {
    padding: 20px;
    font-size: 30px;
    margin: 50px;
    font-family: "Lora", serif;
  }
  .content {
    position: relative;
    margin: auto;
    justify-content: center;
  }
  .region {
    margin-top: 30px;
    justify-content: center;
    margin-bottom: 30px;
    max-width: 95%;
    border: 1px black solid;
    border-radius: 0.4em;
  }
  .region-title {
    margin-left: 0.1em;
    padding: 0.5em 0.1em;
    color: black;
    background-color: #f1f1f1;
  }
  .region-title-abrev {
    background-color: rgb(0, 0, 0);
    color: white;
    font: bold 18px/16px Helvetica, Verdana, Tahoma;
    width: 40px;
    height: 40px;
    border: none;
    border-radius: 50%;
    margin-left: 0.6em;
    text-align: center;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 5px 5px;
  }
  .line {
    display: flex;
    align-items: flex-end;
    flex-wrap: wrap;
  }
  .chord-letter {
    display: flex;
    flex-direction: column;
    padding: 0 5px;
    align-items: center;
  }
  .chord {
    font-style: italic;
    font-weight: bold;
    font-size: 25px;
    color: rgb(0, 0, 118);
  }
  .theme-table {
    font: bold 15px/13px "Ubuntu", sans-serif;
  }
  .map {
    line-height: 1.2em;
    overflow-wrap: break-word;
    display: flex;
    flex-wrap: wrap;
    align-items: flex-start;
    row-gap: 10px;
    align-content: space-between;
  }
  .theme-column {
    line-height: 1.2em;
    display: -webkit-flex;
    display: -moz-flex;
    display: -ms-flex;
    display: -o-flex;
    display: flex;
    justify-content: space-around;
  }
  .theme-column-text {
    line-height: 1.2em;
    display: -webkit-flex;
    display: -moz-flex;
    display: -ms-flex;
    display: -o-flex;
    display: flex;
    justify-content: space-around;
    flex-direction: column;
  }
  .theme-values {
    border-radius: 20px;
    background-color: rgb(78, 87, 79);
    margin-right: 5px;
    color: white;
    font: bold 12px/10px Helvetica, Verdana, Tahoma;
    /* min-width: 14px; */
    padding: 4px 5px 6px 5px;
    text-align: center;
  }
  .map-values {
    position: relative;
    background-color: rgb(0, 0, 0);
    color: white;
    font: bold 18px/16px Helvetica, Verdana, Tahoma;
    width: 40px;
    height: 40px;
    border: none;
    border-radius: 50%;
    margin-right: 10px;
    text-align: center;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 5px 5px;
  }

  .map-values-legend {
    position: absolute;
    top: 0;
    right: 0;
    border: 2px solid rgb(0, 0, 0);
    background-color: rgb(255, 255, 255);
    color: rgb(7, 7, 7);
    font: bold 13px/10px Ubuntu, Verdana, Tahoma;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;

    margin: auto;
    width: 16px;
    height: 16px;
    text-align: center;
  }
  .collapsible {
    cursor: pointer;
    background-color: rgb(1, 84, 1);
    border: 2px solid white;
    border-radius: 12px; /* one half of ( (border * 2) + height + padding ) */
    box-shadow: 1px 1px 1px black;
    color: white;
    font: bold 15px/13px Helvetica, Verdana, Tahoma;
    height: 16px;
    min-width: 14px;
    padding: 4px 5px 3px 5px;
    text-align: center;
  }

  .collapsible:after {
    content: "+";
    background-color: rgb(1, 84, 1);
  }

  .active:after {
    content: "-";
    background-color: rgb(1, 84, 1);
  }

  .content-compress {
    max-height: 0;
    overflow: hidden;
    transition: max-height 0.2s ease-out;
    background-color: #f1f1f1;
  }

  .column {
    float: left;
    width: 46%;
    padding: 3px;
    margin: 1%;
  }

  .row:after {
    content: "";
    float: center;
    display: table;
    clear: both;
  }

  @media screen and (max-width: 700px) {
    .column {
      width: 98%;
    }
  }
</style>
"""

    def getTitle(self):
        # soup = self.get_soap(self.url)
        return (
            self.soap.find("h2", class_="t-song-details__marquee__headline")
            .get_text()
            .replace("\n", "")
            .strip()
        )

    def getSinger(self):
        return (
            self.soap.find("p", class_="large").a.get_text().replace("\n", "").strip()
        )

    def getDetails(self):
        detailsWordsToRemove = [":", "da escritura", "\n", r"\(s\)"]
        detailsAttributesToRemove = [
            "escritoras",
            "tempo",
            "intervalo de chave",
            "chave recomendada",
            "ministério",
            "writer",
            "recommended key",
            "ccli #",
        ]
        detailsAttributesToRename = {
            "chave original": "tom",
            "scripture reference": "Referência",
            "original key": "tom",
            "theme": "temas",
        }
        find = self.soap.find("div", class_="song_taxonomy")
        details = find.find_all("div", class_="detail")
        response = {}
        for item in details:
            name = item.span.get_text().lower().strip()
            content = re.sub("\n", "", item.p.get_text().strip())
            for elem in detailsWordsToRemove:
                # clear content
                name = re.sub(elem, "", name)
            name = (
                detailsAttributesToRename[name]
                if name in detailsAttributesToRename.keys()
                else name
            )
            if name not in detailsAttributesToRemove:
                response[name.capitalize()] = content

        return response

    def getMap(self):
        self.mapMusic = MapMusic(self.soap.title)
        find = self.soap.find_all("div", class_="chord-pro-line")
        for line in find:
            verify = line.find_all("span", class_="matchedChord")

            if all(element["chordnumber"] == "???" for element in verify):
                verifyLines = verify[0].parent.parent.parent.parent.find_all(
                    "span", class_="matchedChord"
                )
                hasLyrics = False
                for item in verifyLines:
                    if item["chordnumber"] != "???":
                        hasLyrics = True
                if hasLyrics != True:
                    region = Region(
                        name=verifyLines[0]
                        .parent.parent.parent.find("div", class_="chord-pro-lyric")
                        .get_text()
                    )
                    self.mapMusic.append(region)
            else:
                verify = line.find_all("div", class_="chord-pro-segment")
                newLine = Line()
                for item in verify:  # chord-pro-segment
                    chordText = ""
                    for elem in item.find("div", class_="chord-pro-note").children:
                        if elem.string is not None:
                            chordText += elem.string
                        else:
                            chordText += elem.get_text()

                    try:
                        lyrics = item.find("div", class_="chord-pro-lyric").get_text()
                    except:
                        lyrics = ""

                    newSequence = Sequence(
                        chords=chordText,
                        lyrics=lyrics,
                    )
                    newLine.append(newSequence)
                region.append(newLine)

        return self.mapMusic

    def getHead(self):
        return f"""<head>
        <meta charset="UTF-8">
  <title>{self.getTitle()}</title>
</head>"""

    def makeFile(self):
        details = """<fieldset class="info">
    <legend align="right" class="legend collapsible active">
      Informações Gerais
    </legend>
    <div class="content-compress" style="max-height: 900000px;"><table class="theme-table"> """
        for key, value in self.getDetails().items():
            details += f"""
        <tr>
          <td>{key}</td>
          <td class="theme-column">{''.join(['<span class="theme-values">'+ item +'</span>' for item in value.split(',')]) if key == "Temas" else (''.join(['<span class="theme-values-text">'+ item +'</span>' for item in value.split(';')]) if key == "Referência" else value)}</td>
        </tr>
"""
        details += "</table></div></fieldset>"
        return (
            """<!DOCTYPE html>
<html>"""
            + self.getStyle()
            + self.getHead()
            + f"""
        <body>
        <h1 class='title'>{self.getTitle()}</h1>
        <h2 class='subtitle'>{self.getSinger()}</h2>
        {details}<br>
        <fieldset class="info">
    <legend align="right" class="legend collapsible active">
      Mapa
    </legend>
    <div class="content-compress" style="max-height: 900000px;">
        <div class="content row"><div class="map">{self.getResumeMap()}</div></div></div>
        </fieldset><br><fieldset class="info">
    <legend align="right" class="legend collapsible active">
      Letra e Cifra
    </legend>
    <div class="content-compress" style="max-height: 900000px;">
        <div class="content row">{str(self.mapMusic)}</div></div>
        </fieldset>{self.getScripts()}
        </body></html>
        """
        )
