import os
from flask import Flask, render_template, redirect, url_for, flash, request, session, send_from_directory
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'profile_images'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])


from database import db_session
from models import User

app = Flask(__name__)
app.secret_key = '\xa4\xcaG \x8f\x1c\x94i\xd8P$9\x11\x8b,\xbdV\x9f\xc5\xf3\x1cL\xcev'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route("/home")
def home():
    if check_session():
        return render_template("index.html", name=session['name'], profile_photo=session['profile_photo'])
    else:
        return redirect(url_for('login'))

@app.route("/")
def slash():
    if check_session():
        return redirect(url_for("home"))
    else:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if not request.form['username'] or not request.form['password']:
            error = 'Field(s) left blank. Please try again.'
        elif not check_user_details(request.form['username'], request.form['password']):
            error = 'Invalid Credentials. Please try again.'
        elif check_user_details(request.form['username'], request.form['password']):
                return redirect(url_for('home'))
    return render_template('login.html', error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    #default
    photo_path = None
    if request.method == 'POST':
        if 'file' in request.files:
            photo_path = image_upload(request.files['file'])
        if not request.form['username'] or not request.form['password'] or not request.form['name']:
            error = 'Not all fields were filled out. Please check you have supplied all requested information.'
        elif check_user_details(request.form['username'], request.form['password']):
                error = 'An account has already been registered for this email address.'
                session.pop("username")
                session.pop("name")
                session.pop("profile_photo")
        new_user = User(request.form['username'], request.form['password'], request.form['name'], photo_path)
        db_session.add(new_user)
        db_session.commit()
        flash('New user created successfully.')
    return render_template('register.html', error=error)

def check_user_details(username, password):
    User.query.all()
    obj = User.query.filter(User.username == username).first()
    if obj:
        if obj.password == password:
            session['username']=obj.username
            session['name']=obj.name
            session['profile_photo'] = obj.profile_photo
            return True
    return False

@app.route("/logout")
def logout():
    if session.get("name"):
        session.pop("name")
        session.pop("username")
        session.pop("profile_photo")
        #todo: possibly add a message flash notifying user of successful logout
    return redirect(url_for('login'))

@app.route('/profile', methods = ['GET', 'POST'])
def profile():
    if check_session():
        if request.method == 'POST':
            current_user = User.query.filter_by(username=session['username']).first()
            #do this a better way later, currently a user could change their username to one that is already taken which isnt ideal
            print(request.form['username'])
            print(request.form['name'])
            print(request.form['password'])
            print(request.files['profile_photo'])
            current_user.username = request.form['username']
            current_user.name = request.form['name']
            current_user.password = request.form['password']
            #could add logic to remove old photos from the profile_images dir
            new_photo = session['profile_photo']
            if request.form['password'] != "":
                current_user.password = request.form['password']
            db_session.commit()
            session['name'] = request.form['name']
            session['username'] = request.form['username']
            #session['profile_photo'] = request.profile_photo
            flash("User details were successfully updated.")
        return render_template('profile.html', name=session['name'], username=session['username'],
                               profile_photo=session['profile_photo'].split('/')[-1])
    else:
        return redirect(url_for('login'))

def check_session():
    if 'name' in session and 'username' in session:
        return True
    else:
        return False

@app.route("/tables")
def tables():
	return render_template("tables.html")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def image_upload(file):
    default_image = 'profile_images/default.png'
    if file.filename == "":
        flash('No file selected')
        return default_image
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        path_to_file = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(path_to_file)
        return path_to_file

@app.route('/document_upload', methods=['GET', 'POST'])
def document_upload():
    if request.method == 'POST':
        pass
    else:
        return render_template('document_upload.html', username=session['username'], name=session['name'],
                               profile_photo=session['profile_photo'])

@app.route('/profile_images/<filename>')
def serve_image(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)

if __name__ == "__main__":
    app.run(debug=False)
