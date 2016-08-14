__author__ = 'william'

IMAGE_UPLOAD_FOLDER = 'profile_images'
DOCUMENT_UPLOAD_FOLDER = 'documents/current_versions'
DOCUMENT_ARCHIVE_FOLDER = 'documents/old_versions'

RESTRICTED_CHARACTERS = ['[', ']', '{', '}']

SECRET_KEY =

DEFAULT_PROFILE_PHOTO = 'default.png'
ALLOWED_IMAGE_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
ALLOWED_DOCUMENT_EXTENSIONS = set(['txt', 'pdf', 'docx', 'doc', 'ppt', 'xlsx'])

SESSION_CHECKING_ENDPOINT_EXCEPTIONS = ['/register', '/login']

DEBUG=True

SESSION_LIFETIME = 30