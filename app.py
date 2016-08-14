import os, time, datetime, shutil
from flask import Flask, jsonify, render_template, redirect, url_for, flash, request, session, send_from_directory, send_file, make_response
from werkzeug.utils import secure_filename
from models import Document, Checkout, Tag, ChangeLog
from hashlib import md5
from datetime import timedelta

# Application config options
# todo: Maybe externalise these options to a config file which also holds DB connection params etc

from database import db_session, engine
from models import User

app = Flask(__name__)
app.config.from_pyfile('config.py')


#method is run before every request, thus refreshing the session lifetime,
#the session expires after 30 minutes of inactivity i.e. no new requests
#have been received by the server for that session
@app.before_request
def session_expiry():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=(app.config['SESSION_LIFETIME']))


@app.before_request
def check_session():
    if 'username' in session or request.url_rule.rule in app.config['SESSION_CHECKING_ENDPOINT_EXCEPTIONS']:
        return None
        print("rendered from here")
    return render_template('login.html')


@app.route("/home")
def home():
    return render_template("index.html")


@app.route("/")
def slash():
    return redirect(url_for("home"))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if check_user_details(request.form.get('username'), request.form.get('password')):
            return redirect(url_for('home'))
        else:
            flash("Invalid credentials. Please try again.")
    return render_template('login.html')


@app.route("/logout")
def logout():
    if session.get("name"):
        session.clear()
        flash('Logout successful.')
    return redirect(url_for('login'))


def check_user_details(username, password):
    obj = User.query.filter(User.username == username).first()
    if obj:
        if obj.password == password:
            session['username']=obj.username
            session['name']=obj.name
            session['profile_photo'] = obj.profile_photo
            return True
    return False


def account_exists(username):
    obj = User.query.filter(User.username == username).first()
    if obj:
        return True
    return False


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if not request.form.get('username') or not request.form.get('password') or not request.form.get('name'):
            flash('Not all fields were filled out. Please check you have supplied all requested information.')
        elif account_exists(request.form.get('username')):
                flash('An account has already been registered for this email address.')
        else:
            photo_path = file_upload(request.files.get('profile_photo'), app.config['IMAGE_UPLOAD_FOLDER'], app.config['ALLOWED_IMAGE_EXTENSIONS'])
            new_user = User(request.form.get('username'), request.form.get('password'), request.form.get('name'), photo_path)
            db_session.add(new_user)
            db_session.commit()
            flash('New user created successfully.')
            # todo: remove error variable from register.html and replace with flashed mesages
    return render_template('register.html')


@app.route('/profile_images/<filename>')
def serve_image(filename):
    return send_from_directory(app.config['IMAGE_UPLOAD_FOLDER'], filename)


@app.route('/profile', methods = ['GET', 'POST'])
def profile():
    if request.method == 'POST':
        current_user = User.query.filter_by(username=session['username']).first()
        # :todo I think this solves the issue of users changing their username to one that is already taken.
        # :todo If the current user is the same as the requested username the user can pick the name as they already own it - i.e. there will be no change
        if session['username'] != request.form['username'] and account_exists(request.form['username']):
            flash("An account already exists for this username")
        elif request.form['username'] != "":
            current_user.username = request.form['username']
        if current_user.name != request.form['name'] and request.form['name'] != "":
            current_user.name = request.form['name']
        if request.form['password'] != "" and current_user.password != request.form.password:
            current_user.password = request.form['password']
        new_photo = session['profile_photo']
        db_session.commit()
        session['name'] = request.form['name']
        session['username'] = request.form['username']
        #session['profile_photo'] = request.profile_photo
        flash("User details were successfully updated.")
    return render_template('profile.html')


def allowed_file(filename, extensions):
    return '.' in filename and filename.rsplit('.', 1)[1] in extensions


