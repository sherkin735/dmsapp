import os, datetime, subprocess
from flask import Flask, jsonify, render_template, redirect, url_for, flash, request, session, send_from_directory, send_file, make_response
from werkzeug.utils import secure_filename
from models import Document, Checkout, Tag, ChangeLog
from hashlib import md5
from datetime import timedelta
from Classifier import Classifier
from sqlalchemy import exc
from sqlalchemy.sql import func
import json
from random import randint
from operator import itemgetter

from database import db_session, engine
from models import User

app = Flask(__name__)
app.config.from_pyfile('config.py')

#method is run before every request, thus refreshing the session lifetime,
#the session expires after 30 minutes of inactivity i.e. no new requests
#have been received by the server in that time and so the session could not be refreshed
@app.before_request
def session_expiry():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=(app.config['SESSION_LIFETIME']))


@app.before_request
def check_session():
    if 'username' in session:
        return None
    elif request.url_rule:
        # adding exception here for static files (was causing css issues with get requests)
        if request.url_rule.rule in app.config['SESSION_CHECKING_ENDPOINT_EXCEPTIONS'] or app.config['STATIC_PATH'] in request.path:
            print("REQUEST PATH: {0}".format(request.path))
            return None
    return redirect(url_for('login'))


@app.route("/home")
def home():
    if session['access_level'] == 1:
        return redirect(url_for('admin'))
    return render_template("index.html")


@app.route("/admin")
def admin():
    user_count = 0
    users = User.query.filter(User.password_try_count == 3).all()
    if users:
        user_count = len(users)
    return render_template("admin.html", locked_out_users=user_count)


def populate_data():
    for i in range(1, 10):
        num_records = randint(2, 10)
        for num in range(1, num_records):
            date = datetime.datetime.today() - datetime.timedelta(days=i)
            #checkout = Checkout(document_id=1, checkout_time=date, checkout_username='sherkin', document_version='1.0')
            #doc = Document(document_name="Name{0}{1}".format(num, date), file_name="{0}-{1}".format(num, date), uploader='william', upload_date=date, version='1.0', last_edited_by='william', archived=False,hash="{0}-{1}".format(num, date), file_extension='pdf', access_level=3, major_category='pending')
            user = User("{0}-{1}".format(date, num),'password', 'name', 'photo', 3, 0, date)
            db_session.add(user)
            db_session.commit()


def collate_download_stats():
    twenty_days_ago = datetime.datetime.today() - datetime.timedelta(days=20)
    recent_checkouts = Checkout.query.filter(Checkout.checkout_time >= twenty_days_ago).all()
    checkout_stats = {}
    for checkout in recent_checkouts:
        date = checkout.checkout_time.strftime("%d-%m-%Y")
        if date in checkout_stats:
            checkout_stats[date] += 1
        else:
            checkout_stats[date] = 1
    return checkout_stats


def collate_upload_stats():
    twenty_days_ago = datetime.datetime.today() - datetime.timedelta(days=20)
    recent_uploads = Document.query.filter(Document.upload_date >= twenty_days_ago).all()
    upload_stats = {}
    for upload in recent_uploads:
        date = upload.upload_date.strftime("%d-%m-%Y")
        if date in upload_stats:
            upload_stats[date] += 1
        else:
            upload_stats[date] = 1
    return upload_stats


def collate_user_stats():
    twenty_days_ago = datetime.datetime.today() - datetime.timedelta(days=20)
    new_users = User.query.filter(User.creation_date >= twenty_days_ago).all()
    user_stats = {}
    user_list = []
    for user in new_users:
        date = user.creation_date.strftime("%d-%m-%Y")
        if date in user_stats:
            user_stats[date] += 1
        else:
            user_stats[date] = 1
    for date in user_stats.keys():
        user_list.append({'date': date,
                          'count': user_stats[date]})
    return sorted(user_list, key=itemgetter('date'))


def combine_stats(uploads, downloads):
    result_list = []
    for key in uploads.keys():
        result_list.append({'date': key,
                            'uploads': uploads[key],
                            'downloads': downloads[key]})
    return sorted(result_list, key=itemgetter('date'))


