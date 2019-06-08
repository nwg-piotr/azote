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

    log('Launched', common.INFO)
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
            log('Pictures dir: {}'.format(self.src_path), common.INFO)
            self.save()

        with open(self.file, 'rb') as input_data:
            settings = pickle.load(input_data)

        self.src_path = settings.src_path  # holds selected path to source pictures

    def save(self):
        with open(self.file, 'wb') as output:
            pickle.dump(self, output, pickle.HIGHEST_PROTOCOL)
