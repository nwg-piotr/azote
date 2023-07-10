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
from PIL import Image
import pickle
import subprocess
import sys
import shutil

import json

import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf, GLib

from azote import common

dir_name = os.path.dirname(__file__)

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
    common.sway = os.getenv('SWAYSOCK')
    if common.sway:
        common.env['wm'] = 'sway'

    else:
        if os.getenv('XDG_SESSION_DESKTOP'):
            common.env['wm'] = os.getenv('XDG_SESSION_DESKTOP')
        elif os.getenv('DESKTOP_SESSION'):
            common.env['wm'] = os.getenv('DESKTOP_SESSION')
        elif os.getenv('I3SOCK'):
            common.env['wm'] = "i3"
        else:
            common.env['wm'] = 'undetected'

    # sway or not, we may be on Wayland anyway
    if not common.sway:
        common.env['wayland'] = os.getenv('WAYLAND_DISPLAY')

    if common.sway:
        print("Running on sway")
        # We need swaymsg to check outputs on Sway
        try:
            displays = []
            json_string = subprocess.check_output("swaymsg -t get_outputs", shell=True).decode("utf-8").strip()
            outputs = json.loads(json_string)
            for output in outputs:
                if output['active']:  # dunno WTF xroot-0 is: i3 returns such an output with "active":false
                    g_name = output["make"] if output["make"] != "Unknown" else ""
                    if output["model"] and output["model"] != "Unknown":
                        g_name += " {}".format(output["model"])
                    if output["serial"] and output["serial"] != "Unknown":
                        g_name += " {}".format(output["serial"])
                    display = {'name': output['name'],
                               'x': output['rect']['x'],
                               'y': output['rect']['y'],
                               'width': output['rect']['width'],
                               'height': output['rect']['height'],
                               'generic-name': g_name}
                    displays.append(display)
                    log("Output found: {}".format(display), common.INFO)
                try:
                    if output['focused']:
                        common.screen_h = output['rect']['height']
                        print("Available screen height: {} px".format(int(common.screen_h * 0.95)))
                except:
                    pass

            # sort displays list by x, y: from left to right, then from bottom to top
            displays = sorted(displays, key=lambda x: (x.get('x'), x.get('y')))

            return displays

        except Exception as e:
            print("Failed checking displays: {}".format(e), common.ERROR)
            log("Failed checking displays: {}".format(e), common.ERROR)
            exit(1)

    elif os.getenv("HYPRLAND_INSTANCE_SIGNATURE"):
        print("Running on Hyprland")
        import socket
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.connect("/tmp/hypr/{}/.socket.sock".format(os.getenv("HYPRLAND_INSTANCE_SIGNATURE")))

        s.send("j/monitors".encode("utf-8"))
        output = s.recv(20480).decode('utf-8')
        s.close()
        displays = []
        clients = json.loads(output)
        for c in clients:
            g_name = c["make"] if c["make"] else ""
            if c["model"]:
                g_name += " {}".format(c["model"])
            if c["serial"]:
                g_name += " {}".format(c["serial"])
            display = {'name': c['name'],
                       'x': c['x'],
                       'y': c['y'],
                       'width': c['width'],
                       'height': c['height'],
                       'generic-name': g_name}
            displays.append(display)
            log("Output found: {}".format(display), common.INFO)

            if c['focused']:
                if c['transform'] in [0, 2, 4, 6]:
                    h = c['height'] - c["reserved"][1] - c["reserved"][3] - 6
                    common.screen_h = h
                else:
                    h = c['width'] - c["reserved"][0] - c["reserved"][2] - 6
                    common.screen_h = h
                print("Available screen height: {} px".format(h))

        # sort displays list by x, y: from left to right, then from bottom to top
        displays = sorted(displays, key=lambda x: (x.get('x'), x.get('y')))

        return displays

    elif common.env['wayland']:
        print("Running on Wayland, but not sway")
        lines = None
        try:
            lines = subprocess.check_output("wlr-randr", shell=True).decode("utf-8").strip().splitlines()
        except Exception as e:
            print("Wayland, but not sway. Optional wlr-randr package required.")
            log("Failed checking displays: {}".format(e), common.ERROR)
            sys.exit(1)

        if lines:
            name, w, h, x, y, generic_name = None, None, None, None, None, None
            displays = []
            for line in lines:
                if not line.startswith(" "):
                    name = line.split()[0]
                    # very tricky way to obtain this value...
                    generic_name = line.replace(name, "")[2:-4]
                elif "current" in line:
                    w_h = line.split()[0].split('x')
                    w = int(w_h[0])
                    h = int(w_h[1])
                elif "Position" in line:
                    x_y = line.split()[1].split(',')
                    x = int(x_y[0])
                    y = int(x_y[1])
                    if name is not None and w is not None and h is not None and x is not None and y is not None:
                        display = {'name': name,
                                   'x': x,
                                   'y': y,
                                   'width': w,
                                   'height': h,
                                   'generic-name': generic_name}
                        displays.append(display)
                        log("Output found: {}".format(display), common.INFO)
            displays = sorted(displays, key=lambda x: (x.get('x'), x.get('y')))
            print(displays)
            return displays

        else:
            print("Failed parsing wlr-ranrd output")
            log("Failed parsing wlr-ranrd output", common.ERROR)
            exit(1)

        fnull = open(os.devnull, 'w')
        try:
            common.env['swaybg'] = subprocess.call(["swaybg", "-v"], stdout=fnull, stderr=subprocess.STDOUT) == 0
        except Exception as e:
            print("swaybg package required: {}".format(e))
            log("swaybg package not found", common.ERROR)
            exit(1)

    else:
        if common.env['wm'] == "i3":
            print("Running on i3")
        else:
            print("Running on X11")
        fnull = open(os.devnull, 'w')
        try:
            common.env['xrandr'] = subprocess.call(["xrandr", "-v"], stdout=fnull, stderr=subprocess.STDOUT) == 0
        except Exception as e:
            print("xorg-xrandr package required: {}".format(e))
            log("xorg-xrandr package not found", common.ERROR)
            exit(1)

        try:
            common.env['feh'] = subprocess.call(["feh", "-v"], stdout=fnull, stderr=subprocess.STDOUT) == 0
        except Exception as e:
            print("feh package required: {}".format(e))
            log("feh package not found", common.ERROR)
            exit(1)

        try:
            names = subprocess.check_output("xrandr | awk '/ connected/{print $1}'", shell=True).decode(
                "utf-8").splitlines()
            res = subprocess.check_output("xrandr | awk '/[*]/{print $1}'", shell=True).decode("utf-8").splitlines()
            coords = subprocess.check_output("xrandr --listmonitors | awk '{print $3}'", shell=True).decode(
                "utf-8").splitlines()
            displays = []
            for i in range(len(res)):
                w_h = res[i].split('x')
                try:
                    x_y = coords[i + 1].split('+')
                except:
                    x_y = (0, 0, 0)
                display = {'name': names[i],
                           'x': x_y[1],
                           'y': x_y[2],
                           'width': int(w_h[0]),
                           'height': int(w_h[1]),
                           'xrandr-idx': i}
                displays.append(display)
                log("Output found: {}".format(display), common.INFO)

            displays = sorted(displays, key=lambda x: (x.get('x'), x.get('y')))
            return displays

        except Exception as e:
            print("Failed checking displays: {}".format(e), common.ERROR)
            log("Failed checking displays: {}".format(e), common.ERROR)
            exit(1)


