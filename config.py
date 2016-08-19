__author__ = 'william'

IMAGE_UPLOAD_FOLDER = 'profile_images'
DOCUMENT_UPLOAD_FOLDER = '/Users/william/Desktop/dmsapp/documents/current_versions'
DOCUMENT_ARCHIVE_FOLDER = '/Users/william/Desktop/dmsapp/documents/old_versions'

RESTRICTED_CHARACTERS = ['[', ']', '{', '}']

SECRET_KEY = '\xa4\xcaG \x8f\x1c\x94i\xd8P$9\x11\x8b,\xbdV\x9f\xc5\xf3\x1cL\xcev'

DEFAULT_PROFILE_PHOTO = 'default.png'
ALLOWED_IMAGE_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
ALLOWED_DOCUMENT_EXTENSIONS = set(['txt', 'pdf', 'docx', 'doc', 'ppt', 'xlsx'])

STATIC_PATH = '/static/'

SESSION_CHECKING_ENDPOINT_EXCEPTIONS = ['/register', '/login']

DEBUG=True

SESSION_LIFETIME = 30