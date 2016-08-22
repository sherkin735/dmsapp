__author__ = 'william'

import os
from config import DOCUMENT_UPLOAD_FOLDER, DOCUMENT_ARCHIVE_FOLDER, IMAGE_UPLOAD_FOLDER

def clear_files():
    folders = [DOCUMENT_UPLOAD_FOLDER, DOCUMENT_ARCHIVE_FOLDER, IMAGE_UPLOAD_FOLDER]
    for folder in folders:
        for file in os.listdir(folder):
            if 'default.png' not in file:
                file_path = os.path.join(folder, file)
                try:
                    if os.path.isfile(file_path):
                        print('Removing file at location: {0}'.format(file_path))
                        os.unlink(file_path)
                except Exception, ex:
                    print('Exception encountered while removing document files'.format(ex))
            else:
                print('Skipping default.png')
    print('File removal complete.')