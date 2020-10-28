# ytdown
A quick and dirty youtube downloader.

Due to the recent making of "youtube-dl" offline and the simplicity of this tool https://github.com/sdushantha/bin/blob/master/utils/ytdl.py (however it does not support full-hd or even 4K video download), I started to develop a similar tool, that overcomes such limits.

So the general idea is to parse a youtube webpage, find the part where the itags are defined, select the adaptive itag formats, unescape all the objects there and finally select video with max height, and audio with max bitrate.
Afterwards everything is combined using `ffmpeg`.
The filename of the video is automatically estimated based on the video title.

## Requirements
* python3 (at least 3.6, 3.8 is recommended)
* ffmpeg (4.2 recommended)



