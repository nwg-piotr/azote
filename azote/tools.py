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
import os
import glob
import hashlib
import logging
from PIL import Image, ImageOps
import common
import pickle
import subprocess
import locale
import pkg_resources
from shutil import copyfile

import json

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


def log(message, level=None):
    if common.logging_enabled:
        if level == "critical":
            logging.critical(message)
        elif level == "error":
            logging.error(message)
        elif level == "warning":
            logging.warning(message)
        elif level == "info":
            logging.info(message)
        else:
            logging.debug(message)


def str_to_bool(s):
    if s.upper() == 'TRUE':
        return True
    elif s.upper() == 'FALSE':
        return False
    else:
        raise ValueError


def check_displays():
    # Sway or not Sway?
    wm = subprocess.check_output("wmctrl -m | awk '/Name/{print $2}'", shell=True).decode("utf-8").strip()
    common.sway = 'LG3D' in wm or 'wlroots' in wm
    if common.sway:
        common.env['wm'] = 'sway'
    else:
        common.env['wm'] = wm

    fnull = open(os.devnull, 'w')
    common.env['xrandr'] = subprocess.call(["which", "xrandr"], stdout=fnull, stderr=subprocess.STDOUT) == 0

    if common.env['wm'] == 'sway':
        # We need swaymsg to check outputs on Sway
        try:
            displays = []
            json_string = subprocess.check_output("swaymsg -t get_outputs", shell=True).decode("utf-8").strip()
            outputs = json.loads(json_string)
            for output in outputs:
                if output['active']:  # dunno WTF xroot-0 is: i3 returns such an output with "active":false
                    display = {'name': output['name'],
                               'x': output['rect']['x'],
                               'y': output['rect']['y'],
                               'width': output['rect']['width'],
                               'height': output['rect']['height']}
                    displays.append(display)
                    log("Output found: {}".format(display), common.INFO)

            # Dummy display for testing
            """display = {'name': 'HDMI-A-2',
                       'x': 1920,
                       'y': 0,
                       'width': 1920,
                       'height': 1080}
            displays.append(display)
            log("Output: {}".format(display), common.INFO)"""

            # sort displays list by x, y: from left to right, then from bottom to top
            displays = sorted(displays, key=lambda x: (x.get('x'), x.get('y')))

            return displays

        except Exception as e:
            log("Failed checking displays: {}".format(e))

    # On i3 we could use i3-msg here, but xrandr should also return what we need. If not on Sway - let's use xrandr
    elif common.env['xrandr']:
        names = subprocess.check_output("xrandr | awk '/ connected/{print $1}'", shell=True).decode(
            "utf-8").splitlines()
        res = subprocess.check_output("xrandr | awk '/*/{print $1}'", shell=True).decode("utf-8").splitlines()
        displays = []
        for i in range(len(names)):
            w_h = res[i].split('x')
            display = {'name': names[i],
                       'x': 0,
                       'y': 0,
                       'width': w_h[0],
                       'height': w_h[1]}
            displays.append(display)
            log("Output found: {}".format(display), common.INFO)

        return displays

    else:
        log("Couldn't check displays", common.ERROR)
        exit(1)