def file_upload(upload_file, destination_folder, extensions):
    if not upload_file:
        upload_file = app.config['DEFAULT_PROFILE_PHOTO']
        path_to_file = os.path.join(app.config['IMAGE_UPLOAD_FOLDER'], upload_file)
    elif allowed_file(upload_file.filename, extensions):
        filename = secure_filename(upload_file.filename)
        path_to_file = os.path.join(destination_folder, filename)
        upload_file.save(path_to_file)
    else:
        path_to_file = os.path.join(app.config['IMAGE_UPLOAD_FOLDER'], app.config['DEFAULT_PROFILE_PHOTO'])
    return path_to_file


def remove_file(file, destination_folder):
    pass


def get_document_hash(file):
    hash_md5 = md5()
    for chunk in iter(lambda: file.read(4096), b""):
        hash_md5.update(chunk)
    return hash_md5.hexdigest()


def doc_previously_uploaded(hash_value):
    document = Document.query.filter_by(hash=hash_value).first()
    if document:
        return document.document_name
    return None


def sanitise_filename(filename):
    filename = filename.encode('utf-8').translate(None, ''.join(app.config['RESTRICTED_CHARACTERS']))
    return filename.replace(' ', '_')


@app.route('/document_upload', methods=['GET', 'POST'])
def document_upload():
    if request.method == 'POST':
        tags = (request.form.getlist('tags'))
        saved_tags = Tag.query.filter(Tag.text.in_(tags)).all()
        for tag in saved_tags:
            tags.remove(tag.text)
        if request.form.get('document_name') and request.form.get('tags') and request.files.get('document'):
            doc_hash = get_document_hash(request.files['document'])
            doc_name = doc_previously_uploaded(doc_hash)
            if not doc_name:
                todays_date_time = datetime.datetime.today()
                request.files['document'].filename = sanitise_filename(request.files['document'].filename)
                result = file_upload(request.files['document'], app.config['DOCUMENT_UPLOAD_FOLDER'], app.config['ALLOWED_DOCUMENT_EXTENSIONS'])
                document = Document(document_name=request.form['document_name'], file_name=request.files['document'].filename,
                uploader=session['username'], upload_date=todays_date_time,
                version=1.0, last_edited_by=session['username'], archived=False, hash=doc_hash)
                for tag in tags:
                    document.tags.append(Tag(tag))
                if result:
                    db_session.add(document)
                    db_session.commit()
                    upload_event = ChangeLog(document.document_id, todays_date_time, "Initial upload of document", session['username'], document.document_name)
                    db_session.add(upload_event)
                    db_session.commit()
                    flash("Document saved successfully")
                if saved_tags:
                    for tag in saved_tags:
                        engine.execute("INSERT INTO DocumentTag (tag_id, document_id) VALUES ({0}, {1})".format(tag.tag_id, document.document_id))
            else:
                flash("This document has been uploaded previously. Please search for the following document: {0}".format(doc_name))
        else:
            flash("Not all required fields were filled out. Please ensure all fields have been filled and try again")
    return render_template('document_upload.html')


@app.route("/document_search", methods=['GET', 'POST'])
def document_search():
    tagged_documents = []
    named_documents = []
    if request.method == 'POST':
        doc_name = request.form.get('document_name')
        tags = request.form.getlist('document_tags')
        if doc_name:
            named_documents = Document.query.filter(Document.document_name.like("%{0}%".format(doc_name))).all()
        else:
             flash("The document name must be provided")
        if tags:
            for tag in tags:
                docs = Document.query.filter(Document.tags.any(text=tag)).all()
                for doc in docs:
                    if doc not in tagged_documents:
                        tagged_documents.append(doc)
            print(tagged_documents)
    all_docs = set(named_documents + tagged_documents)
    if not all_docs:
        all_docs = None
    else:
        all_docs = [doc for doc in all_docs if doc != []]
    return render_template("document_search.html", relevant_docs=all_docs)

