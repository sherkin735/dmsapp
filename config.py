__author__ = 'william'
import sys
import os

if sys.platform == 'darwin':
    IMAGE_UPLOAD_FOLDER = 'profile_images'
    DOCUMENT_UPLOAD_FOLDER = './documents/current_versions'
    DOCUMENT_ARCHIVE_FOLDER = './documents/old_versions'
    DEBUG=True
else:
    IMAGE_UPLOAD_FOLDER = './profile_images'
    DOCUMENT_UPLOAD_FOLDER = '/var/www/dmsapp/documents/current_versions'
    DOCUMENT_ARCHIVE_FOLDER = '/var/www/dmsapp/documents/old_versions'
    DEBUG=False

RESTRICTED_CHARACTERS = ['[', ']', '{', '}']

SECRET_KEY = '\xdd\x0fN\x92n\xdc\xd6x\xd2\xce\x14\x07 \xcc\xde\xe2\x02\xce\xfaHj\xf0\xed\xe0'

DEFAULT_PROFILE_PHOTO = 'default.png'
ALLOWED_IMAGE_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
ALLOWED_DOCUMENT_EXTENSIONS = set(['txt', 'pdf', 'docx', 'doc', 'ppt', 'xlsx'])

STATIC_PATH = '/static/'

SESSION_CHECKING_ENDPOINT_EXCEPTIONS = ['/register', '/login']

SESSION_LIFETIME = 30