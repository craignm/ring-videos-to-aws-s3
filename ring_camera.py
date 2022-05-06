import json
from pathlib import Path
from pprint import pprint
from ring_doorbell import Ring, Auth
from oauthlib.oauth2 import MissingTokenError
import os


class RingVideo:
    url = None
    filepath = None
    filename = None

    def __init__(self, url, filepath, filename):
        self.url = url
        self.filepath = filepath
        self.filename = filename

def otp_callback():
    auth_code = input("2FA code: ")
    return auth_code

cache_file = Path("test_token.cache")

def token_updated(token):
    cache_file.write_text(json.dumps(token))


class RingCamera:
    ring = None
    cameras = None
    history_limit = 200
    videos = []

    def __init__(self, username, password, history_limit):
        if cache_file.is_file():
            auth = Auth("Dropbox/1.0", json.loads(cache_file.read_text()), token_updated)
        else:
            auth = Auth("Dropbox/1.0", None, token_updated)
            try:
                print("try no otp")
                auth.fetch_token(username, password)
            except MissingTokenError:
                print("try with otp")
                auth.fetch_token(username, password, otp_callback())

        self.ring = Ring(auth)
        self.ring.update_data()

        devices = self.ring.devices()
        pprint(devices)

        self.history_limit = history_limit

        if 'stickup_cams' in devices and len(devices['stickup_cams']) > 0:
            self.cameras = devices['stickup_cams']
        else:
            raise Exception("Unable to connect to find any devices")

    def get_motion_videos_by_date(self, date_to_download, timezone):
        for camera in self.cameras:
            video_history = camera.history(limit=self.history_limit)
            pprint(video_history)
            video_history = [x for x in video_history if (x['created_at'].astimezone(timezone).date() ==
                                                          date_to_download and x['kind'] == 'motion')]
            for history in video_history:
                directory = history['created_at'].astimezone(timezone).strftime("%Y/%m/%d")
                filename = camera.name + \
                    history['created_at'].astimezone(timezone).strftime("-%Y-%m-%d-%H-%M-%S") + ".mp4"

                path = os.path.join(directory, filename)

                self.videos.append(RingVideo(camera.recording_url(history['id']), path, filename))

        return self.videos
