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

env = {"wm": '', "xrandr": False, "send2trash": False}
sway = False

lang = None             # dictionary "name": lang_string

preview = None
progress_bar = None
status_bar = None
buttons_list = None
display_boxes_list = None
selected_wallpaper = None
selected_picture_label = None
split_button = None
apply_button = None
apply_to_all_button = None

cols = 3                # number of columns in pictures preview

allowed_file_types = ['jpg', 'jpeg', 'png']
associations = None     # dictionary {'extension": [program1, program2, program3, ...]}

app_dir = ''            # ~/.azote
thumb_dir = ''          # ~/.azote/thumbnails
tmp_dir = ''            # ~/.azote/temp
bcg_dir = ''            # ~/.azote/backgrounds-sway or ~/.azote/backgrounds-feh
sample_dir = ''         # ~/.azote/sample
log_file = ''           # ~/.azote/log.txt
cmd_file = ''           # ~/.azote/command.sh
config_home = ''        # $XDG_CONFIG_HOME or ~/.config/azote
data_home = ''          # $XDG_DATA_HOME or ~/.local/share/azote
data_migrated = False

logging_enabled = True
displays = None         # detected displays details

settings = None         # object saved to / restored from ~/.azote/settings.pkl

modes_swaybg = ["stretch", "fit", "fill", "center", "tile"]
modes_feh = ["scale", "max", "fill", "center", "tile"]

main_window = None
clipboard = None
picker = False