CRITICAL = 'critical'
ERROR = 'error'
WARNING = 'warning'
INFO = 'info'
DEBUG = 'debug'

wayland = False
preview = None
buttons_list = None
selected_image = None
selected_picture_label = None

allowed_file_types = ['jpg', 'jpeg', 'png']

app_dir = ''            # ~/.azote
thumb_dir = ''          # ~/.azote/thumbnails
log_file = ''           # ~/.azote/log.txt
logging_enabled = True
outputs = None          # detected display names

settings = None         # object saved to / restored from ~/.azote/settings.pkl