@app.route('/admin_stats')
def admin_stats():
    #populate_data()
    checkout_list = collate_download_stats()
    upload_list = collate_upload_stats()
    user_stats = collate_user_stats()
    result = combine_stats(upload_list, checkout_list)
    return jsonify({'admin_stats': result,
                   'user_stats': user_stats})


@app.route("/")
def slash():
    return redirect(url_for("home"))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('username') and request.form.get('password'):
            result = check_user_details(request.form.get('username'), request.form.get('password'))
            if result == 'valid':
                if session['access_level'] == 1:
                    return redirect(url_for('admin'))
                else:
                    return redirect(url_for('home'))
            elif result == 'invalid':
                flash("Invalid credentials. Please try again.", 'error')
            elif result == 'locked':
                flash("You have made too many incorrect password attempts and your account has been locked. Please contact an administrator to resolve this.", "error")
        else:
            flash("One or more fields were left blank. Please try again.", "error")
    return render_template('login.html')


@app.route("/logout")
def logout():
    if session.get("name"):
        session.clear()
        flash('Logout successful.', 'success')
    return redirect(url_for('login'))


def set_session(user):
    session['username']=user.username
    session['name']=user.name
    session['profile_photo'] = os.path.join(app.config['IMAGE_UPLOAD_FOLDER'], user.profile_photo)
    session['access_level'] = user.access_level

def check_user_details(username, password):
    result = 'invalid'
    try:
        obj = User.query.filter(User.username == username).first()
    except exc.SQLAlchemyError, ex:
        print ex
        return result
    if obj:
        if obj.password == password and obj.password_try_count < 3:
            obj.password_try_count = 0
            set_session(obj)
            result = 'valid'
        elif obj.password != password and obj.password_try_count < 2:
            obj.password_try_count += 1
            result = 'invalid'
        elif obj.password != password and obj.password_try_count == 2:
            obj.password_try_count += 1
            result = 'locked'
        elif obj.password_try_count == 3:
            result = 'locked'
        db_session.commit()
    return result


def account_exists(username):
    obj = User.query.filter(User.username == username).first()
    if obj:
        return True
    return False


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if not request.form.get('username') or not request.form.get('password') or not request.form.get('name'):
            flash('Not all fields were filled out. Please check you have supplied all requested information.', 'error')
        elif account_exists(request.form.get('username')):
                flash('An account has already been registered for this email address. Please try a different address.', 'error')
        else:
            file_name = file_upload(request.files.get('profile_photo'), app.config['IMAGE_UPLOAD_FOLDER'], app.config['ALLOWED_IMAGE_EXTENSIONS'])
            if not file_name:
                file_name = app.config['DEFAULT_PROFILE_PHOTO']
            todays_date_time = datetime.datetime.today()
            new_user = User(username=request.form.get('username'), password=request.form.get('password'), name=request.form.get('name').title(),
                            profile_photo=file_name, creation_date=todays_date_time)
            db_session.add(new_user)
            db_session.commit()
            flash('New user created successfully.', 'success')
    return render_template('register.html')


@app.route('/profile_images/<filename>')
def serve_image(filename):
    return send_from_directory(app.config['IMAGE_UPLOAD_FOLDER'], filename)


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if request.method == 'POST':
        try:
            no_change = True
            current_user = User.query.filter_by(username=session['username']).first()
            if session['username'] != request.form['username'] and account_exists(request.form['username']):
                flash("An account already exists for this username")
                return render_template('profile.html')
            elif request.form['username'] != "" and session['username'] != request.form['username']:
                current_user.username = request.form['username']
                no_change = False
            if current_user.name != request.form['name'] and request.form['name'] != "":
                current_user.name = request.form['name']
                no_change = False
            if request.form['password'] != "":
                current_user.password = request.form['password']
                no_change = False
            if request.files.get(('profile_photo')):
                file_name = file_upload(request.files.get('profile_photo'), app.config['IMAGE_UPLOAD_FOLDER'], app.config['ALLOWED_IMAGE_EXTENSIONS'])
                if session['profile_photo'] != app.config['DEFAULT_PROFILE_PHOTO']:
                    os.unlink(session['profile_photo'])
                current_user.profile_photo = file_name
                no_change = False
            db_session.commit()
            set_session(current_user)
            print(no_change)
            if no_change:
                flash("No user details were changed as no new values were submitted.", 'success')
            else:
                flash("User details were successfully updated.", 'success')
        except Exception, ex:
            flash("There was an error updating your details. Please try again later", 'error')
            print("Exception while updating details: {0}".format(ex))
    return render_template('profile.html')


