CRITICAL = 'critical'
ERROR = 'error'
WARNING = 'warning'
INFO = 'info'
DEBUG = 'debug'

wayland = False
preview = None
status_bar = None
buttons_list = None
selected_thumbnail = None
selected_picture_label = None

cols = 3                # number of columns in pictures preview

allowed_file_types = ['jpg', 'jpeg', 'png']

app_dir = ''            # ~/.azote
thumb_dir = ''          # ~/.azote/thumbnails
bcg_dir = ''            # ~/.azote/backgrounds
log_file = ''           # ~/.azote/log.txt
logging_enabled = True
outputs = None          # detected display names

settings = None         # object saved to / restored from ~/.azote/settings.pkl
