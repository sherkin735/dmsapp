__author__ = 'william'

from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey, Table
from database import Base
from sqlalchemy.orm import relationship
import shutil

class User(Base):
    __tablename__ = "User"
    user_id = Column(Integer, primary_key=True)
    username = Column(String(30), unique=True)
    password = Column(String(20), unique=False)
    name = Column(String(30), unique=False)
    profile_photo = Column(String(80), unique=False)

    def __init__(self, username=None, password=None, name=None, profile_photo=None):
        self.username = username
        self.password = password
        self.name = name
        self.profile_photo = profile_photo


    def __repr__(self):
        return '<User %r' % (self.username)

DocumentTag = Table("DocumentTag",
                    Base.metadata,
                    Column("tag_id", Integer, ForeignKey("Tag.tag_id"), primary_key=True),
                    Column("document_id", Integer, ForeignKey("Document.document_id"), primary_key=True))

class Document(Base):

    DOCUMENT_UPLOAD_FOLDER = 'documents/current_versions'
    DOCUMENT_ARCHIVE_FOLDER = 'documents/old_versions'

    __tablename__ = "Document"
    document_id = Column(Integer, primary_key=True)
    document_name = Column(String(30), unique=True)
    file_name = Column(String(30), unique=False)
    uploader = Column(String(40), unique=False)
    upload_date = Column(DateTime, unique=False)
    version = Column(Float, unique=False)
    #hashing algorithm used is MD5 which produces 128 bit hashes - 32 characters in length
    #md5 yields hex digits which are 4 bits as opposed to 8 hence 128/4=32
    hash = Column(String(32), unique=True)
    last_edited_by = Column(String(40), unique=False)
    archived = Column(Boolean, unique=False)
    tags = relationship('Tag', secondary=DocumentTag, backref='Document')

    def __init__(self, document_name=None, file_name=None, uploader=None, upload_date=None, version=None, last_edited_by=None,
    archived=None, hash=None):
        self.document_name = document_name
        self.file_name = file_name
        self.uploader = uploader
        self.upload_date = upload_date
        self.version = version
        self.last_edited_by = last_edited_by
        self.archived = archived
        self.hash = hash


    def increment_version_number(self):
        self.version += 0.1


    def archive_document(self, archive):
        locations = {'old' : self.DOCUMENT_UPLOAD_FOLDER + "/" + self.file_name,
                     'new' : self.DOCUMENT_ARCHIVE_FOLDER + "/" + self.file_name.split('.')[0] + "_v-{0}".format(str(self.version).replace('.', '-')) + '.' + self.file_name.split('.')[-1]}
        try:
            if archive:
                shutil.move(locations['old'], locations['new'])
            else:
                shutil.move(locations['new'], locations['old'])
            return True
        except Exception, ex:
            print ex
        return False


    def __repr__(self):
        return '<Document %r' % (self.document_name)


class Tag(Base):
    __tablename__ = "Tag"
    tag_id = Column(Integer, primary_key=True)
    text = Column(String(20), unique=True)
    documents = relationship('Document', secondary=DocumentTag, backref='Tag')

    def __init__(self, text=None):
        self.text = text

    def __repr__(self):
        return '<Tag %r' % (self.text)

class Checkout(Base):
    __tablename__ = "Checkout"
    checkout_id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("Document.document_id"), nullable=False)
    checkout_time = Column(DateTime, unique=False)
    checkout_username = Column(String(40), unique=False)
    document_version = Column(Float, unique=False)

    def __init__(self, document_id=None, checkout_time=None, checkout_username=None, document_version=None):
        self.document_id = document_id
        self.checkout_time = checkout_time
        self.checkout_username = checkout_username
        self.document_version = document_version

    def __repr__(self):
        return '<Checkout_ID %r' % (self.document_id)


class ChangeLog(Base):
    __tablename__ = "ChangeLog"
    #todo add fields for username and filename and friendly name
    changelog_id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("Document.document_id"), nullable=False)
    change_username = Column(String(40), unique=False)
    document_name = Column(String(30), unique=False)
    checkin_date = Column(DateTime, unique=False)
    comments = Column(String(200), unique=False)

    def __init__(self, document_id=None, checkin_date=None, comments=None, change_username=None, document_name=None):
        self.document_id = document_id
        self.checkin_date = checkin_date
        self.comments = comments
        self.change_username = change_username
        self.document_name = document_name

    def __repr__(self):
        return '<Change ID %r' % (self.changelog_id)

    def nice_date_format(self):
        return str(self.checkin_date).split(' ')

    def creation_event(self):
        if self.comments == 'Initial upload of document':
            return True
        return False