# Copyright (c) Subramanya N. Licensed under the Apache License 2.0. All Rights Reserved
import logging
import os
import sys
import re

# selenium
import selenium
from selenium import webdriver
import warnings

logging.basicConfig(
    format="[%(levelname)s: %(name)-12s] %(message)s",
    level=logging.ERROR)
logger = logging.getLogger(__name__)

warnings.filterwarnings("ignore", category=UserWarning, module="selenium")

def names_contain(names, name):
    for n in names:
        if name in n:
            return True
    return False

class Echo360Downloader(object):
    def __init__(self, course, output_dir, webdriver_to_use="chrome"):
        super(Echo360Downloader, self).__init__()
        self._course = course
        root_path = os.path.dirname(os.path.abspath(sys.modules["__main__"].__file__))
        if output_dir == "":
            output_dir = root_path
        self._output_dir = output_dir

        self._useragent = "Mozilla/5.0 (iPad; CPU OS 6_0 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/6.0 Mobile/10A5376e Safari/8536.25"

        if webdriver_to_use == "chrome":
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.chrome.options import Options

        opts = Options()
        opts.add_argument("--window-size=1920x1080")
        opts.add_argument("user-agent={}".format(self._useragent))

        service = Service()
        self._driver = webdriver.Chrome(service=service, options=opts)

        self._course.set_driver(self._driver)
        self._videos = []

        self.regex_replace_invalid = re.compile(r"[\\\\/:*?\"<>|]")

    def _find_pos(self, videos, the_video):
        # compare by object id, because date could possibly be the same in some case.
        return videos.index(the_video)

    def _get_filename(self, course, date, title):
        if course:
            # add [:150] to avoid filename too long exception
            filename = "{} - {} - {}".format(course, date, title[:150])
        else:
            filename = "{} - {}".format(date, title[:150])
        # replace invalid character for files
        return self.regex_replace_invalid.sub("_", filename)

    def download_all(self):
        print("> I assume you have already logged in to Echo360...")
        print("> Retrieving couser information...", flush=True)
        print("> Done!")
        videos = self._course.get_videos().videos
        # change the output directory to be inside a folder named after the course
        self._output_dir = os.path.join(
            self._output_dir, "{0}".format(self._course.nice_name).strip()
        )
        print("> Downloading videos to: {0}".format(self._output_dir))
        if os.path.exists(self._output_dir):
            already = os.listdir(self._output_dir)
            print(f"These files are already under that directory: {already}")
        else:
            already = []
        # replace invalid character for folder
        self.regex_replace_invalid.sub("_", self._output_dir)
        videos_to_be_download = []
        for video in videos:
            lecture_number = self._find_pos(videos, video)
            sub_videos = video.get_all_parts()

            for i, sub_video in list(enumerate(sub_videos)):
                sub_lecture_num = lecture_number + 1
                if len(sub_videos) > 1:
                    sub_lecture_num = "{}.{}".format(sub_lecture_num, i + 1)
                title = "Lecture {} [{}]".format(sub_lecture_num, sub_video.title)
                filename = self._get_filename(self._course.course_id,
                                                date=sub_video.date,
                                                title=title)

                # check if the video is already downloaded
                print("> Checking if the video '{0}' has already been downloaded...".format(filename))
                if names_contain(already, filename):
                    print(
                        ">> Skipping Lecture '{0}' as it has already been downloaded.".format(
                            filename
                        )
                    )
                else:
                    print("> Adding video '{0}' to the download list...".format(filename))
                    videos_to_be_download.append((filename, sub_video))

        print("-" * 80)
        print("    Course: {0}".format(self._course.nice_name))
        print(
            "    Total videos to download: {0} out of {1}".format(
                len(videos_to_be_download), len(videos)
            )
        )
        print("-" * 80)

        downloaded_videos = []
        for filename, video in videos_to_be_download:
            if video.url is False:
                print(
                    ">> Skipping Lecture '{0}' as it says it does "
                    "not contain any video.".format(filename)
                )
            else:
                if video.download(self._output_dir, filename):
                    downloaded_videos.append(filename)
        self._driver.close()
