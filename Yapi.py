import os
from pathlib import Path

from dotenv import load_dotenv
from yandex_music import Client
from yandex_music.exceptions import Unauthorized, YandexMusicError

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

LOGIN = os.getenv("LOGIN")
PWD = os.getenv("PWD")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")


class Yapi:
    client = None
    _TOKEN = None
    _LOGIN = None
    _PWD = None

    def __init__(self, token: str = '', login: str = '', pwd: str = ''):
        if token != '':
            self._TOKEN = token
        if login != '':
            self._LOGIN = login
        if pwd != '':
            self._PWD = pwd

        print("Yapi instance create")

    async def init(self, login: str = '', pwd: str = ''):
        try:
            if login != '' and pwd != '':
                # self.client = Client.from_credentials(login, pwd, report_new_fields=False)
                self.client = Client.from_credentials(login, pwd)
                return True

            else:
                if pwd == '' and login != '':
                    # self.client = Client.from_token(login, report_new_fields=False)
                    self.client = Client.from_token(login)
                    return True
                else:
                    # self.client = Client.from_credentials(LOGIN, PWD, report_new_fields=False)
                    self.client = Client.from_credentials(LOGIN, PWD)
                    return True

        except Unauthorized:
            print("Unauthorized")
            return False

        except YandexMusicError:
            print("YandexMusicError")
            return False

    def get_user_likes_tracks(self):
        tracks = self.client.users_likes_tracks()
        return tracks