def allowed_file(filename, extensions):
    return '.' in filename and filename.rsplit('.', 1)[1] in extensions


def file_upload(upload_file, destination_folder, extensions):
    if upload_file and allowed_file(upload_file.filename, extensions):
            filename = sanitise_filename(upload_file.filename)
            upload_file.save(os.path.join(destination_folder, filename))
            return filename
    return None


def delete_file():
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
        user_access_exceptions = (request.form.getlist('user_exceptions'))

        user_name_id_dict = {'name': [name for name in user_access_exceptions if not name.isdigit()], 'id':[int(id) for id in user_access_exceptions if id.isdigit()]}
        tag_text_id_dict = {'text': [text for text in tags if not text.isdigit()], 'id':[int(id) for id in tags if id.isdigit()]}

        saved_tags = []
        if tag_text_id_dict['id']:
            saved_tags = Tag.query.filter(Tag.id.in_(tag_text_id_dict['id'])).all()
        user_exceptions = []
        if user_name_id_dict['id']:
            user_exceptions = User.query.filter(User.id.in_(user_name_id_dict['id'])).all()

        if request.form.get('document_name') and request.form.get('tags') and 'file' in request.files:
            file = request.files['file']
            if not file:
                flash("No file included in upload", "error")
            doc_hash = get_document_hash(file)
            # getting the hash brings us to the end of the file - reset to the beginning
            file.stream.seek(0)
            doc_name = doc_previously_uploaded(doc_hash)
            if not doc_name:
                saved_file_name = file_upload(request.files['file'], app.config['DOCUMENT_UPLOAD_FOLDER'], app.config['ALLOWED_DOCUMENT_EXTENSIONS'])
                todays_date_time = datetime.datetime.today()
                #here is where the item will be added to the beanstalk queue
                #document_classifier = Classifier(app.config['DOCUMENT_UPLOAD_FOLDER'] + '/' + saved_file_name)
                predicted_category = 'pending'#document_classifier.classify_document()

                document = Document(document_name=request.form['document_name'], file_name=saved_file_name,
                uploader=session['username'], upload_date=todays_date_time,
                version="1.0", last_edited_by=session['username'], archived=False, hash=doc_hash,
                file_extension=saved_file_name.split('.')[-1], access_level=request.form.getlist("access_level")[0], major_category=predicted_category)
                for tag in tag_text_id_dict['text']:
                    document.tags.append(Tag(tag))
                for exception in user_exceptions:
                    document.user_access_exceptions.append(exception)
                if saved_file_name:
                    db_session.add(document)
                    db_session.commit()
                    upload_event = ChangeLog(document.id, todays_date_time, "Initial upload of document", session['username'], document.document_name, document.file_name, "1.0")
                    db_session.add(upload_event)
                    db_session.commit()
                    flash("Document uploaded successfully", 'success')
                else:
                    os.remove(app.config['DOCUMENT_UPLOAD_FOLDER'] + '/' + saved_file_name)
                    flash("Document upload failed. Please contact an administrator", 'error')
                if len(saved_tags) > 0:
                    for tag in saved_tags:
                        engine.execute("INSERT INTO DocumentTag (tag_id, document_id) VALUES ({0}, {1})".format(tag.id, document.id))
            else:
                flash("This document has been uploaded previously. Please search for the following document: {0}".format(doc_name), 'error')
        else:
            flash("Not all required fields were filled out. Please ensure all fields have been filled and try again")
    return render_template('document_upload.html')


@app.route("/document_search", methods=['GET', 'POST'])
def document_search():
    tagged_documents = []
    named_documents = []
    if request.method=='GET':
        return render_template('document_search.html', relevant_docs='empty')
    elif request.method == 'POST':
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
        checkout_date_time = datetime.datetime.today()
        previous_checkout = Checkout.query.filter(Checkout.checkout_username == session['username']).filter(Checkout.document_id == document_id).first()
        if not previous_checkout:
            chkout = Checkout(document_id, checkout_date_time, session['username'], version)
            db_session.add(chkout)
        else:
            previous_checkout.checkout_date_time = checkout_date_time
            previous_checkout.version = version
        db_session.commit()
        return True
    except Exception, ex:
        print(ex)
    return False