def checkout_document(document_id, version):
    try:
        previous_checkout = Checkout.query.filter(Checkout.checkout_username==session['username']).filter(Checkout.document_id== document_id).first()
        if not previous_checkout:
            checkout_date_time = datetime.datetime.today()
            chkout = Checkout(document_id, checkout_date_time, session['username'], version)
            db_session.add(chkout)
            db_session.commit()
            return True
    except Exception, ex:
        print(ex)
    return False


def checkin_document():
    try:
        request.files['document'].filename = sanitise_filename(request.files['document'].filename)
        document = Document.query.filter(Document.document_id == request.form.get("doc_id")).first()
        # the names for the select items are auto generated by concatting tags_for_ and the doc_id
        tags = (request.form.getlist('tags_for_'+str(document.document_id)))
        saved_tags = Tag.query.filter(Tag.text.in_(tags)).all()
        saved_tags_text = [tag.text for tag in saved_tags]
        for tag in tags:
            if tag not in saved_tags_text:
                document.tags.append(Tag(tag))
        #update the hash value of the document
        document.hash = get_document_hash(request.files['document'])
        #increment document version number
        document.archive_document(True)
        document.increment_version_number()
        result = file_upload(request.files['document'], app.config['DOCUMENT_UPLOAD_FOLDER'], app.config['ALLOWED_DOCUMENT_EXTENSIONS'])
        document.file_name = request.files['document'].filename
        if result:
            db_session.commit()
            flash("The document was updated successfully")
        else:
            #upload fails - move back to original locations
            document.archive_document(archive=False)
        checkin_date_time = datetime.datetime.today()
        changes = ChangeLog(document.document_id, checkin_date_time, request.form.get('comments'), session['username'], document.document_name)
        db_session.add(changes)
        checkout_record=Checkout.query.filter(Checkout.checkout_username==session['username']).filter(Checkout.document_id==document.document_id).first()
        db_session.delete(checkout_record)
        db_session.commit()
        return True
    except Exception, ex:
        print(ex)
    return False


@app.route("/get_tags")
def get_tags():
    doc_id = request.args.get("document_id")
    tags = Tag.query.filter(Tag.documents.any(document_id=doc_id)).all()
    return jsonify(result=[tag.text for tag in tags])


@app.route("/downloads/<document_id>")
def download_document(document_id):
    doc = Document.query.filter(Document.document_id == document_id).first()
    filename = doc.file_name
    version = doc.version
    if checkout_document(document_id, version):
        return send_from_directory(app.config['DOCUMENT_UPLOAD_FOLDER'], filename, as_attachment=True)
    else:
        return "There was an error in checking out the requested document. Please try again."


@app.route("/my-documents", methods=['GET', 'POST'])
def my_documents():
    #todo: version numbers increment even upon failed updates. bundle all activities together
    if request.method == 'POST':
        checkin_document()
    checked_documents = Checkout.query.filter(Checkout.checkout_username == session['username']).all()
    doc_ids = []
    for doc in checked_documents:
        doc_ids.append(doc.document_id)
    #fix here so _in clauses cannot run on empty sequences
    all_docs = Document.query.filter(Document.document_id.in_(doc_ids)).all()
    all_checkouts = Checkout.query.filter(Checkout.document_id.in_(doc_ids)).all()
    checkout_version_dict = {}
    for document in all_checkouts:
        checkout_version_dict[document.document_id] = document.document_version
    return render_template("my_documents.html", user_relevant_docs=all_docs, checkouts=checkout_version_dict)


@app.route("/document-timeline/<document_id>", methods=['GET', 'POST'])
def get_document_timeline(document_id):
    history = []
    history = ChangeLog.query.filter(ChangeLog.document_id == document_id).all()
    return render_template("timeline.html", history=history)


@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()


@app.route('/document-timeline/profile_images/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['IMAGE_UPLOAD_FOLDER'],
                               filename)

if __name__ == "__main__":
    app.run()