def set_env(language=None):
    # application folder
    common.app_dir = os.path.join(os.getenv("HOME"), ".azote")
    if not os.path.isdir(common.app_dir):
        os.mkdir(common.app_dir)

    # logging
    common.log_file = os.path.join(common.app_dir, "log.txt")
    logging.basicConfig(filename=common.log_file, format='%(asctime)s %(levelname)s: %(message)s', filemode='w',
                        level=logging.INFO)

    try:
        version = pkg_resources.require(common.app_name)[0].version
    except Exception as e:
        version = ' unknown version: {}'.format(e)

    log('Azote v{}'.format(version), common.INFO)

    # We will preload the en_EN dictionary as default values
    common.lang = Language()

    if not language:
        # Lets check locale value
        # If running with LC_ALL=C, we'll get (None, None) here. Let's use en_EN in such case.
        lang = locale.getlocale()[0] if locale.getlocale()[0] is not None else 'en_EN'
    else:
        lang = language

    common.lang.load(lang)

    common.displays = check_displays()

    # thumbnails folder
    common.thumb_dir = os.path.join(common.app_dir, "thumbnails")
    if not os.path.isdir(common.thumb_dir):
        os.mkdir(common.thumb_dir)

    # command file
    common.cmd_file = os.path.join(os.getenv("HOME"), ".azotebg")

    # temporary folder
    common.tmp_dir = os.path.join(common.app_dir, "temp")
    if not os.path.isdir(common.tmp_dir):
        os.mkdir(common.tmp_dir)
    # remove all files inside on start
    for file in os.listdir(common.tmp_dir):
        path = os.path.join(common.tmp_dir, file)
        os.remove(path)  # clear on start
        log("Removed {}".format(path), common.INFO)

    # backgrounds folder
    name = 'backgrounds-sway' if common.sway else 'backgrounds-feh'
    common.bcg_dir = os.path.join(common.app_dir, name)
    if not os.path.isdir(common.bcg_dir):
        os.mkdir(common.bcg_dir)

    # Sample folder (will be set on 1st run only)
    common.sample_dir = os.path.join(common.app_dir, "sample")
    if not os.path.isdir(common.sample_dir):
        os.mkdir(common.sample_dir)
    copyfile('images/azote-wallpaper.jpg', os.path.join(common.sample_dir, 'azote-wallpaper.jpg'))
    copyfile('images/azote-wallpaper1.jpg', os.path.join(common.sample_dir, 'azote-wallpaper1.jpg'))
    copyfile('images/azote-wallpaper2.jpg', os.path.join(common.sample_dir, 'azote-wallpaper2.jpg'))

    # Sway comes with some sample wallpapers
    if common.sway and os.path.isdir('/usr/share/backgrounds/sway'):
        common.sample_dir = '/usr/share/backgrounds/sway'

    common.settings = Settings()

    log("Environment: {}".format(common.env), common.INFO)

    # check programs capable of opening files of allowed extensions
    if os.path.isfile('/usr/share/applications/mimeinfo.cache'):
        common.associations = {}  # Will stay None if the mimeinfo.cache file not found

        with open(os.path.join('/usr/share/applications/mimeinfo.cache')) as f:
            mimeinfo_cache = f.read().splitlines()

        for file_type in common.allowed_file_types:
            for line in mimeinfo_cache:
                if line.startswith('image/{}'.format(file_type)):
                    line = line.split('=')[1]  # cut out leading 'image/ext'
                    # Paths to .desktop files for opener names found
                    filenames = line[:-1].split(';')  # cut out trailing ';' to avoid empty last element after splitting
                    # prepend path
                    for i in range(len(filenames)):
                        filenames[i] = '/usr/share/applications/{}'.format(filenames[i])

                    data = []
                    for i in range(len(filenames)):
                        # Let's find the program Name= and Exec= in /usr/share/applications/shortcut_name.desktop
                        shortcut_file = '/usr/share/applications/{}'.format(filenames[i])
                        name, exec = '', ''

                        if os.path.isfile(filenames[i]):
                            with open(filenames[i]) as f:
                                rows = f.read().splitlines()
                                for row in rows:
                                    if row.startswith('Name='):
                                        name = row.split('=')[1]
                                    elif row.startswith('Name[{}]='.format(common.lang.lang[0:2])):
                                        name = row.split('=')[1]
                                    if row.startswith('Exec'):
                                        exec = row.split('=')[1].split()[0]
                                        continue
                            if name and exec:
                                data.append((name, exec))
                    common.associations[file_type] = data
        """
        Not necessarily all programs register jpg and jpeg extension (e.g. gimp registers jpeg only).
        Let's create sets, join them and replace lists for both jpg and jpeg keys.
        """
        jpg = set(common.associations['jpg'])
        jpeg = set(common.associations['jpeg'])
        together = jpg | jpeg
        common.associations['jpg'] = together
        common.associations['jpeg'] = together

        log("Image associations: {}".format(common.associations), common.INFO)


