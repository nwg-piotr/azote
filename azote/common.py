CRITICAL = 'critical'
ERROR = 'error'
WARNING = 'warning'
INFO = 'info'
DEBUG = 'debug'

allowed_file_types = ['jpg', 'jpeg', 'png']

app_dir = ''            # ~/.azote
thumb_dir = ''          # ~/.azote/thumbnails
log_file = ''           # ~/.azote/log.txt
logging_enabled = True
src_paths = []          # source pictures: array of paths
outputs = None          # detected display names

settings = None         # object saved to / restored from ~/.azote/settings.pkl
