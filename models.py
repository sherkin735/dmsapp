__author__ = 'william'

from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey, Table
from database import Base
from sqlalchemy.orm import relationship
from sqlalchemy.orm.session import object_session
import shutil, os


DocumentUser = Table("DocumentUser",
                    Base.metadata,
                    Column("user_id", Integer, ForeignKey("User.id"), primary_key=True),
                    Column("document_id", Integer, ForeignKey("Document.id"), primary_key=True))


DocumentTag = Table("DocumentTag",
                    Base.metadata,
                    Column("tag_id", Integer, ForeignKey("Tag.id"), primary_key=True),
                    Column("document_id", Integer, ForeignKey("Document.id"), primary_key=True))


class User(Base):
    __tablename__ = "User"
    id = Column(Integer, primary_key=True)
    username = Column(String(30), unique=True)
    password = Column(String(20), unique=False)
    name = Column(String(30), unique=False)
    profile_photo = Column(String(80), unique=False)
    access_level = Column(Integer, unique=False)
    password_try_count = Column(Integer, unique=False)
    creation_date = Column(DateTime, unique=False)
    user_access_exceptions = relationship('Document', secondary=DocumentUser, backref='User')

    def __init__(self, username=None, password=None, name=None, profile_photo=None, access_level=3, password_try_count=0, creation_date=None):
        self.username = username
        self.password = password
        self.name = name
        self.profile_photo = profile_photo
        #access level defaults to 3 (intermediate)
        self.access_level = access_level
        self.password_try_count = password_try_count
        self.creation_date = creation_date

    def __repr__(self):
        return '<User %r' % (self.username)

    def to_dict(self):
        return {'id': self.id,
                'username': self.username,
                'name': self.name,
                'access_level': self.access_level,
                'password_try_count': self.password_try_count,
                'password': self.password
                }

    def to_ajax_dict(self):
        return {'id': self.id,
                'text': self.username
                }


class Document(Base):

    DOCUMENT_UPLOAD_FOLDER = 'documents/current_versions'
    DOCUMENT_ARCHIVE_FOLDER = 'documents/old_versions'

    __tablename__ = "Document"
    id = Column(Integer, primary_key=True)
    document_name = Column(String(30), unique=True)
    file_name = Column(String(40), unique=False)
    file_extension = Column(String(5), unique=False)
    uploader = Column(String(40), unique=False)
    upload_date = Column(DateTime, unique=False)
    version = Column(String(3), unique=False)
    access_level = Column(Integer, unique=False)
    major_category = Column(String(30), unique=False)
    #hashing algorithm used is MD5 which produces 128 bit hashes - 32 characters in length
    #md5 yields hex digits which are 4 bits as opposed to 8 hence 128/4=32
    hash = Column(String(32), unique=True)
    last_edited_by = Column(String(40), unique=False)
    archived = Column(Boolean, unique=False)
    user_access_exceptions = relationship('User', secondary=DocumentUser, backref='Document')
    tags = relationship('Tag', secondary=DocumentTag, backref='Document')
    changes = relationship('ChangeLog')

    def __init__(self, document_name=None, file_name=None, uploader=None, upload_date=None, version=None, last_edited_by=None,
    archived=None, hash=None, file_extension=None, access_level=None, major_category=None):
        self.document_name = document_name
        self.file_name = file_name
        self.uploader = uploader
        self.upload_date = upload_date
        self.version = version
        self.last_edited_by = last_edited_by
        self.archived = archived
        self.hash = hash
        self.file_extension = file_extension
        self.access_level = access_level
        self.major_category = major_category


    def increment_version_number(self):
        self.version = str(float(self.version) + 0.1)


    def archive_document(self, archive):
        locations = {'old' : os.path.join(self.DOCUMENT_UPLOAD_FOLDER, self.file_name),
                     'new' : os.path.join(self.DOCUMENT_ARCHIVE_FOLDER, self.file_name.split('.')[0] + "_v-{0}".format(self.version.replace('.', '-')) + '.' + self.file_name.split('.')[-1])
        }
        try:
            if archive:
                print('OLD LOCATION: {0}'.format(locations['old']))
                print('NEW LOCATION: {0}'.format(locations['new']))
                filename = self.file_name.split('.')[0] + "_v-{0}".format(self.version.replace('.', '-')) + '.' + self.file_name.split('.')[-1]
                shutil.move(locations['old'], locations['new'])
            else:
                filename = self.DOCUMENT_UPLOAD_FOLDER + '_'.join(self.file_name.split('_')[0:-1]) + self.file_name.split('.')[-1]
                shutil.move(locations['new'], filename)
            return filename
        except Exception, ex:
            print('Archive exception')
            print ex
        return False


    def __repr__(self):
        return '<Document %r' % (self.document_name)



class Tag(Base):
    __tablename__ = "Tag"
    id = Column(Integer, primary_key=True)
    text = Column(String(20), unique=True)
    documents = relationship('Document', secondary=DocumentTag, backref='Tag')

    def __init__(self, text=None):
        self.text = text

    def __repr__(self):
        return '<Tag %r' % (self.text)

    def to_dict(self):
        return {'id': self.id,
                'text': self.text}

class Checkout(Base):
    __tablename__ = "Checkout"
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("Document.id"), nullable=False)
    checkout_time = Column(DateTime, unique=False)
    checkout_username = Column(String(40), unique=False)
    document_version = Column(String(3), unique=False)

    def __init__(self, document_id=None, checkout_time=None, checkout_username=None, document_version=None):
        self.document_id = document_id
        self.checkout_time = checkout_time
        self.checkout_username = checkout_username
        self.document_version = document_version

    def __repr__(self):
        return '<Checkout_ID %r' % (self.id)


class ChangeLog(Base):
    __tablename__ = "ChangeLog"
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("Document.id"))
    change_username = Column(String(40), unique=False)
    document_name = Column(String(30), unique=False)
    # store as string rather than float as queries on floats dont work properly and return none
    document_version = Column(String(3), unique=False)
    checkin_date = Column(DateTime, unique=False)
    comments = Column(String(200), unique=False)
    file_name = Column(String(40), unique=False)


    def __init__(self, document_id=None, checkin_date=None, comments=None, change_username=None, document_name=None, file_name=None, document_version=None):
        self.document_id = document_id
        self.checkin_date = checkin_date
        self.comments = comments
        self.change_username = change_username
        self.document_name = document_name
        self.file_name = file_name
        self.document_version = document_version

    def __repr__(self):
        return '<Change ID %r' % (self.id)

    def nice_date_format(self):
        return str(self.checkin_date).split(' ')

    def creation_event(self):
        if self.comments == 'Initial upload of document':
            return True
        return False