def copy_backgrounds():
    # Clear current folder content
    for file in os.listdir(common.bcg_dir):
        os.remove(os.path.join(common.bcg_dir, file))
    # Copy manipulated (flip, split) files from the temporary folder
    for file in os.listdir(common.tmp_dir):
        copyfile(os.path.join(common.tmp_dir, file), os.path.join(common.bcg_dir, file))


def hash_name(full_path):
    """
    Thumbnail path -> name (w/o extension)
    :param full_path: original file path
    :return: MD5-hashed path
    """
    return hashlib.md5(full_path.encode()).hexdigest()


def create_thumbnails(scr_path):
    # Let's count allowed files first
    common.progress_bar.hide()
    counter = 0
    for extension in common.allowed_file_types:
        for in_path in glob.glob(os.path.join(scr_path, "*.{}".format(extension))):
            if file_allowed(in_path):
                counter += 1
    if counter > 0:
        # get all the files of allowed types from current path
        common.progress_bar.show()
        common.progress_bar.set_fraction(0.0)
        processed = 0
        for extension in common.allowed_file_types:
            for in_path in glob.glob(os.path.join(scr_path, "*.{}".format(extension))):
                if file_allowed(in_path):
                    thumb_name = "{}.png".format(hash_name(in_path))
                    dest_path = os.path.join(common.thumb_dir, thumb_name)
                    if not os.path.isfile(dest_path):
                        create_thumbnail(in_path, dest_path, thumb_name)
                    elif is_newer(in_path, dest_path):
                        create_thumbnail(in_path, dest_path, thumb_name, True)
                    processed += 1
                    common.progress_bar.set_fraction(processed / counter)
                    common.progress_bar.set_text(str(processed))
                    while Gtk.events_pending():
                        Gtk.main_iteration()
        common.progress_bar.hide()


def create_thumbnail(in_path, dest_path, thumb_name, refresh=False):
    action = 'New thumb' if not refresh else 'Refresh'
    try:
        img = Image.open(in_path)
        # convert to thumbnail image
        img.thumbnail((240, 135), Image.ANTIALIAS)

        img = expand_img(img)

        img.save(dest_path, "PNG")
        log('{}: {} -> {}'.format(action, in_path, thumb_name), common.INFO)
    except Exception as e:
        log('{} - {}'.format(action, e), common.ERROR)


def flip_selected_wallpaper():
    """
    This creates vertically flipped image and its thumbnail and saves to ~/.azote/backgrounds
    :return: thumbnail path, flipped image path
    """
    if common.selected_wallpaper:
        try:
            img = Image.open(common.selected_wallpaper.source_path)
            flipped = img.transpose(Image.FLIP_LEFT_RIGHT)
            img_path = os.path.join(common.bcg_dir, "flipped-{}".format(common.selected_wallpaper.filename))
            flipped.save(os.path.join(common.tmp_dir, "flipped-{}".format(common.selected_wallpaper.filename)), "PNG")

            flipped.thumbnail((240, 135), Image.ANTIALIAS)
            flipped = expand_img(flipped)

            thumb_path = os.path.join(common.tmp_dir, "thumbnail-{}".format(common.selected_wallpaper.filename))
            flipped.save(thumb_path, "PNG")
            return thumb_path, img_path

        except Exception as e:
            log('Failed flipping {} - {}'.format(common.selected_wallpaper.source_path, e), common.ERROR)