def current_display():
    display_number = 0
    x, y = 0, 0
    if common.env['wm'] == "sway":
        string = subprocess.getoutput("swaymsg -t get_outputs")
        outputs = json.loads(string)
        for i in range(len(outputs)):
            if outputs[i]["focused"]:
                rect = outputs[i]["rect"]
                x, y = rect["x"], rect["y"]
    elif common.env['wm'] == "i3":
        # Unfortunately `i3-msg -t get_outputs` output does not have the "focused" key.
        # Let's find the active workspace and its rectangle.
        string = subprocess.getoutput("i3-msg -t get_workspaces")
        workspaces = json.loads(string)
        for i in range(len(workspaces)):
            if workspaces[i]['focused']:
                rect = workspaces[i]["rect"]
                x, y = rect["x"], rect["y"]
    else:
        # For not sway nor i3. This rises deprecation warnings and won't work w/o `pynput` module.
        screen = common.main_window.get_screen()
        try:
            display_number = screen.get_monitor_at_window(screen.get_active_window())
            rectangle = screen.get_monitor_geometry(display_number)
            x, y = rectangle.x, rectangle.y
        except Exception as e:
            print(e)

    for i in range(len(common.displays)):
        display = common.displays[i]
        if display["x"] == x and display['y'] == y:
            display_number = i
            break
    return display_number


