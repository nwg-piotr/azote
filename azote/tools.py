import os
import glob
import hashlib
import logging
from PIL import Image, ImageOps
import common
import pickle
import subprocess
from shutil import copyfile


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


def set_env():

    # application folder
    common.app_dir = os.path.join(os.getenv("HOME"), ".azote")
    print(common.app_dir)
    if not os.path.isdir(common.app_dir):
        os.mkdir(common.app_dir)

    # thumbnails folder
    common.thumb_dir = os.path.join(common.app_dir,"thumbnails")
    if not os.path.isdir(common.thumb_dir):
        os.mkdir(common.thumb_dir)

    # logging
    common.log_file = os.path.join(common.app_dir, "log.txt")
    logging.basicConfig(filename=common.log_file, format='%(asctime)s %(levelname)s: %(message)s', filemode='w',
                        level=logging.INFO)

    # command file
    common.cmd_file = os.path.join(common.app_dir, "command.sh")

    log('Azote launched', common.INFO)

    # check if Wayland available
    common.wm = subprocess.check_output("wmctrl -m | grep 'Name' | awk '{print $2}'", shell=True).decode("utf-8").strip()
    log("WM: {}".format(common.wm), common.INFO)

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
    common.bcg_dir = os.path.join(common.app_dir, "backgrounds")
    if not os.path.isdir(common.bcg_dir):
        os.mkdir(common.bcg_dir)

    common.settings = Settings()


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
    # get all the files of allowed types from current path
    for extension in common.allowed_file_types:
        for in_path in glob.glob(os.path.join(scr_path, "*.{}".format(extension))):
            if file_allowed(in_path):
                thumb_name = "{}.png".format(hash_name(in_path))
                dest_path = os.path.join(common.thumb_dir, thumb_name)
                if not os.path.isfile(dest_path):
                    create_thumbnail(in_path, dest_path, thumb_name)
                elif is_newer(in_path, dest_path):
                    create_thumbnail(in_path, dest_path, thumb_name, True)


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
    common.status_bar.push(0, "{} thumbnails in cache ({})".format(num_files, convert_bytes(total_size)))


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
        print("Settings file", self.file)

        # Try to find user's Pictures directory
        user_dirs = os.path.join(os.getenv("HOME"), '.config/user-dirs.dirs')
        if os.path.isfile(user_dirs):
            lines = open(user_dirs, 'r').read().rstrip().splitlines()
            for line in lines:
                if line.startswith('XDG_PICTURES_DIR'):
                    pic_dir = os.path.join(os.getenv("HOME"), line.split('/')[1][:-1])
                    if os.path.isdir(pic_dir):
                        print(pic_dir)
                        self.src_path = pic_dir

                    else:
                        self.src_path = os.getenv("HOME")
        else:
            self.src_path = os.getenv("HOME")

        self.load()

    def load(self):
        if not os.path.isfile(self.file):
            log('Creating initial settings', common.INFO)
            self.save()

        with open(self.file, 'rb') as input_data:
            settings = pickle.load(input_data)

        self.src_path = settings.src_path  # holds selected path to source pictures

    def save(self):
        with open(self.file, 'wb') as output:
            pickle.dump(self, output, pickle.HIGHEST_PROTOCOL)