def split_selected_wallpaper(num_parts):
    try:
        img = Image.open(common.selected_wallpaper.source_path)
        width, height = img.size
        part_width = width // num_parts
        paths_list = []
        for i in range(num_parts):
            box = (i * part_width, 0, i * part_width + part_width, height)
            part = img.crop(box)
            img_path = os.path.join(common.bcg_dir, "part{}-{}".format(i, common.selected_wallpaper.filename))
            part.save(os.path.join(common.tmp_dir, "part{}-{}".format(i, common.selected_wallpaper.filename)), "PNG")

            part.thumbnail((240, 135), Image.ANTIALIAS)

            thumb_path = os.path.join(common.tmp_dir, "thumb-part{}-{}".format(i, common.selected_wallpaper.filename))

            part = expand_img(part)

            part.save(thumb_path, "PNG")
            paths = (img_path, thumb_path)
            paths_list.append(paths)
        return paths_list

    except Exception as e:
        log('Failed splitting {} - {}'.format(common.selected_wallpaper.source_path, e), common.ERROR)


def expand_img(image):
    # We want the thumbnail to be always 240 x 135. Let's expand if necessary.
    width, height = image.size
    border_h = (240 - width) // 2
    border_v = (135 - height) // 2
    if border_v > 0 or border_h > 0:
        border = (border_h, border_v, border_h, border_v)
        return ImageOps.expand(image, border=border)
    else:
        return image


def is_newer(in_path, dest_path):
    return os.path.getmtime(in_path) > os.path.getmtime(dest_path)


def file_allowed(path):
    ext = path.split('.')[-1].lower()
    return ext in common.allowed_file_types


def update_status_bar():
    num_files = 0
    total_size = 0
    if os.path.isdir(common.thumb_dir):
        for file in os.listdir(common.thumb_dir):
            num_files += 1
            file_info = os.stat(os.path.join(common.thumb_dir, file))
            total_size += file_info.st_size
    common.status_bar.push(0, common.lang['thumbnails_in_cache'].format(num_files, convert_bytes(total_size)))


def convert_bytes(num):
    """
    https://stackoverflow.com/a/39988702/4040598
    """
    for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
        if num < 1024.0:
            return "%3.1f %s" % (num, x)
        num /= 1024.0


def rgba_to_hex(color):
    """
    Return hexadecimal string for :class:`Gdk.RGBA` `color`
    http://wrhansen.blogspot.com/2012/09/how-to-convert-gdkrgba-to-hex-string-in.html
    """
    return "#{0:02x}{1:02x}{2:02x}".format(int(color.red * 255),
                                           int(color.green * 255),
                                           int(color.blue * 255))


class Settings(object):
    def __init__(self):
        self.file = os.path.join(common.app_dir, "settings.pkl")

        self.src_path = common.sample_dir
        self.sorting = 'new'

        self.load()

    def load(self):
        if not os.path.isfile(self.file):
            log('Creating initial settings', common.INFO)
            self.save()

        with open(self.file, 'rb') as input_data:
            settings = pickle.load(input_data)

        self.src_path = settings.src_path  # holds selected path to source pictures
        try:
            self.sorting = settings.sorting  # 'new' 'old' 'az' 'za'
            log('Image sorting: {}'.format(self.sorting), common.INFO)
        except AttributeError:
            self.save()

    def save(self):
        with open(self.file, 'wb') as output:
            pickle.dump(self, output, pickle.HIGHEST_PROTOCOL)


class Language(dict):
    def __init__(self):
        super().__init__()
        self.lang = 'en_EN'
        # We'll initialize with values from en_EN
        with open(os.path.join('languages', 'en_EN')) as f:
            lines = f.read().splitlines()
            for line in lines:
                if line and not line.startswith('#'):
                    pair = line.split('=')
                    key, value = pair[0].strip(), pair[1].strip()
                    self[key] = value

    def load(self, lang):
        try:
            # Overwrite initial values if translation found
            with open(os.path.join('languages', lang)) as f:
                lines = f.read().splitlines()
                for line in lines:
                    if line and not line.startswith('#'):
                        pair = line.split('=')
                        key, value = pair[0].strip(), pair[1].strip()
                        self[key] = value
            self.lang = lang
            log("Loaded lang: {}".format(lang), common.INFO)

        except FileNotFoundError:
            log("Couldn't load lang: {}".format(lang), common.WARNING)