def set_env(__version__, lang_from_args=None):
    xdg_config_home = os.getenv('XDG_CONFIG_HOME')
    common.config_home = xdg_config_home if xdg_config_home else os.path.join(os.getenv("HOME"), ".config")
    common.azote_config_home = os.path.join(xdg_config_home, "azote") if xdg_config_home else os.path.join(
        os.getenv("HOME"), ".config/azote")
    if not os.path.isdir(common.azote_config_home):
        os.mkdir(common.azote_config_home)

    xdg_data_home = os.getenv('XDG_DATA_HOME')
    common.data_home = xdg_data_home if xdg_data_home else os.path.join(os.getenv("HOME"), ".local/share/azote")
    if not os.path.isdir(common.data_home):
        os.mkdir(common.data_home)

    # MIGRATE DATA to XDG Base_Directory Specification - compliant folders
    # Up to v1.7.0 Azote used to store all the data here:
    common.app_dir = os.path.join(os.getenv("HOME"), ".azote")

    # Let's move all the content to their proper location, if not yet moved
    data_migrated = False
    migration_error = None
    if os.path.isdir(common.app_dir):
        try:
            azote_rc = os.path.join(common.app_dir, 'azoterc')
            if os.path.isfile(azote_rc):
                shutil.move(azote_rc, os.path.join(common.azote_config_home, 'azoterc'))

            azote_pkl = os.path.join(common.app_dir, 'settings.pkl')
            if os.path.isfile(azote_pkl):
                shutil.move(azote_pkl, os.path.join(common.data_home, 'settings.pkl'))

            bcg_feh_dir = os.path.join(common.app_dir, 'backgrounds-feh')
            if os.path.isdir(bcg_feh_dir):
                cmd = 'cp -rf {} {}'.format(bcg_feh_dir, os.path.join(common.data_home, 'backgrounds-feh'))
                os.system(cmd)

            bcg_sway_dir = os.path.join(common.app_dir, 'backgrounds-sway')
            if os.path.isdir(bcg_sway_dir):
                cmd = 'cp -rf {} {}'.format(bcg_sway_dir, os.path.join(common.data_home, 'backgrounds-sway'))
                os.system(cmd)

            data_migrated = True
        except Exception as e:
            migration_error = e

    if data_migrated:
        # Remove the old ~/.azote folder
        shutil.rmtree(common.app_dir)

    # logging
    common.log_file = os.path.join(common.data_home, "log.txt")
    logging.basicConfig(filename=common.log_file, format='%(asctime)s %(levelname)s: %(message)s', filemode='w',
                        level=logging.INFO)

    log('Azote v{}'.format(__version__), common.INFO)

    if data_migrated:
        log('Data migrated to XDG-compliant folders', common.INFO)

    if migration_error:
        log('Data migration error: {}'.format(migration_error), common.ERROR)

    common.lang = Language(lang_from_args)

    common.displays = check_displays()

    # thumbnails folder
    common.thumb_dir = os.path.join(common.data_home, "thumbnails")
    if not os.path.isdir(common.thumb_dir):
        os.mkdir(common.thumb_dir)

    # command file; let's use separate file name for Hyprland, as generic display names may be different
    if os.getenv("HYPRLAND_INSTANCE_SIGNATURE"):
        common.cmd_file = os.path.join(os.getenv("HOME"), ".azotebg-hyprland")
    else:
        common.cmd_file = os.path.join(os.getenv("HOME"), ".azotebg")

    # temporary folder
    common.tmp_dir = os.path.join(common.data_home, "temp")
    if not os.path.isdir(common.tmp_dir):
        os.mkdir(common.tmp_dir)
    # remove all files inside on start
    for file in os.listdir(common.tmp_dir):
        path = os.path.join(common.tmp_dir, file)
        os.remove(path)  # clear on start
        log("Removed {}".format(path), common.INFO)

    # backgrounds folder
    name = 'backgrounds-sway' if common.sway or common.env['wayland'] else 'backgrounds-feh'
    common.bcg_dir = os.path.join(common.data_home, name)
    if not os.path.isdir(common.bcg_dir):
        os.mkdir(common.bcg_dir)

    # Sample folder (will be set on 1st run only)
    common.sample_dir = os.path.join(common.data_home, "sample")
    if not os.path.isdir(common.sample_dir):
        os.mkdir(common.sample_dir)
        shutil.copyfile(os.path.join(dir_name, 'images/azote-wallpaper.png'), os.path.join(common.sample_dir, 'azote-wallpaper.png'))
        shutil.copyfile(os.path.join(dir_name, 'images/azote-wallpaper1.jpg'), os.path.join(common.sample_dir, 'azote-wallpaper1.jpg'))
        shutil.copyfile(os.path.join(dir_name, 'images/azote-wallpaper2.png'), os.path.join(common.sample_dir, 'azote-wallpaper2.png'))

    # Sway comes with some sample wallpapers
    if common.sway and os.path.isdir('/usr/share/backgrounds/sway'):
        common.sample_dir = '/usr/share/backgrounds/sway'

    if os.path.isdir('/usr/share/backgrounds/nwg-shell'):
        common.sample_dir = '/usr/share/backgrounds/nwg-shell'

    common.settings = Settings()
    if common.settings.clear_thumbnails:
        clear_thumbnails(clear_all=True)
        common.settings.clear_thumbnails = False

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
                        name, exe = '', ''

                        if os.path.isfile(filenames[i]):
                            with open(filenames[i]) as f:
                                rows = f.read().splitlines()
                                for row in rows:
                                    if row.startswith('Name='):
                                        name = row.split('=')[1]
                                    elif row.startswith('Name[{}]='.format(common.lang.lang[0:2])):
                                        name = row.split('=')[1]
                                    if row.startswith('Exec'):
                                        exe = row.split('=')[1].split()[0]
                                        continue
                            if name and exe:
                                data.append((name, exe))
                    common.associations[file_type] = data
                    """
                    Not necessarily all programs register jpg and jpeg extension (e.g. gimp registers jpeg only).
                    Let's create sets, join them and replace lists for both jpg and jpeg keys.
                    """
                    try:
                        jpg = set(common.associations['jpg'])
                        jpeg = set(common.associations['jpeg'])
                        together = jpg | jpeg
                        common.associations['jpg'] = together
                        common.associations['jpeg'] = together
                    except KeyError:
                        pass
                    # What if nothing found for 'jpg' or 'jpeg'?
                    if 'jpg' not in common.associations and 'jpeg' in common.associations:
                        common.associations['jpg'] = common.associations['jpeg']
                    elif 'jpeg' not in common.associations and 'jpg' in common.associations:
                        common.associations['jpeg'] = common.associations['jpg']

        log("Image associations: {}".format(common.associations), common.INFO)
    else:
        print('Failed opening /usr/share/applications/mimeinfo.cache')
        log("Failed creating image associations: /usr/share/applications/mimeinfo.cache file not found."
            " Setting feh as the only viewer.", common.ERROR)

    # Check if packages necessary to pick colours from the screen available
    try:
        magick = subprocess.run(['convert', '-version'], stdout=subprocess.DEVNULL).returncode == 0
    except FileNotFoundError:
        magick = False
        print('imagemagick package not found - color picked disabled')
    av = 'found' if magick else 'not found'
    log("Color picker: imagemagick library {}".format(av), common.INFO)

    if common.sway or common.env['wayland']:
        try:
            grim = subprocess.run(['grim', '-h'], stdout=subprocess.DEVNULL).returncode == 0
        except FileNotFoundError:
            grim = False
            print('grim package not found - color picked disabled')
        av = 'found' if grim else 'not found'
        log("Color picker/Wayland: grim package {}".format(av), common.INFO)

        try:
            slurp = subprocess.run(['slurp', '-h'], stdout=subprocess.DEVNULL).returncode == 0
        except FileNotFoundError:
            slurp = False
            print('slurp package not found - color picked disabled')
        av = 'found' if slurp else 'not found'
        log("Color picker/Wayland: slurp package {}".format(av), common.INFO)

        if magick and grim and slurp:
            log("Pick color from screen feature enabled", common.INFO)
            common.picker = True
        else:
            log("Pick color from screen feature needs imagemagick, grim and slurp packages packages", common.WARNING)
    else:
        try:
            maim = subprocess.run(['maim', '-v'], stdout=subprocess.DEVNULL).returncode == 0
        except FileNotFoundError:
            maim = False
            print('maim package not found - color picked disabled')
        av = 'found' if maim else 'not found'
        log("Color picker/X11: maim package {}".format(av), common.INFO)

        try:
            slop = subprocess.run(['slop', '-v'], stdout=subprocess.DEVNULL).returncode == 0
        except FileNotFoundError:
            slop = False
            print('slop package not found - color picked disabled')
        av = 'found' if slop else 'not found'
        log("Color picker/X11: slurp package {}".format(av), common.INFO)

        if magick and maim and slop:
            log("Pick color from screen - feature available", common.INFO)
            common.picker = True
        else:
            log("Pick color from screen feature needs imagemagick, maim and slop packages installed", common.WARNING)

    log("Environment: {}".format(common.env), common.INFO)

    # Find dotfiles
    if os.path.isfile(os.path.join(common.config_home, 'alacritty/alacritty.yml')):
        common.alacritty_config = os.path.join(common.config_home, 'alacritty/alacritty.yml')
    elif os.path.isfile(os.path.join(os.getenv('HOME'), '.alacritty.yml')):
        common.alacritty_config = os.path.join(os.getenv('HOME'), '.alacritty.yml')

    msg = common.alacritty_config if common.alacritty_config else 'not found'
    log('Alacritty config file: {}'.format(msg), common.INFO)
    if common.alacritty_config and not common.env['yaml']:
        log("python yaml module not found - alacritty.yml toolbox disabled", common.WARNING)
        print('python-yaml module not found - alacritty.yml toolbox disabled')

    if os.path.isfile(os.path.join(os.getenv('HOME'), '.Xresources')):
        common.xresources = os.path.join(os.getenv('HOME'), '.Xresources')
        log('{} file found'.format(common.xresources), common.INFO)
    else:
        log('~/.Xresources file not found', common.INFO)


