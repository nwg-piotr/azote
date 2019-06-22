#!/usr/bin/env python3
# _*_ coding: utf-8 _*_

"""
Wallpaper manager for Sway, i3 and some other WMs, as a frontend to swaybg and feh

Author: Piotr Miller
e-mail: nwg.piotr@gmail.com
Website: http://nwg.pl
Project: https://github.com/nwg-piotr/azote
License: GPL3
"""
app_name = 'azote'

CRITICAL = 'critical'
ERROR = 'error'
WARNING = 'warning'
INFO = 'info'
DEBUG = 'debug'

env = {"wm": '', "i3ipc": False, "xrandr": False, "send2trash": False}
sway = False

lang = None             # dictionary "name": lang_string

preview = None
status_bar = None
buttons_list = None
display_boxes_list = None
selected_wallpaper = None
selected_picture_label = None
split_button = None
apply_button = None
feh_button = None
trash_button = None

cols = 3                # number of columns in pictures preview

allowed_file_types = ['jpg', 'jpeg', 'png']

app_dir = ''            # ~/.azote
thumb_dir = ''          # ~/.azote/thumbnails
tmp_dir = ''            # ~/.azote/temp
bcg_dir = ''            # ~/.azote/backgrounds-sway or ~/.azote/backgrounds-feh
sample_dir = ''         # ~/.azote/sample
log_file = ''           # ~/.azote/log.txt
cmd_file = ''           # ~/.azote/command.sh
logging_enabled = True
displays = None         # detected displays details

settings = None         # object saved to / restored from ~/.azote/settings.pkl
