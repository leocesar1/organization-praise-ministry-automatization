from __future__ import print_function

import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from default.default import get_Credentials, Metaclass


class GoogleSheet(metaclass=Metaclass):
    connection = False

    def __init__(self):
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
        self.creds = None
        if os.path.exists('token.json'):
            self.creds = Credentials.from_authorized_user_file(
                'token.json', SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentialsGoogle.json', SCOPES)
                self.creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(self.creds.to_json())

    def getAllMusicDetails(self):
        getDefaultsValues = get_Credentials("googleSheet")["googleSheet"]
        SAMPLE_SPREADSHEET_ID = getDefaultsValues["SAMPLE_SPREADSHEET_ID"]
        SAMPLE_RANGE_NAME = getDefaultsValues["SAMPLE_RANGE_NAME"]

        try:
            service = build('sheets', 'v4', credentials=self.creds)

            # Call the Sheets API
            sheet = service.spreadsheets()
            result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                        range=SAMPLE_RANGE_NAME
                                        ).execute()
            values = result.get('values', [])

            if not values:
                print('No data found.')
                return

            response = {}
            for row in values:
                # Print columns A and E, which correspond to indices 0 and 4.
                musicName = row[0]
                if musicName != "":
                    categories = row[1:]
                    categories = self.makeCategories(categories)
                    response[musicName] = categories
            return response

        except HttpError as err:
            print(err)

    def makeCategories(self, categories=[]):
        defaultList = [
            "\#amor",
            "\#bondade",
            "\#busca",
            "\#cristologia",
            "\#escatologia",
            "\#exaltacao",
            "\#fe",
            "\#gratidao",
            "\#intercessao",
            "\#paternidade",
            "\#pneumatologia",
            "\#rendicao"
        ]
        categoriesOfMusic = ""
        for i in range(0, len(categories)):
            if categories[i] == "TRUE":
                categoriesOfMusic += defaultList[i] + " "

        return categoriesOfMusic
    
    def updateSongs(self, songList = []):
        pass
