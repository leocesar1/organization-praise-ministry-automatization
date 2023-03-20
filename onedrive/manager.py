from json import load, loads
from requests import get
from urllib.parse import quote
from sys import stdout

from default.default import get_Credentials, Metaclass

stdout.reconfigure(encoding='utf-8')


class OneDrive(metaclass=Metaclass):
    connection = False

    def __init__(self, client_id=None):
        if not self.connection:
            self.connection = self.connect(client_id)
        else:
            pass

    def connect(self, client_id=None):
        URL = 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize'
        permissions = ['files.readwrite']
        response_type = 'token'
        redirect_uri = 'http://localhost:8080/'
        scope = '+'.join(permissions)
        client_id = client_id if client_id is not None else get_Credentials("onedrive")[
            "onedrive"]["client_id"]
        try:
            print('Click over this link ' + URL + '?client_id=' + client_id + '&scope=' +
                  scope + '&response_type=' + response_type+'&redirect_uri=' + quote(redirect_uri))
            print('Sign in to your account, copy the whole redirected URL.')
            code = input("Paste the URL here :")
            self.token = code[(code.find('access_token') +
                               len('access_token') + 1): (code.find('&token_type'))]
            self.URL = 'https://graph.microsoft.com/v1.0/'
            self.HEADERS = {'Authorization': 'Bearer ' + self.token}
            response = get(self.URL + 'me/drive/', headers=self.HEADERS)
            if (response.status_code == 200):
                response = loads(response.text)
                # print('Connected to the OneDrive of', response['owner']['user']['displayName']+' (', response['driveType']+' ).',
                #       '\nConnection valid for one hour. Reauthenticate if required.')
            elif (response.status_code == 401):
                response = loads(response.text)
                print('API Error! : ', response['error']['code'],
                      '\nSee response for more details.')
            else:
                response = loads(response.text)
                print('Unknown error! See response for more details.')
        except:
            print('Connection fail.')
            return False
        finally:
            print('OneDrive Connected')
            return True

    def getFileList(self, pathId="A9BCF86E0D3403C2!367937"):
        url = f"{self.URL}drives/a9bcf86e0d3403c2/items/{pathId}/children"
        response = get(url, headers=self.HEADERS)
        return loads(response.text)['value']

    def downloadFile(self, downloadUrl):
        return get(downloadUrl, headers=self.HEADERS,
                   allow_redirects=True).content