def update_tags(document, submitted_tags):
    existing_tags = []
    try:
        document.tags = []
        db_session.commit()
        submitted_tags_dict = {'id': [int(tagID) for tagID in submitted_tags if tagID.isdigit()],
                               'text': [tag_text for tag_text in submitted_tags if not tag_text.isdigit()]}
        if len(submitted_tags_dict['text']) > 0:
            existing_tags = Tag.query.filter(Tag.text.in_(submitted_tags_dict['text'])).all()
        for tag in existing_tags:
            submitted_tags_dict['text'].remove(tag.text)
            submitted_tags_dict['id'].append(tag.id)
        for text in submitted_tags_dict['text']:
            document.tags.append(Tag(text))
        for tagID in submitted_tags_dict['id']:
            engine.execute("INSERT INTO DocumentTag (tag_id, document_id) VALUES ({0}, {1})".format(tagID, document.id))
        return True
    except Exception, ex:
        print('SQL EXCEPTION: {0}'.format(ex))
        return False


def checkin_document():
    try:
        request.files['document'].filename = sanitise_filename(request.files['document'].filename)
        document = Document.query.filter(Document.id == request.form.get("doc_id")).first()
        print(document)
        # the names for the select items are auto generated by concatting tags_for_ and the doc_id
        tag_update_successful = update_tags(document, request.form.getlist('tags_for_'+str(document.id)))
        #update the hash value of the document
        document.hash = get_document_hash(request.files['document'])
        #increment document version number
        archive_filename = document.archive_document(True)
        upload_successful = file_upload(request.files['document'], app.config['DOCUMENT_UPLOAD_FOLDER'], app.config['ALLOWED_DOCUMENT_EXTENSIONS'])
        document.file_name = request.files['document'].filename
        if upload_successful and tag_update_successful:
            db_session.commit()
        else:
            #upload fails - move back to original locations
            document.archive_document(archive=False)
        checkin_date_time = datetime.datetime.today()
        previous_event = ChangeLog.query.filter(ChangeLog.document_version == document.version).first()#db_session.query(func.max(ChangeLog.checkin_date))
        print(previous_event)
        previous_event.file_name = archive_filename
        document.increment_version_number()
        change_object = ChangeLog(document.id, checkin_date_time, request.form.get('comments'), session['username'], document.document_name, document.file_name, document.version)
        document.changes.append(change_object)
        db_session.commit()
        return True
    except Exception, ex:
        print("Checkin exception")
        print(ex)
        return False


def delete_download_record(document):
    checkout_record=Checkout.query.filter(Checkout.checkout_username==session['username']).filter(Checkout.document_id==document.id).first()
    db_session.delete(checkout_record)
    db_session.commit()


@app.route("/get_tags")
def get_tags():
    doc_id = request.args.get("document_id")
    tags = Tag.query.filter(Tag.documents.any(document_id=doc_id)).all()
    return jsonify(result=[tag.text for tag in tags])


@app.route("/downloads/<document_id>")
def download_document(document_id):
    doc = Document.query.filter(Document.id == document_id).first()
    filename = doc.file_name
    version = doc.version
    if checkout_document(document_id, version):
        return send_from_directory(app.config['DOCUMENT_UPLOAD_FOLDER'], filename, as_attachment=True)
    else:
        return "There was an error in checking out the requested document. Please try again."


@app.route('/admin_user_table', methods=['GET', 'POST'])
def send_user_data():
    if request.method == 'POST':
        result = None
        changes = (request.form.to_dict())
        print(changes)
        data = parse_change_data(changes)
        if changes['action'] == 'edit':
            if data[1].get('username') and account_exists(data[1]['username']):
                result = jsonify({'fieldErrors': [{"name": "username",
                                                 "status": 'This username is taken.'}]})
            else:
                update_user = User.query.filter(User.id == data[0])
                update_user.update(data[1])
                result = jsonify({'data': [update_user.first().to_dict()]})
        elif changes['action'] == 'create':
            if not account_exists(data[1]['username']):
                new_user = User(username=data[1]['username'], password=data[1]['password'], name=data[1]['name'],
                                profile_photo=app.config['DEFAULT_PROFILE_PHOTO'],
                                access_level=data[1]['access_level'])
                db_session.add(new_user)
                result = jsonify({'data': [new_user.to_dict()]})
            else:
                result = jsonify({'fieldErrors': [{"name": "username",
                                                 "status": 'This username is taken.'}]})
        elif changes['action'] == 'remove':
            user = User.query.filter(User.id == data[0]).first()
            db_session.delete(user)
            result = jsonify({"data": []})
        db_session.commit()
        return result
    else:
        users = User.query.all()
        user_list = [user.to_dict() for user in users]
        return jsonify({
            "data": user_list,
            "options": [],
            "files": []
        })


