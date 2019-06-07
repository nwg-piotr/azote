import os
import glob
import hashlib
import logging
from PIL import Image
import common
import pickle


def set_env():
    # application folder
    common.app_dir = os.getenv("HOME") + "/.azote"
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

    common.settings = Settings()


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


def hash_name(full_path):
    """
    Returns thumbnail name
    :param full_path: original file path
    :return: MD5-hashed path + .jpg extension
    """
    return hashlib.md5(full_path.encode()).hexdigest()


def create_thumbnails(scr_path):
    # get all the jpg files from current path
    for in_path in glob.glob(os.path.join(scr_path, "*.jpg")):
        if file_allowed(in_path):
            thumb_name = "{}.png".format(hash_name(in_path))
            dest_path = os.path.join(common.thumb_dir, thumb_name)
            if not os.path.isfile(dest_path):
                create_thumbnail(in_path, dest_path, thumb_name)
                log('New thumb {} -> {}'.format(in_path, thumb_name), common.INFO)
            elif is_newer(in_path, dest_path):
                create_thumbnail(in_path, dest_path, thumb_name)
                log('Refresh {} -> {}'.format(in_path, thumb_name), common.INFO)

    for in_path in glob.glob(os.path.join(scr_path, "*.png")):
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
        img.thumbnail((256, 256), Image.ANTIALIAS)
        img.save(dest_path, "PNG")
        log('{}: {} -> {}'.format(action, in_path, thumb_name), common.INFO)
    except Exception as e:
        log('{} - {}'.format(action, e), common.ERROR)


def is_newer(in_path, dest_path):
    return os.path.getmtime(in_path) > os.path.getmtime(dest_path)


def file_allowed(path):
    ext = path.split('.')[-1].lower()
    return ext in common.allowed_file_types


class Settings(object):
    def __init__(self):
        self.file = os.path.join(common.app_dir, "settings.pkl")
        self.src_paths = ['/home/piotr/Obrazy/Wallpapers', '/home/piotr/Obrazy']

        self.load()

    def load(self):
        if not os.path.isfile(self.file):
            self.save()

        with open(self.file, 'rb') as input_data:
            settings = pickle.load(input_data)

        self.src_paths = settings.src_paths  # holds selected paths to source pictures

    def save(self):
        with open(self.file, 'wb') as output:
            pickle.dump(self, output, pickle.HIGHEST_PROTOCOL)
