#!/usr/bin/env python3
"""a minimalistic youtube downloader
"""
import argparse
import sys
import urllib.request
import re
import json
import math
import os
from codecs import encode, decode
import logging


def unescape(x):
    """unescapes a nested json object,
    e.g. "{\\"la\\": 42} --> {"la": 42}

    based on https://stackoverflow.com/a/57192592
    """
    return decode(encode(x, "latin-1", "backslashreplace"), "unicode-escape")


class DownloadProgressBar:
    """a download progress bar for urllib.request.urlretrieve
    roughly based on https://stackoverflow.com/a/53643011
    """

    def __init__(self):
        self._downloaded = 0

    def __call__(self, block_num, block_size, total_size):

        self._downloaded = block_num * block_size
        if self._downloaded < total_size:
            percent = int(math.ceil(100 * self._downloaded / total_size))
            max_width = 60
            width = int(math.ceil(max_width * percent / 100))
            progress = "\r[" + width * "#" + (max_width - width) * "-" + "] "
            progress += str(percent).rjust(3) + " %"
            print(progress, flush=True, end="")
        else:
            print()


def _get_file(url, target_filename_and_path):
    """
    downloads a file from `url` to `target_filename_and_path`
    """
    try:
        urllib.request.urlretrieve(url, target_filename_and_path, DownloadProgressBar())
    except urllib.error.URLError as e:
        return False
    return True


def create_filename(x):
    """creates a unified filename for a youtube video based on the title"""
    return x.replace(" - Youtube", "").strip().lower().replace(" ", "_").replace("\n", "")


def download(youtube_url):
    """download a video from youtube"""

    # read html page
    html = str(urllib.request.urlopen(youtube_url).read(), "latin1")
    # get title
    title = "unknown video"
    for l in html.split("\n"):  # this iteration saves some time
        m = re.match(".*<title>(.*?)</title>.*", l)
        if m:
            title = m.group(1)
            break
    filename = create_filename(title)

    # parse the player api part of the html page
    player_api = html.split('id="player-api"')[1].split("</script>")[1]

    # normal "non-adaptive" video/audio formats
    n_formats = re.match('.*formats\\\\":\[(.*?)\],', player_api).group(1)
    normal_formats = json.loads("[" + unescape(n_formats) + "]")

    logging.debug(json.dumps(normal_formats, indent=4))

    # adaptive formats
    a_formats = re.match('.*adaptiveFormats\\\\":\[(.*?)\]}', player_api).group(1)
    adaptive_formats = json.loads("[" + unescape(a_formats) + "]")
    logging.debug(json.dumps(adaptive_formats, indent=4))
    video_streams = []
    audio_streams = []

    for x in adaptive_formats:
        if "video" in x["mimeType"]:
            video_streams.append(x)
        if "audio" in x["mimeType"]:
            audio_streams.append(x)

    # select streams for audio and video
    max_video_height = max(video_streams, key=lambda x: x["height"])
    max_audio_br = max(audio_streams, key=lambda x: x["averageBitrate"])
    print(
        f"""
    selected audio={max_audio_br["itag"]} {max_audio_br["mimeType"]}
             video={max_video_height["itag"]} {max_video_height["mimeType"]}
    """
    )

    # download the files
    video_filename = filename + ".video"
    print(f"download video to {video_filename}:")
    _get_file(max_video_height["url"], video_filename)
    audio_filename = filename + ".audio"
    print(f"download audio to {audio_filename}:")
    _get_file(max_audio_br["url"], audio_filename)

    # combine both files to one video, and delete the audio and video parts
    print(f"combine audio and video to {filename}.mkv:")
    os.system(f"""ffmpeg -i "{video_filename}" -i "{audio_filename}" -c:v copy -c:a copy {filename}.mkv """)
    os.remove(video_filename)
    os.remove(audio_filename)
    return True


def main(_):
    # argument parsing
    parser = argparse.ArgumentParser(
        description="minimalistic youtube downloader; download filename will be automatically deduced",
        epilog="stg7 2020",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("youtube-url", type=str, help="url to download")
    parser.add_argument(
        "-d",
        "--debug",
        help="Print debugging statements",
        action="store_const",
        dest="loglevel",
        const=logging.DEBUG,
        default=logging.WARNING,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="Be verbose",
        action="store_const",
        dest="loglevel",
        const=logging.INFO,
    )

    a = vars(parser.parse_args())
    logging.basicConfig(level=a["loglevel"])

    download(a["youtube-url"])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