def parse_change_data(changes):
    change_keys = changes.keys()
    change_keys.remove('action')
    userID = None
    if change_keys:
        ck_dict = {}
        for key in change_keys:
            new_string = key.replace('[', '<').replace(']', '<')
            split_string = new_string.split('<')
            filter_list = filter(None, split_string)
            print(filter_list)
            ck_dict[filter_list[2]] = changes[key]
            if not userID:
                userID = filter_list[1]
        return (userID, ck_dict)
    return None


@app.route('/admin_tag_table')
def send_tag_data():
    if request.method == 'POST':
        pass
    tags = Tag.query.all()
    tag_list = [tag.to_dict() for tag in tags]
    return jsonify({
            "data": tag_list,
            "options": [],
            "files": []
    })


@app.route('/ajax_doc_tags')
def ajax_doc_tags():
    term = request.args.get('search')
    tags = Tag.query.filter(Tag.text.like("{0}%".format(term))).all()
    return jsonify({'items': [tag.to_dict() for tag in tags]})


@app.route('/ajax_user_names')
def ajax_user_names():
    term = request.args.get('search')
    users = User.query.filter(User.username.like("{0}%".format(term))).all()
    return jsonify({'items': [user.to_ajax_dict() for user in users]})


@app.route('/reboot_server')
def reboot_server():
    print("Server going down for reboot")
    print(subprocess.call('reboot', shell=True))



@app.route("/my-documents", methods=['GET', 'POST'])
def my_documents():
    #todo: version numbers increment even upon failed updates. bundle all activities together
    if request.method == 'POST':
        success = checkin_document()
        if success:
            flash("Document updated successfully", 'success')
        else:
            flash("There was an error updating the document. Please try again later", 'error')
    all_checkouts = Checkout.query.filter(Checkout.checkout_username == session['username']).all()
    doc_ids = [doc.id for doc in all_checkouts]
    #fix here so _in clauses cannot run on empty sequences
    downloads = Document.query.filter(Document.id.in_(doc_ids)).all()
    uploads = Document.query.filter(Document.uploader == session['username']).all()
    downloads = [doc for doc in downloads if doc not in uploads]
    checkout_version_dict = {}
    for checkout in all_checkouts:
        checkout_version_dict[checkout.document_id] = checkout.document_version
    if len(downloads) == 0:
        downloads = None
    if len(uploads) == 0:
        uploads = None
    return render_template("my_documents.html", downloaded_docs=downloads, checkouts=checkout_version_dict, uploads=uploads)


@app.route("/document-timeline/<document_id>", methods=['GET', 'POST'])
def get_document_timeline(document_id):
    history = ChangeLog.query.filter(ChangeLog.document_id == document_id).all()
    return render_template("timeline.html", history=history)


@app.route("/archive/<file_name>")
def fetch_from_archive(file_name):
    # :Fixme need a nicer way of doing this (for now just checking the file name contains the '_v- pattern associated with versioned docs
    if '_v-' in file_name:
        if ChangeLog.query.filter(ChangeLog.file_name == file_name).first():
            return send_from_directory(app.config['DOCUMENT_ARCHIVE_FOLDER'], file_name, as_attachment=True)
    document = Document.query.filter(Document.file_name == file_name).first()
    print(document)
    if document:
        flash('Please use the search page to download the most recent version of this document', 'error')
        return redirect(url_for('get_document_timeline', document_id=document.id))


@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()


#some issues with the timeline page where it wouldnt serve the profile image
#added this as a temporary workaround
@app.route('/document-timeline/profile_images/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['IMAGE_UPLOAD_FOLDER'],
                               filename)

if __name__ == "__main__":
    app.run(threaded=True, debug=True)