def copy_backgrounds():
    used = []
    for item in common.display_boxes_list:
        fn = item.wallpaper_path.split("/")[-1]
        used.append(fn)
        fn = item.thumbnail_path.split("/")[-1]
        used.append(fn)

    # Clear unused files
    for file in os.listdir(common.bcg_dir):
        f2delete = os.path.join(common.bcg_dir, file)
        if file not in used:
            os.remove(f2delete)

    # Copy manipulated (flip, split) files from the temporary folder
    for file in os.listdir(common.tmp_dir):
        shutil.copyfile(os.path.join(common.tmp_dir, file), os.path.join(common.bcg_dir, file))


def hash_name(full_path):
    """
    Thumbnail path -> name (w/o extension)
    :param full_path: original file path
    :return: MD5-hashed path
    """
    return hashlib.md5(full_path.encode()).hexdigest()


def create_thumbnails(scr_path):
    common.progress_bar.hide()
    counter = 0
    inames = "-iname \"*."+"\" -o -iname \"*.".join(common.allowed_file_types)+"\""
    files=subprocess.check_output("find '%s' -mindepth 1 %s" %(scr_path, inames), shell=True).decode().split("\n")[:-1]
    for in_path in files:
        if file_allowed(in_path):
            counter += 1
    if counter > 0:
        # get all the files of allowed types from current path
        common.progress_bar.show()
        common.progress_bar.set_fraction(0.0)
        processed = 0
        for in_path in files:
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
        img.thumbnail(common.settings.thumb_size, Image.LANCZOS)

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

            flipped.thumbnail(common.settings.thumb_size, Image.LANCZOS)
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
        is_horizontal = width >= height
        if is_horizontal:
            part_width = width // num_parts
            part_height = height
        else:
            part_width = width
            part_height = height // num_parts
        paths_list = []
        for i in range(num_parts):
            if is_horizontal:
                box = (i * part_width, 0, i * part_width + part_width, part_height)
            else:
                box = (0, i * part_height, part_width, i * part_height + part_height)
            part = img.crop(box)
            img_path = os.path.join(common.bcg_dir, "part{}-{}".format(i, common.selected_wallpaper.filename))
            part.save(os.path.join(common.tmp_dir, "part{}-{}".format(i, common.selected_wallpaper.filename)), "PNG")

            part.thumbnail(common.settings.thumb_size, Image.LANCZOS)

            thumb_path = os.path.join(common.tmp_dir, "thumb-part{}-{}".format(i, common.selected_wallpaper.filename))

            part = expand_img(part)

            part.save(thumb_path, "PNG")
            paths = (img_path, thumb_path)
            paths_list.append(paths)
        return paths_list

    except Exception as e:
        log('Failed splitting {} - {}'.format(common.selected_wallpaper.source_path, e), common.ERROR)


