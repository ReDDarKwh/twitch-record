

import requests
import os
import time
import json
import sys
import subprocess
import datetime
import getopt
import shutil


class TwitchRecorder:
    def __init__(self):
        # global configuration
        self.client_id = "jzkbprff40iqj646a697cyrvl0zt2m6"  # don't change this
        # get oauth token value by typing `streamlink --twitch-oauth-authenticate` in terminal
        self.oauth_token = "6hmqdun3lcrunsrl5roloic36ahczu"
        self.ffmpeg_path = 'ffmpeg'
        self.refresh = 30.0
        self.root_path = "/home/pi/twitchVideos"

        # user configuration
        self.username = "juniantr"
        self.quality = "720p"

    def run(self):
        # path to recorded stream
        self.recorded_path = os.path.join(
            self.root_path, "recorded", self.username)

        # path to finished video, errors removed
        self.processed_path = os.path.join(
            self.root_path, "processed", self.username)

        # create directory for recordedPath and processedPath if not exist
        if(os.path.isdir(self.recorded_path) is False):
            os.makedirs(self.recorded_path)
        if(os.path.isdir(self.processed_path) is False):
            os.makedirs(self.processed_path)

        # remove the last videos recorded for space

        for the_file in os.listdir(self.recorded_path):
            file_path = os.path.join(self.recorded_path, the_file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)

            except Exception as e:
                print(e)

        for the_file in os.listdir(self.processed_path):
            file_path = os.path.join(self.processed_path, the_file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)

            except Exception as e:
                print(e)

        print("Checking for", self.username, "every", self.refresh,
              "seconds. Record with", self.quality, "quality.")

        self.loopcheck()

    def check_user(self):
        # 0: online,
        # 1: offline,
        # 2: not found,
        # 3: error
        url = 'https://api.twitch.tv/kraken/streams/' + self.username
        info = None
        status = 3
        try:
            r = requests.get(
                url, headers={"Client-ID": self.client_id}, timeout=15)
            r.raise_for_status()
            info = r.json()
            if info['stream'] == None:
                status = 1
            else:
                status = 0
        except requests.exceptions.RequestException as e:
            if e.response:
                if e.response.reason == 'Not Found' or e.response.reason == 'Unprocessable Entity':
                    status = 2

        return status, info

    def loopcheck(self):
        while True:
            status, info = self.check_user()
            if status == 2:
                print("Username not found. Invalid username or typo.")
                time.sleep(self.refresh)
            elif status == 3:
                print(datetime.datetime.now().strftime("%Hh%Mm%Ss"), " ",
                      "unexpected error. will try again in 5 minutes.")
                time.sleep(300)
            elif status == 1:
                print(self.username, "currently offline, checking again in",
                      self.refresh, "seconds.")
                time.sleep(self.refresh)
            elif status == 0:
                print(self.username, "online. Stream recording in session.")
                filename = self.username + " - " + datetime.datetime.now().strftime("%Y-%m-%d %Hh%Mm%Ss") + \
                    " - " + (info['stream']
                             ).get("channel").get("status") + ".mp4"

                # clean filename from unecessary characters
                filename = "".join(x for x in filename if x.isalnum() or x in [
                                   " ", "-", "_", "."])

                recorded_filename = os.path.join(self.recorded_path, filename)

                # start streamlink process and timeout after 4 hours
                subprocess.call(["streamlink", "--twitch-oauth-token", self.oauth_token,
                                 "twitch.tv/" + self.username, self.quality, "-o", recorded_filename], timeout=60 * 60 * 4)

                print("Recording stream is done. Fixing video file.")
                if(os.path.exists(recorded_filename) is True):
                    try:
                        subprocess.call([self.ffmpeg_path, '-err_detect', 'ignore_err', '-i',
                                         recorded_filename, '-c', 'copy', os.path.join(self.processed_path, filename)])
                        os.remove(recorded_filename)
                    except Exception as e:
                        print(e)
                else:
                    print("Skip fixing. File not found.")

                print("Fixing is done. exiting")
                break


def main(argv):
    twitch_recorder = TwitchRecorder()
    usage_message = 'twitch-recorder.py -u <username> -q <quality>'

    try:
        opts, args = getopt.getopt(argv, "hu:q:", ["username=", "quality="])
    except getopt.GetoptError:
        print(usage_message)
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print(usage_message)
            sys.exit()
        elif opt in ("-u", "--username"):
            twitch_recorder.username = arg
        elif opt in ("-q", "--quality"):
            twitch_recorder.quality = arg

    twitch_recorder.run()


if __name__ == "__main__":
    main(sys.argv[1:])
