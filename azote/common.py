CRITICAL = 'critical'
ERROR = 'error'
WARNING = 'warning'
INFO = 'info'
DEBUG = 'debug'

env = {"wm": '', "i3ipc": False, "xrandr": False}
sway = False

preview = None
status_bar = None
buttons_list = None
display_boxes_list = None
selected_wallpaper = None
selected_picture_label = None

cols = 3                # number of columns in pictures preview

allowed_file_types = ['jpg', 'jpeg', 'png']

app_dir = ''            # ~/.azote
thumb_dir = ''          # ~/.azote/thumbnails
tmp_dir = ''            # ~/.azote/temp
bcg_dir = ''            # ~/.azote/backgrounds-sway or ~/.azote/backgrounds-feh
log_file = ''           # ~/.azote/log.txt
cmd_file = ''           # ~/.azote/command.sh
logging_enabled = True
displays = None         # detected displays details

settings = None         # object saved to / restored from ~/.azote/settings.pkl