def expand_img(image):
    # We want the thumbnail to be always in the same proportion. Let's expand if necessary.
    width, height = image.size
    border_h = (common.settings.thumb_width - width) // 2
    border_v = (common.settings.thumb_height - height) // 2
    if border_v > 0 or border_h > 0:
        # border = (border_h, border_v, border_h, border_v)
        # return ImageOps.expand(image, border=border)
        # Let's add checkered background instead of the black one
        background = Image.open('images/squares.jpg')
        background = background.resize(common.settings.thumb_size, Image.LANCZOS)
        background.paste(image, (border_h, border_v))
        return background
    else:
        return image


def scale_and_crop(item, image_path, width, height):
    img = Image.open(image_path)

    # We can either scale vertically & crop horizontally or scale horizontally and crop vertically
    new_height = int(img.size[0] * height / width)

    if new_height < img.size[1]:  # we need to scale to display width and crop vertical margins
        new_height = int(width * img.size[1] / img.size[0])
        # Choose the filter depending on if we're scaling down or up
        if new_height >= height:
            img = img.resize((width, new_height), Image.LANCZOS)
        else:
            img = img.resize((width, new_height), Image.BILINEAR)

        margin = (img.size[1] - height) // 2
        img = img.crop((0, margin, width, height + margin))

    elif new_height > img.size[1]:  # we need to scale to display height and crop horizontal margins
        new_width = int(img.size[0] * height / img.size[1])
        if new_width >= width:
            img = img.resize((new_width, height), Image.LANCZOS)
        else:
            img = img.resize((new_width, height), Image.BILINEAR)

        margin = (img.size[0] - width) // 2
        img = img.crop((margin, 0, width + margin, height))

    else:
        img = img.resize((width, height), Image.LANCZOS)

    img.save('{}-{}x{}{}'.format(os.path.splitext(image_path)[0], width, height, os.path.splitext(image_path)[1]))
    common.preview.refresh()


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


def clear_thumbnails(clear_all=False):
    files_in_use = os.listdir(common.settings.src_path)
    for i in range(len(files_in_use)):
        full_path = os.path.join(common.settings.src_path, files_in_use[i])
        files_in_use[i] = '{}.png'.format(hashlib.md5(full_path.encode()).hexdigest())

    number = 0
    for file in os.listdir(common.thumb_dir):
        if file not in files_in_use or clear_all:
            file_path = os.path.join(common.thumb_dir, file)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    number += 1
            except Exception as e:
                print(e)
    msg = 'thumbnails' if clear_all else 'unused thumbnails'
    print('\nAzote: {} {} deleted\n'.format(number, msg))


def convert_bytes(num):
    """
    https://stackoverflow.com/a/39988702/4040598
    """
    for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
        if num < 1024.0:
            return "%3.1f %s" % (num, x)
        num /= 1024.0


def create_pixbuf(size, color):
    image = Image.new("RGB", size, color)
    data = image.tobytes()
    w, h = image.size
    data = GLib.Bytes.new(data)
    return GdkPixbuf.Pixbuf.new_from_bytes(data, GdkPixbuf.Colorspace.RGB, False, 8, w, h, w * 3)


class Settings(object):
    def __init__(self):
        # Settings available in GUI we'll store in a pickle file
        self.file = os.path.join(common.data_home, "settings.pkl")

        self.src_path = common.sample_dir
        self.sorting = 'new'
        # Gtk.Menu() on sway is unreliable, especially called with right click
        self.custom_display = None
        self.old_thumb_width = None
        self.clear_thumbnails = False
        self.copy_as = '#rgb'
        self.color_dictionary = False
        self.image_menu_button = False
        self.track_files = True
        self.generic_display_names = False

        # Runtime config (json) location
        self.rc_file = os.path.join(common.azote_config_home, "azoterc")

        self.load()

    def load(self):
        save_needed = False
        if not os.path.isfile(self.file):
            log('Creating initial settings', common.INFO)
            self.save()

        with open(self.file, 'rb') as input_data:
            settings = pickle.load(input_data)

        # Do not read if it's inside old folders (before data migration); save default value instead
        if not settings.src_path == os.path.join(os.getenv('HOME'), '.azote/sample'):
            self.src_path = settings.src_path
        else:
            save_needed = True

        # In case the stored wallpapers directory no longer existed
        if not os.path.isdir(self.src_path):
            self.src_path = common.sample_dir
            save_needed = True

        try:
            self.sorting = settings.sorting  # 'new' 'old' 'az' 'za'
            log('Image sorting: {}'.format(self.sorting), common.INFO)
        except AttributeError:
            save_needed = True

        try:
            self.custom_display = settings.custom_display
            log('Custom display: {}'.format(self.custom_display), common.INFO)
        except AttributeError:
            save_needed = True

        try:
            self.old_thumb_width = settings.old_thumb_width
            log('Old thumbnail width: {}'.format(self.old_thumb_width), common.INFO)
        except AttributeError:
            save_needed = True

        try:
            self.copy_as = settings.copy_as
        except AttributeError:
            save_needed = True

        try:
            self.color_dictionary = settings.color_dictionary
        except AttributeError:
            save_needed = True

        try:
            self.image_menu_button = settings.image_menu_button
        except AttributeError:
            save_needed = True

        try:
            self.track_files = settings.track_files
        except AttributeError:
            save_needed = True

        try:
            self.generic_display_names = settings.generic_display_names
        except AttributeError:
            save_needed = True

        self.load_rc()
        # overwrite self.old_thumb_width with self.thumb_width if changed in azoterc
        if self.old_thumb_width != self.thumb_width:
            self.old_thumb_width = self.thumb_width
            save_needed = True
            log('New thumbnail width: {}, clearing existing thumbnails!'.format(self.thumb_width), common.WARNING)
            self.clear_thumbnails = True

        if save_needed:
            self.save()

    def save(self):
        with open(self.file, 'wb') as output:
            pickle.dump(self, output, pickle.HIGHEST_PROTOCOL)

    def load_rc(self):
        save_needed = False
        try:
            with open(self.rc_file, 'r') as f:
                rc = json.load(f)
        except FileNotFoundError:
            log('{} file not found, creating...'.format(self.rc_file), common.INFO)
            self.save_rc(set_defaults=True)

        try:
            with open(self.rc_file, 'r') as f:
                rc = json.load(f)
            log('{} file loaded'.format(self.rc_file), common.INFO)
        except Exception as e:
            log('rc file error: {}'.format(e), common.ERROR)

        try:
            self.thumb_width = int(rc['thumb_width'])
            # ignore too small values
            if self.thumb_width < 128:
                self.thumb_width = 128
        except KeyError:
            self.thumb_width = 240
            save_needed = True

        self.thumb_height = int(self.thumb_width * 135 / 240)
        self.thumb_size = (self.thumb_width, self.thumb_height)
        log('Thumbnail size: {}'.format(self.thumb_size), common.INFO)

        try:
            self.columns = int(rc['columns'])
        except KeyError:
            self.columns = 3
            save_needed = True
        log('Number of columns: {}'.format(self.columns), common.INFO)

        try:
            self.color_icon_w = int(rc['color_icon_w'])
        except KeyError:
            self.color_icon_w = 100
            save_needed = True

        try:
            self.color_icon_h = int(rc['color_icon_h'])
        except KeyError:
            self.color_icon_h = 50
            save_needed = True

        try:
            self.clip_prev_size = int(rc['clip_prev_size'])
        except KeyError:
            self.clip_prev_size = 30
            save_needed = True

        try:
            self.palette_quality = int(rc['palette_quality'])
        except KeyError:
            self.palette_quality = 10
            save_needed = True
        log('Palette quality: {} (10 by default, the less, the better & slower)'.format(self.palette_quality),
            common.INFO)

        try:
            self.tracking_interval_seconds = int(rc['tracking_interval_seconds'])
        except KeyError:
            self.tracking_interval_seconds = 5
            save_needed = True
        log('Files tracking interval: {} seconds'.format(self.tracking_interval_seconds),
            common.INFO)

        try:
            self.screen_measurement_delay = int(rc['screen_measurement_delay'])
        except KeyError:
            self.screen_measurement_delay = 300
            save_needed = True
        log('Screen measurement delay: {} ms'.format(self.screen_measurement_delay),
            common.INFO)

        if save_needed:
            self.save_rc()

    def save_rc(self, set_defaults=False):
        if set_defaults:
            self.thumb_width = 240
            self.columns = 3
            self.color_icon_w = 100
            self.color_icon_h = 50
            self.clip_prev_size = 30
            self.palette_quality = 10
            self.tracking_interval_seconds = 5
            self.screen_measurement_delay = 300

        rc = {'thumb_width': str(self.thumb_width),
              'columns': str(self.columns),
              'color_icon_w': str(self.color_icon_w),
              'color_icon_h': str(self.color_icon_h),
              'clip_prev_size': str(self.clip_prev_size),
              'palette_quality': str(self.palette_quality),
              'tracking_interval_seconds': str(self.tracking_interval_seconds),
              'screen_measurement_delay': str(self.screen_measurement_delay)}

        with open(self.rc_file, 'w') as f:
            json.dump(rc, f, indent=2)


def save_json(src_dict, path, en_ascii=False):
    with open(path, 'w') as f:
        json.dump(src_dict, f, indent=2, ensure_ascii=en_ascii)


def load_json(path):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(e)
        return {}


class Language(dict):
    def __init__(self, lang_from_args):
        super().__init__()
        self.dir_name = os.path.dirname(__file__)
        shell_data = load_shell_data()

        self.lang = os.getenv("LANG").split(".")[0] if not shell_data["interface-locale"] else shell_data[
            "interface-locale"]

        if lang_from_args:
            self.lang = lang_from_args
            log("Lang: '{}' (from args)".format(self.lang), common.INFO)
        else:
            log("Lang: '{}'".format(self.lang), common.INFO)

        base_dict = load_json(os.path.join(self.dir_name, "langs", "en_US.json".format(self.lang)))
        for key in base_dict:
            self[key] = base_dict[key]

        if self.lang != "en_US":
            user_dict = load_json(os.path.join(self.dir_name, "langs", "{}.json".format(self.lang)))
            if len(user_dict) == 0:
                log("No translations found for '{}'".format(self.lang), common.INFO)
            else:
                log("{} translation phrases found in '{}'".format(len(user_dict), self.lang), common.INFO)
                for key in user_dict:
                    self[key] = user_dict[key]


def get_shell_data_dir():
    data_dir = ""
    home = os.getenv("HOME")
    xdg_data_home = os.getenv("XDG_DATA_HOME")

    if xdg_data_home:
        data_dir = os.path.join(xdg_data_home, "nwg-shell/")
    else:
        if home:
            data_dir = os.path.join(home, ".local/share/nwg-shell/")

    return data_dir


def load_shell_data():
    shell_data_file = os.path.join(get_shell_data_dir(), "data")
    shell_data = load_json(shell_data_file) if os.path.isfile(shell_data_file) else {}

    defaults = {
        "interface-locale": ""
    }

    for key in defaults:
        if key not in shell_data:
            shell_data[key] = defaults[key]

    return shell_data
