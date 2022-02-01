import multiprocessing

from flask import Flask, render_template, request, redirect, url_for, session, flash, json, jsonify, current_app, g
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mysqldb import MySQL 
from flask_cors import CORS, cross_origin 
from google.oauth2 import id_token 
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol

import google.auth.transport.requests
import MySQLdb.cursors, re, os
import pathlib
import requests
import time, datetime

app = Flask(__name__)
CORS(app)

app.secret_key = '9d1500abf69151a4d1e159a130a39530'
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

#app.config['MYSQL_HOST'] = 'localhost'
#app.config['MYSQL_USER'] = 'root'
#app.config['MYSQL_PASSWORD'] = 'admin12345'
#app.config['MYSQL_DB'] = 'ThesisDB'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_PORT'] = 5522
app.config['MYSQL_USER'] = 'pundfetu_4juser'
app.config['MYSQL_PASSWORD'] = 'scSRq&edRE=*6Q9C'
app.config['MYSQL_DB'] = 'pundfetu_4jThesisDB'

os.environ['REQUESTS_CA_BUNDLE'] = "certifi/cacert.pem"

mysql = MySQL(app)

GOOGLE_CLIENT_ID = "301334052492-dq6i7f9rc416t2c4ih8qe4a29fp8afq8.apps.googleusercontent.com"
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")

flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
    redirect_uri="http://127.0.0.1:5000/callback"
)

# FUNCTIONS
# FUNCTIONS
# FUNCTIONS

def get_user(userID):
    with app.app_context():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE userID = %s', (userID,))
        user = cursor.fetchone()
        return user

def get_class(classID):
    with app.app_context():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT class.*, users.fullname FROM class JOIN users ON class.instructorID = users.userID WHERE classID = %s', (classID,))
        classData = cursor.fetchone()
        return classData

def get_webBlock(classID):
    with app.app_context():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM blocker WHERE blockType =  %s and classID = %s', ('web',classID,))
        webBlockData = cursor.fetchall()
        return webBlockData

def get_appBlock(classID):
    with app.app_context():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM blocker WHERE blockType =  %s and classID = %s', ('app',classID,))
        appBlockData = cursor.fetchall()
        return appBlockData

def get_students(classID):
    with app.app_context():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT users.userID, fullname, isActive, extension FROM users INNER JOIN classroom ON users.userID = classroom.studentID INNER JOIN class ON classroom.classID = class.classID WHERE class.classID = %s;', (classID,))
        studentLists = cursor.fetchall()
        data = []
        import datetime
        dt = datetime.datetime.now()
        curDate = dt.strftime('%Y-%m-%d')
        for x in studentLists:
            cursor.execute('SELECT activityName FROM activity_log WHERE studentID=%s AND classID=%s AND curDate=%s ORDER BY logID DESC LIMIT 1', (x['userID'], classID, curDate,))
            current = cursor.fetchone()
            if current == None:
                current = 'None'
            else:
                current = current.get('activityName')
            a = []

            b = x.get('fullname').split(' ')
            c = []
            for b in b:
                c.append(b[:1].upper())

            img = ''.join(str(item) for item in c)
            a.extend((x.get('userID'), x.get('fullname'), x.get('isActive'), current, img, x.get('extension')))
            data.append(a)
        
        return data

def generate_id():
    import string, random
    char = string.ascii_lowercase + string.digits
    id = ''.join(random.choice(char) for i in range(9))
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT classID FROM class')
    id_lists = str(cursor.fetchall())
    
    while id in id_lists:
        id = ''.join(random.choice(char) for i in range(9))
    else: 
        return id

def trackerStatus():
    if 'tracker' in session:
        status = '1'
    else:
        status = '0'
    return status

# AUTH
# AUTH
# AUTH

@app.route('/')
@app.route("/sign-in", methods=['GET', 'POST'])
def sign_in():
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        # fetch username in database
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cursor.fetchone()
        # verify if username exists in database
        if username == 'admin' and password == 'admin':
            session['loggedin'] = True
            flash('Welcome!', 'popup-success')
            return redirect(url_for('admin_dashboard'))
        if user: 
            password_hash = user['password']
            if check_password_hash(password_hash, password):
                session['loggedin'] = True
                session['userID'] = user['userID']
                session['username'] = user['username']
                flash('Welcome!', 'popup-success')
                return redirect(url_for('class_view'))
            else:
                flash('Username and Password dont not match. Try Again', 'popup-error')
                return redirect(request.url)
        flash('User doesnt exists', 'popup-error')
        return redirect(request.url)
    return render_template('public/sign-in.html')

@app.route("/google_signin")
def google_signin():
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)

@app.route("/callback")
def callback():
    flow.fetch_token(authorization_response=request.url)

    if not session["state"] == request.args["state"]:
        abort(500)

    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)
    
    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=GOOGLE_CLIENT_ID
    )

    session["google_id"] = id_info.get("sub")
    session["name"] = id_info.get("name")
    name = id_info.get("name")
    email = id_info.get("email")
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * from users where email=%s', (email,))
    user = cursor.fetchone()

    if user:
        session['loggedin'] = True
        session['userID'] = user['userID']
        session['username'] = user['username']
        flash('Welcome!', 'popup-success')
        return redirect(url_for('class_view'))

    return render_template('public/type.html', name=name, email=email)

@app.route("/onboard-google", methods=['GET', 'POST'])
def onboard():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if request.method == 'POST' and 'fullname' in request.form and 'email' in request.form and 'type' in request.form:
        usertype = str(request.form['type'])
        fullname = request.form['fullname']
        email = request.form['email']
        import datetime
        date = datetime.datetime.now()
        import string, random
        char = string.ascii_lowercase + string.digits
        id = ''.join(random.choice(char) for i in range(12))
        username = fullname.split(' ')[0] + id
        password = fullname.split(' ')[0] + id
        is_active = '0'
        userImg = 'None'
        extension = '0'
        cursor.execute('INSERT INTO users (fullname, email, username, password, type, isActive, userImg, datecreated, extension) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)', (fullname, email, username, password, usertype, is_active, userImg, date, extension))
        mysql.connection.commit()

        cursor.execute('SELECT * FROM users WHERE email=%s', (email,))
        user = cursor.fetchone()

        session['loggedin'] = True
        session['userID'] = user['userID']
        userID = user['userID']
        userData = get_user(session['userID'])
        return redirect(url_for('class_view'))

    
    flash('Try Again!', 'popup-error')
    return redirect(url_for("sign_in"))

@app.route('/')
@app.route("/sign-up", methods=['GET', 'POST'])
def sign_up():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if request.method == 'POST' and 'fullname' in request.form and 'username' in request.form and 'email' in request.form and 'password' in request.form and 'type' in request.form:
        usertype = str(request.form['type'])
        fullname = request.form['fullname']
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        import datetime
        date = datetime.datetime.now()
        hash_password = generate_password_hash(password)
        # fetch username in database
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cursor.fetchone()
        # validate
        if user:
            flash('Account Already Exists', 'popup-error')
        elif not fullname or not username or not email or not password:
            flash('Please Fill out the Form.', 'popup-error')
        elif not re.match(r'[A-Za-z0-9]+', username):
            flash('Username must contain only characters and numbers', 'popup-error')
        else:
            is_active = '0'
            userImg = 'None'
            extension = '0'
            cursor.execute('INSERT INTO users VALUES (NULL, %s, %s, %s, %s, %s, %s, %s, %s, %s)', (fullname, email, username, hash_password, usertype, is_active, userImg, date, extension))
            mysql.connection.commit()
            flash('Account Successfully Created!', 'popup-success')
            return redirect(url_for("sign_in"))
    elif request.method == 'POST':
        flash('Please Fill out the Form.', 'popup-error')

    return render_template('public/sign-up.html')

@app.route('/sign-out')
def sign_out():
    # Remove session data, this will log the user out
   session.pop('loggedin', None)
   session.pop('userID', None)
   session.pop('username', None)
   session.pop('tracker', None)

   # Redirect to login page
   flash('Sign out Successful', 'popup-success')
   return redirect(url_for('sign_in'))

# ADMIN
# ADMIN
# ADMIN

@app.route("/admin/dashboard")
def admin_dashboard():
    if 'loggedin' not in session:
        return redirect(url_for('sign_in'))
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT COUNT(userID) as student FROM users WHERE type=%s', ('student',))
    student = cursor.fetchone()
    cursor.execute('SELECT COUNT(userID) as instructor FROM users WHERE type=%s', ('instructor',))
    instructor = cursor.fetchone()
    cursor.execute('SELECT COUNT(classID) as class FROM class')
    noofclass = cursor.fetchone()
    cursor.execute('SELECT COUNT(userID) as active FROM users WHERE isActive=%s', (1,))
    activeStudent = cursor.fetchone()

    cursor.execute('SELECT userID, fullname, datecreated FROM users ORDER BY userID DESC LIMIT 10')
    recentUsers = cursor.fetchall()

    cursor.execute('SELECT classID, className, datecreated FROM class ORDER BY datecreated DESC LIMIT 10')
    recentClass = cursor.fetchall()
    
    return render_template('admin/dashboard.html', student = student, instructor = instructor, noofclass=noofclass, activeStudent=activeStudent, recentUsers=recentUsers, recentClass=recentClass)

@app.route("/admin/users")
def admin_users():
    if 'loggedin' not in session:
        return redirect(url_for('sign_in'))
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM users')
    usersData = cursor.fetchall()
    return render_template('admin/users.html', usersData = usersData)

@app.route("/admin/class")
def admin_class():
    if 'loggedin' not in session:
        return redirect(url_for('sign_in'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT classID, className, classDesc, classTimeStart, classTimeEnd, classDay, users.fullname FROM class JOIN users ON class.instructorID = users.userID')
    classData = cursor.fetchall()
    cursor.execute('SELECT userID, fullname FROM users WHERE type = %s', ('instructor',))
    instructor = cursor.fetchall()
    return render_template('admin/class.html', classData = classData, instructor=instructor)

@app.route("/admin/assign-student/id=<userID>", methods=['GET', 'POST'])
def admin_assign(userID):
    if 'loggedin' not in session:
        return redirect(url_for('sign_in'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    userData = get_user(userID)
    cursor.execute('SELECT classID, className, classDesc, classTimeStart, classTimeEnd, classDay, users.fullname FROM class JOIN users ON class.instructorID = users.userID')
    classData = cursor.fetchall()
    cursor.execute('select classID from classroom where studentID = %s;', (userID))
    x = cursor.fetchall()
    studentClass = []

    for x in x:
        for a, b in x.items():
            studentClass.append(b)
    print(studentClass)
    return render_template('admin/assign.html', classData=classData, studentClass=studentClass, userData=userData)

@app.route("/admin/class/add", methods=['GET', 'POST'])
def create_class_admin():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    classID = generate_id()
    className = request.form['className']
    classDesc = request.form['classDesc']
    classColor = request.form['classColor']
    classTimeStart = request.form['classTimeStart']
    classTimeEnd = request.form['classTimeEnd']
    classDay =  request.form['classDay']
    instructorID =  request.form['instructor']
    blocker = 'disable'
    keystrokes = 'disable'
    idle = 'disable'
    idleTime = 0
    viewType = 'grid'
    publish = '0'
    import datetime
    date = datetime.datetime.now()

    if classID and className and classDesc and classColor and instructorID and classTimeStart and classTimeEnd and classDay:
        cursor.callproc('create_class', (classID, className, classDesc, classColor, classTimeStart, classTimeEnd, classDay, blocker, keystrokes, idle, idleTime, viewType, publish, date, instructorID))
        mysql.connection.commit()
        
        # Notification
        notifName = 'Class Created'
        notifText = 'Class ' + className + ' successfully created. You may access it in your dashboard.'
        ts= time.time()
        tmstmp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('INSERT INTO notification (notifName, notifText, tmstmp, userID) VALUES (%s, %s, %s, %s)', (notifName, notifText, tmstmp, instructorID,))
        mysql.connection.commit()
        msg = 'Class successfully created'
        return jsonify({'msg' : msg})
    
    return jsonify({'error' : 'Try Again!'})

@app.route("/admin/add-user", methods=['GET', 'POST'])
def admin_add_user():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    usertype = request.form['usertype']
    fullname = request.form['fullname']
    email = request.form['email']
    username = request.form['username']
    password = request.form['password']
    
    if usertype and fullname and email and username and password:
        hash_password = generate_password_hash(password)
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cursor.fetchone()
        if user:
            return jsonify({'error' : 'Account Already Exists'})
        elif not re.match(r'[A-Za-z0-9]+', username):
            return jsonify({'error' : 'Username must contain only characters and numbers'})
        else:
            import datetime
            date = datetime.datetime.now()
            is_active = '0'
            userImg = 'None'
            extension = '0'
            cursor.execute('INSERT INTO users VALUES (NULL, %s, %s, %s, %s, %s, %s, %s)', (fullname, email, username, hash_password, usertype, is_active, userImg, date, extension))
            mysql.connection.commit()
            flash('User Successfully added', 'popup-success')
            return redirect(request.url)

    return jsonify({'error' : 'Please fill up the form'})

@app.route("/admin/assign-student/id=<userID>/add-class/id=<classID>", methods=['GET', 'POST'])
def admin_user_add_class(userID, classID):
    user = get_user(userID)
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT classID FROM class')
    id_lists = str(cursor.fetchall())
    cursor.execute('SELECT studentID FROM classroom WHERE classID = %s', (classID,))
    x = cursor.fetchall()
    lists = []
    for x in x:
        for a, b in x.items():
            lists.append(b)
    userID = user.get('userID')

    if classID:
        if userID in lists:
            return jsonify({'error' : 'Youve Already joined the class.'})
        if classID in id_lists:
            # Notification
            notifName = 'Class Joined'
            notifText = 'Youve had successfully joined the class. you can access it in your dashboard.'
            ts= time.time()
            tmstmp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute('INSERT INTO notification (notifName, notifText, tmstmp, userID) VALUES (%s, %s, %s, %s)', (notifName, notifText, tmstmp, userID,))
            mysql.connection.commit()
            
            cursor.execute('INSERT INTO classroom (studentID, classID) VALUES (%s, %s)', (userID, classID))
            mysql.connection.commit()
            flash('Class Successfully added', 'popup-success')
    
    return redirect(url_for('admin_assign', userID = userID))

@app.route("/admin/assign-student/id=<userID>/remove-class/id=<classID>", methods=['GET', 'POST'])
def admin_user_remove_class(userID, classID):
    user = get_user(userID)
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('DELETE FROM classroom WHERE studentID = %s AND classID = %s', ())
    mysql.connection.commit()
    flash('Class Removed', 'popup-success')
    return redirect(url_for('admin_assign', userID = userID))


@app.route("/admin/delete-class/<classID>", methods=['GET', 'POST'])
def admin_delete_class(classID):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('DELETE FROM class WHERE classID = %s', (classID,))
    mysql.connection.commit()
    flash('Class Removed Successfully', 'popup-success')
    return redirect(url_for('admin_class'))


@app.route("/admin/delete-user/<userID>", methods=['GET', 'POST'])
def admin_delete_user(userID):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('DELETE FROM users WHERE userID = %s', (userID,))
    mysql.connection.commit()

    user = get_user(userID)
    if user['type'] == 'instructor':     
        cursor.execute('DELETE FROM class WHERE instructorID = %s', (userID,))
        mysql.connection.commit()
    elif user['type'] == 'student':
        cursor.execute('DELETE FROM classroom WHERE studentID = %s', (userID,))
        mysql.connection.commit()

    flash('User Removed Successfully', 'popup-success')
    return redirect(url_for('admin_users'))


# NOTIFICATION
# NOTIFICATION
# NOTIFICATION

notificationProcess = None

def notif_process(userID):
    with app.app_context():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT className, classTimeStart, classDay, class.classID FROM class INNER JOIN classroom ON class.classID = classroom.classID INNER JOIN users ON classroom.studentID = users.userID WHERE users.userID = %s', (userID,))
        classdata = cursor.fetchall()
        b = []
        for a in classdata:
            if 'Mon' in a['classDay'].split(','):
                b.append(0)
            if 'Tue' in a['classDay'].split(','):
                b.append(1)
            if 'Wed' in a['classDay'].split(','):
                b.append(2)
            if 'Thu' in a['classDay'].split(','):
                b.append(3)
            if 'Fri' in a['classDay'].split(','):
                b.append(4)
            if 'Sat' in a['classDay'].split(','):
                b.append(5)
            if 'Sun' in a['classDay'].split(','):
                b.append(6)

        dt = datetime.datetime.now()

        time =  []
        for x in classdata:
            z = x['classTimeStart'] - datetime.timedelta(minutes=10)
            time.append(z)

        if dt.weekday() in b:
            for time in time:
                if time == dt:
                    notifName = classdata['className']
                    notiftext = classdata['className'] + ' will start in 10 minutes'
                    ts= time.time()
                    tmstmp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
                    cursor.execute('INSERT INTO notification (notifName, notifText, tmstmp, userID) VALUES (%s, %s, %s, %s)', (notifName, notifText, tmstmp, userID,))
                    mysql.connection.commit()

@app.route("/notification")
def notification():
    if 'loggedin' not in session:
        return redirect(url_for('sign_in'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    userData = get_user(session['userID'])
    userID = userData['userID']
    notif_process(userID)
    cursor.execute('SELECT * FROM notification WHERE userID = %s', (userID,))
    notifData = cursor.fetchall()
    return render_template('public/notification.html', notifData=notifData, userData=userData)


# CALENDAR 
# CALENDAR 
# CALENDAR

@app.route("/calendar")
def calendar():
    if 'loggedin' not in session:
        return redirect(url_for('sign_in'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    userData = get_user(session['userID'])
    userID = userData['userID']

    if userData['type'] == 'instructor':
        cursor.execute('SELECT className, classTimeStart, classTimeEnd, classDay, classColor FROM class WHERE instructorID = %s', (userID,))
        classData = cursor.fetchall()
    elif userData['type'] == 'student':
        cursor.execute('SELECT className, classTimeStart, classTimeEnd, classDay, classColor FROM class INNER JOIN classroom ON class.classID = classroom.classID INNER JOIN users ON classroom.studentID = users.userID WHERE users.userID = %s', (userID,)) 
        classData = cursor.fetchall()
    
    for x in classData:
        a = []
        if 'Sun' in x['classDay'].split(','):
            a.append(0)
        if 'Mon' in x['classDay'].split(','):
            a.append(1)
        if 'Tue' in x['classDay'].split(','):
            a.append(2)
        if 'Wed' in x['classDay'].split(','):
            a.append(3)
        if 'Thu' in x['classDay'].split(','):
            a.append(4)
        if 'Fri' in x['classDay'].split(','):
            a.append(5)
        if 'Sat' in x['classDay'].split(','):
            a.append(6)
        x['classDay'] = a
    return render_template('public/calendar.html', userData=userData, classData=classData)


# CREATE AND JOIN CLASS
# CREATE AND JOIN CLASS
# CREATE AND JOIN CLASS

@app.route("/class")
def class_view():
    if 'loggedin' not in session:
        return redirect(url_for('sign_in'))
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    userData = get_user(session['userID'])
    userID = userData['userID']

    cursor.execute('SELECT * FROM notification WHERE userID = %s AND notifName = %s', (userID, 'Install Blocker Extension'))
    notif = cursor.fetchone()

    if notif:
        pass
    else: 
        notifName = 'Install Blocker Extension'
        notifText = 'Click the click to install the extension in your browser, **link***'
        ts= time.time()
        tmstmp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('INSERT INTO notification (notifName, notifText, tmstmp, userID) VALUES (%s, %s, %s, %s)', (notifName, notifText, tmstmp, userID,))
        mysql.connection.commit()

    global notificationProcess
    notificationProcess = multiprocessing.Process(target=notif_process, args=(userID,), daemon=True, name='NotificationProcess')
    notificationProcess.start()

    if userData['type'] == 'instructor':
        cursor.execute('SELECT * FROM class WHERE instructorID = %s ORDER BY classTimeStart', (userID,))
        classData = cursor.fetchall()
        return render_template('instructor/class.html', userData=userData, classData=classData )
    elif userData['type'] == 'student':
        extension = '0'
        cursor.execute('UPDATE users SET extension = %s WHERE userID = %s', (extension, userID,))
        mysql.connection.commit()

        if 'tracker' in session:
            classID = session['classID']
            return redirect(url_for('class_start_tracker', classID = classID))
        else:
            session.pop('classID', None)
            cursor.execute('SELECT className, classDesc, classTimeStart, classTimeEnd, classDay, class.classID, classColor FROM class INNER JOIN classroom ON class.classID = classroom.classID INNER JOIN users ON classroom.studentID = users.userID WHERE users.userID = %s order by classTimeStart', (userID,)) 
            classData = cursor.fetchall()
            return render_template('student/class.html', userData=userData, classData=classData )

@app.route("/create-class",  methods=['GET', 'POST'])
def create_class():
    if 'loggedin' not in session:
        return redirect(url_for('sign_in'))

    classID = generate_id()
    className = request.form['className']
    classDesc = request.form['classDesc']
    classColor = request.form['classColor']
    classTimeStart = request.form['classTimeStart']
    classTimeEnd = request.form['classTimeEnd']
    classDay =  request.form['classDay']
    blocker = 'disable'
    keystrokes = 'disable'
    idle = 'disable'
    idleTime = 0
    viewType = 'grid'
    publish = '0'
    import datetime
    date = datetime.datetime.now()
    user = get_user(session['userID'])
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    instructorID = user['userID']

    if classID and className and classDesc and classColor and classTimeStart and classTimeEnd and classDay:
        cursor.callproc('create_class', (classID, className, classDesc, classColor, classTimeStart, classTimeEnd, classDay, blocker, keystrokes, idle, idleTime, viewType, publish, date, instructorID))
        mysql.connection.commit()
        # Notification
        notifName = 'Class Created'
        notifText = 'Class ' + className + ' successfully created. You may access it in your dashboard.'
        ts= time.time()
        tmstmp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('INSERT INTO notification (notifName, notifText, tmstmp, userID) VALUES (%s, %s, %s, %s)', (notifName, notifText, tmstmp, instructorID,))
        mysql.connection.commit()
        msg = 'Class successfully created'
        return jsonify({'msg' : msg})
    
    return jsonify({'error' : 'Try Again!'})

@app.route("/join-class",  methods=['GET', 'POST'])
def join_class():
    if 'loggedin' not in session:
        return redirect(url_for('sign_in'))

    classID = request.form['classID']
    user = get_user(session['userID'])
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT classID FROM class')
    id_lists = str(cursor.fetchall())
    cursor.execute('SELECT studentID FROM classroom WHERE classID = %s', (classID,))
    x = cursor.fetchall()
    lists = []
    for x in x:
        for a, b in x.items():
            lists.append(b)
    userID = user['userID']
    if classID:
        if userID in lists:
            return jsonify({'error' : 'Youve Already joined the class.'})
        if classID in id_lists:
            # Notification
            notifName = 'Class Joined'
            notifText = 'Youve had successfully joined the class. you can access it in your dashboard.'
            ts= time.time()
            tmstmp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute('INSERT INTO notification (notifName, notifText, tmstmp, userID) VALUES (%s, %s, %s, %s)', (notifName, notifText, tmstmp, userID,))
            mysql.connection.commit()
            
            cursor.execute('INSERT INTO classroom (studentID, classID) VALUES (%s, %s)', (userID, classID))
            mysql.connection.commit()
            msg = 'Joined Class Successful.'
            return jsonify({'msg' : msg})
        return jsonify({'error' : 'Class doesnt exists'})
    return jsonify({'error' : 'Please fill out the form'})


# PROFILE
# PROFILE
# PROFILE

# User Account

@app.route("/profile/userID=<userID>")
def profile(userID):
    if 'loggedin' not in session:
        return redirect(url_for('sign_in'))
    userData = get_user(session['userID'])
    a = userData['fullname'].split(' ')
    b = []
    for a in a:
        b.append(a[:1].upper())

    img = ''.join(str(item) for item in b)
    return render_template('public/profile.html', userData=userData, img=img)

@app.route("/edit-profile", methods=['GET', 'POST'])
def edit_profile():
    fullname = request.form['fullname']
    email = request.form['email']
    username = request.form['username']
    userData = get_user(session['userID'])
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if fullname and email and username:
        if username == userData['username']:
            cursor.execute('UPDATE users SET fullname=%s, email=%s, username=%s WHERE userID=%s', (fullname, email, username, userData['userID'],))
            mysql.connection.commit()
            msg = 'Profile Information Updated'
            return jsonify({'msg' : msg})

        cursor.execute('SELECT username FROM users')
        un = cursor.fetchall()
        username_lists = []
        for x in un:
            for a, b in x.items():
                username_lists.append(b)

        if username in username_lists:
            return jsonify({'error' : 'Username is already taken.'})
        elif not re.match(r'[A-Za-z0-9]+', username):
            return jsonify({'error' : 'Username must contain only characters and numbers!'})
        else: 
            cursor.execute('UPDATE users SET  fullname=%s, email=%s, username=%s WHERE userID=%s', (fullname, email, username, userData['userID'],))
            mysql.connection.commit()
            msg = 'Profile Information Updated'
            return jsonify({'msg' : msg})
    return jsonify({'error' : 'Try Again'})


@app.route("/change-type", methods=['GET', 'POST'])
def change_type():
    usertype = str(request.form['type'])
    userData = get_user(session['userID'])
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if usertype == userData['type']:
        msg = 'You did nothing -_-'
        return jsonify({'msg' : msg})
    else:
        if userData['type'] == 'instructor':
            cursor.execute('DELETE FROM class WHERE instructorID = %s',  (userData['userID'],))
            mysql.connection.commit()
        elif userData['type'] == 'student':
            cursor.execute('DELETE FROM classroom WHERE studentID = %s',  (userData['userID'],))
            mysql.connection.commit()

        cursor.execute('UPDATE users SET type=%s WHERE userID = %s',  (usertype, userData['userID'],))
        mysql.connection.commit()
        msg = 'User Type successfully changed.'
        return jsonify({'msg' : msg})

@app.route("/change-password", methods=['GET', 'POST'])
def change_password():
    password = request.form['password']
    newPassword = request.form['newPassword']
    hash_new_password = generate_password_hash(newPassword)

    userData = get_user(session['userID'])
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if password and newPassword:
        if userData:
            password_hash = userData['password']
            if check_password_hash(password_hash, password):
                cursor.execute('UPDATE users SET password=%s WHERE userID=%s', (hash_new_password, userData['userID']))
                mysql.connection.commit()
                msg = 'Password Updated'
                return jsonify({'msg' : msg})
            else: 
                return jsonify({'error' : 'Password incorrect'})
    return jsonify({'error' : 'Please fill up the form'})


@app.route("/delete-account", methods=['GET', 'POST'])
def delete_account():
    password = request.form['password']
    userData = get_user(session['userID'])
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if password:
        password_hash = userData['password']
        if check_password_hash(password_hash, password):
            cursor.execute('DELETE FROM users WHERE userID = %s', (session['userID'],))
            mysql.connection.commit()
            msg = 'Account Succcessfully Deleted'
            return jsonify({'msg' : msg})
        else:
            return jsonify({'error' : 'Incorrect Password'})
    return jsonify({'error' : 'Text Field is empty -_-. Enter your password'})


# CLASS
# CLASS
# CLASS

# Home

@app.route("/classid=<classID>")
def class_home(classID):
    if 'loggedin' not in session:
        return redirect(url_for('sign_in'))
    
    status = trackerStatus()
    classData = get_class(classID)
    session['classID'] = classID
    userData = get_user(session['userID'])
    return render_template("public/classHome.html", userData=userData, classData=classData, status=status)

@app.route("/classid=<classID>/people")
def class_people(classID):
    if 'loggedin' not in session:
        return redirect(url_for('sign_in'))
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    cursor.execute('SELECT users.userID, users.fullname, users.type FROM users INNER JOIN classroom ON users.userID = classroom.studentID INNER JOIN class ON classroom.classID = class.classID WHERE class.classID = %s;', (classID,))
    students = cursor.fetchall()
    cursor.execute('SELECT users.fullname, users.type FROM users INNER JOIN class ON users.userID = class.instructorID WHERE class.classID = %s;', (classID,))
    instructor = cursor.fetchone()
    status = trackerStatus()
    classData = get_class(classID)
    session['classID'] = classData['classID']
    userData = get_user(session['userID'])
    return render_template("public/people.html", userData=userData, classData=classData, status=status, students=students, instructor=instructor)


# Configure

@app.route("/classid=<classID>/configure")
def class_configure(classID):
    if 'loggedin' not in session:
        return redirect(url_for('sign_in'))
    status = trackerStatus()
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    classData = get_class(classID)
    webBlockData = get_webBlock(classID)
    appBlockData = get_appBlock(classID)
    userData = get_user(session['userID'])
    session['classID'] = classData['classID']
    cursor.execute('SELECT * from productiveApps WHERE classID = %s', (classID,))
    productiveAppsData = cursor.fetchall()
    if userData['type'] == 'instructor':
        return render_template("instructor/configure.html", userData=userData, classData=classData, webBlockData=webBlockData, appBlockData=appBlockData, productiveAppsData=productiveAppsData)
    elif userData['type'] == 'student':
        return render_template("student/configure.html", userData=userData, classData=classData, webBlockData=webBlockData, appBlockData=appBlockData, productiveAppsData=productiveAppsData, status=status)

@app.route("/add-web-block", methods=['GET', 'POST'])
def add_web_block():
    blockName = request.form['blockName']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    webBlockData = get_webBlock(session['classID'])
    if blockName:
        cursor.execute('INSERT INTO blocker (blockName, blockType, blockStatus, classID) VALUES (%s, %s, %s, %s)', (blockName, 'web', 'disable', session['classID']))
        mysql.connection.commit()
        msg = 'Succcessfully Added'
        return jsonify({'msg' : msg})
    return jsonify({'error' : 'Please input a website url'})

@app.route("/save-web-block", methods=['GET', 'POST'])
def save_web_block():
    webBlock = request.form['webBlock'].split(',')
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT blockName FROM blocker WHERE blockType = %s and classID = %s', ('web',session['classID'],))
    x = cursor.fetchall()
    webBlockLists = []
    for x in x:
        for a, b in x.items():
            webBlockLists.append(b)

    if webBlock[0] == '':
        cursor.execute('UPDATE blocker SET blockStatus=%s WHERE classID=%s', ('disable', session['classID'],))
        mysql.connection.commit()
    
    for webBlockLists in webBlockLists:
        if webBlockLists in webBlock:
            cursor.execute('UPDATE blocker SET blockStatus=%s WHERE blockName=%s and classID=%s', ('enable', webBlockLists, session['classID'],))
            mysql.connection.commit()
        else: 
            cursor.execute('UPDATE blocker SET blockStatus=%s WHERE blockName=%s and classID=%s', ('disable', webBlockLists, session['classID'],))
            mysql.connection.commit()
    msg = 'Saved Successfully'
    return jsonify({'msg' : msg})


@app.route("/add-app-block", methods=['GET', 'POST'])
def add_app_block():
    blockName = request.form['blockName']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    appBlockData = get_appBlock(session['classID'])
    if blockName:
        if blockName not in appBlockData:
            cursor.execute('INSERT INTO blocker (blockName, blockType, blockStatus, classID) VALUES (%s, %s, %s, %s)', (blockName, 'app', 'disable', session['classID']))
            mysql.connection.commit()
            msg = 'Succcessfully Added'
            return jsonify({'msg' : msg})
        return jsonify({'error' : 'Application already added'})
    return jsonify({'error' : 'Please input an application name'})


@app.route("/save-app-block", methods=['GET', 'POST'])
def save_app_block():
    appBlock = request.form['appBlock'].split(',')
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT blockName FROM blocker WHERE blockType = %s and classID = %s', ('app',session['classID'],))
    x = cursor.fetchall()
    appBlockLists = []
    for x in x:
        for a, b in x.items():
            appBlockLists.append(b)
    print(appBlock)
    if appBlock[0] == '':
        cursor.execute('UPDATE blocker SET blockStatus=%s WHERE classID=%s', ('disable', session['classID'],))
        mysql.connection.commit()
    
    for appBlockLists in appBlockLists:
        if appBlockLists in appBlock:
            cursor.execute('UPDATE blocker SET blockStatus=%s WHERE blockName=%s and classID=%s', ('enable', appBlockLists, session['classID'],))
            mysql.connection.commit()
        else: 
            cursor.execute('UPDATE blocker SET blockStatus=%s WHERE blockName=%s and classID=%s', ('disable', appBlockLists, session['classID'],))
            mysql.connection.commit()
    msg = 'Saved Successfully'
    return jsonify({'msg' : msg})


@app.route("/add-productive-app", methods=['GET', 'POST'])
def add_productive_apps():
    appName = request.form['productiveApp']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT appName FROM productiveApps WHERE classID = %s', (session['classID'],))
    a = cursor.fetchall()
    lists = []
    for x in a:
        for y in x:
            lists.append(x[y])
    lists_lc = [x.lower() for x in lists]
    if appName:
        if appName.lower() in lists_lc:
            return jsonify({'error' : 'Application already added'})
        else:
            cursor.execute('INSERT INTO productiveApps(appName, classID) VALUES (%s, %s)', (appName, session['classID']))
            mysql.connection.commit()
            msg = 'Succcessfully Added'
            return jsonify({'msg' : msg})
    return jsonify({'error' : 'Please input a app name'})

@app.route("/delete-prod-app/<appName>", methods=['GET', 'POST'])
def delete_productive_app(appName):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('DELETE FROM productiveApps WHERE appName = %s and classID = %s', (appName, session['classID'],))
    mysql.connection.commit()
    flash('App Removed Successfully', 'popup-success')
    return redirect(url_for('class_configure', classID = session['classID']))

@app.route("/edit-class", methods=['GET', 'POST'])
def edit_class():
    className = request.form['className']
    classDesc = request.form['classDesc']
    classColor = request.form['classColor']
    classTimeStart = request.form['classTimeStart']
    classTimeEnd = request.form['classTimeEnd']
    classDay =  request.form['classDay']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if className and classDesc and classColor and classTimeStart and classTimeEnd and classDay:
        cursor.execute('UPDATE class SET className=%s, classDesc=%s, classColor=%s, classTimeStart=%s, classTimeEnd=%s, classDay=%s WHERE classID=%s', (className, classDesc, classColor, classTimeStart, classTimeEnd, classDay, session['classID']))
        mysql.connection.commit()
        msg = 'Class Updated'
        return jsonify({'msg' : msg})
    return jsonify({'error' : 'Try Again'})


# Function for Tracker
# Function for Tracker
# Function for Tracker

import time, datetime
import win32gui
import win32process
import pywinauto
import psutil
import ctypes
import sys
import subprocess
import os
import atexit
import keyboard 
from waiting import wait
from ctypes import Structure, windll, c_uint, sizeof, byref

def block_app(classID):
    while True:
        with app.app_context():
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT blockName FROM blocker WHERE blockType=%s and blockStatus=%s and classID=%s', ('app', 'enable', classID,))
            a = cursor.fetchall()
            appLists = []
            for x in a:
                for y in x:
                    appLists.append(x[y])
            # get lists of running processes
            processes = os.popen('wmic process get description, processid').read()
            for x in appLists:
                if x.lower() in processes.lower():
                    os.system('taskkill /f /im '+ x +'.exe')
            
            time.sleep(1)

# Tracker

def get_pid():
    try: 
        pid = win32process.GetWindowThreadProcessId(win32gui.GetForegroundWindow()) 
        return psutil.Process(pid[-1]).pid
    except: 
        x = 'Process ID not found'
        return x

def split_name(name):
    string = name.split('.')
    return string[0]
    
def get_active_window():
    try: 
        pid = win32process.GetWindowThreadProcessId(win32gui.GetForegroundWindow())
        return split_name(psutil.Process(pid[-1]).name())
    except:
        x = 'Name not found'
        return x

def url_to_name(url):
    link = url.split('/')
    if 'https' in url:
        return link[2]
    else:
        return link[0]

def get_browser_title():
    return win32gui.GetWindowText(win32gui.GetForegroundWindow())

def get_chrome_url():
    try:
        pid = get_pid()
        app = pywinauto.Application(backend='uia').connect(process = pid)
        dlg = app.top_window()
        url = dlg.child_window(title="Address and search bar", control_type="Edit").get_value()
        if url == '':
            url = 'blank or new tab'
            return url
        else:
            return url
    except:
        url = 'URL not found'
        return url

def get_specific_time(startTime, endTime):
    total_time = endTime - startTime
    total_secs = total_time.total_seconds()
    hrs =  int(total_secs // 3600)
    mins = int((total_secs % 3600) // 60)
    secs = int(total_secs % 60)
    return hrs, mins, secs

def is_not_active(hwnd):
    active = get_active_window()
    if hwnd != active:
        return True
    return False

def tracker(classID, userID):
    with app.app_context():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        activeWindowName = ''
        activityName = ''
        dt = datetime.datetime.now()
        curDate = dt.strftime('%Y-%m-%d')
        while True:
            newWindowName = get_active_window()
            startTime = datetime.datetime.now()
            if 'chrome' in newWindowName:
                newWindowName = url_to_name(get_chrome_url())
                title = get_browser_title()
                cursor.execute('INSERT INTO browser_titles (title, curTime, curDate, classID, studentID) VALUES (%s, %s, %s, %s, %s)', (title, startTime, curDate, classID, userID))
                mysql.connection.commit()

            if 'msedge' in newWindowName:
                title = get_browser_title()
                cursor.execute('INSERT INTO browser_titles (title, curTime, curDate, classID, studentID) VALUES (%s, %s, %s, %s, %s)', (title, startTime, curDate, classID, userID))
                mysql.connection.commit()

            if 'firefox' in newWindowName:
                title = get_browser_title()
                cursor.execute('INSERT INTO browser_titles (title, curTime, curDate, classID, studentID) VALUES (%s, %s, %s, %s, %s)', (title, startTime, curDate, classID, userID))
                mysql.connection.commit()
            
            if activeWindowName != newWindowName:
                activityName = newWindowName
                cursor.execute('INSERT INTO activity_log (activityName, curTime, curDate, classID, studentID) VALUES (%s, %s, %s, %s, %s)', (activityName, startTime, curDate, classID, userID))
                mysql.connection.commit()

                # wait until active window changes
                activeWindowName = activityName
                wait(lambda: is_not_active(activeWindowName))

                # insert time entry 
                endTime = datetime.datetime.now()
                hrs, mins, secs = get_specific_time(startTime, endTime)
                cursor.execute('INSERT INTO time_entries (activityName, startTime, endTime, hrs, mins, secs, curDate, classID, studentID) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)', (activityName, startTime, endTime, hrs, mins, secs, curDate, classID, userID))
                mysql.connection.commit()

            time.sleep(1)

# Running Apps

def running_apps(classID, userID):
    while True:
        cmd = 'powershell "gps | where {$_.MainWindowTitle } | select Name'
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        apps = []
        for line in proc.stdout:
            if line.rstrip():
                x = line.decode().rstrip()
                apps.append(x)
        indices = {0, 1}
        running_apps = str([v for i, v in enumerate(apps) if i not in indices])
        with app.app_context():
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            import datetime
            dt = datetime.datetime.now()
            curDate = dt.strftime('%Y-%m-%d')
            cursor.execute('SELECT appID from running_apps WHERE classID = %s and curDate = %s', (classID, curDate,))
            data = cursor.fetchone()

            if data == None:
                cursor.execute('INSERT INTO running_apps (appLists, curDate, classID, studentID) VALUES (%s, %s, %s, %s)', (running_apps, curDate, classID, userID))
                mysql.connection.commit()
            else: 
                cursor.execute('UPDATE running_apps SET appLists = %s WHERE curDate = %s and classID = %s and studentID = %s', (running_apps, curDate, classID, userID))
                mysql.connection.commit()
        time.sleep(20)

# Idle 

class LASTINPUTINFO(Structure):
    _fields_ = [
        ('cbSize', c_uint),
        ('dwTime', c_uint),
    ]

def get_idle_duration():
    lastInputInfo = LASTINPUTINFO()
    lastInputInfo.cbSize = sizeof(lastInputInfo)
    windll.user32.GetLastInputInfo(byref(lastInputInfo))
    millis = windll.kernel32.GetTickCount() - lastInputInfo.dwTime
    return millis / 1000.0

def idle(classID, userID):
    while True:
        GetLastInputInfo = int(get_idle_duration())
        with app.app_context():
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT idleTime FROM class WHERE classID = %s', (classID,))
            idleTime = cursor.fetchone()
            x = idleTime.get('idleTime')
            
            user = get_user(userID)

            if user.get('isActive') == '3':
                active = '1'
                cursor.execute('UPDATE users SET isActive = %s WHERE userID = %s', (active, userID,))
                mysql.connection.commit()

            if GetLastInputInfo >= x:
                # if GetLastInputInfo is 8 minutes, play a sound
                idled = '3'
                cursor.execute('UPDATE users SET isActive = %s WHERE userID = %s', (idled, userID,))
                mysql.connection.commit()

    time.sleep(1)

# Keystrokes

def keystrokes(classID, userID):
    tab = 0
    copy = 0
    paste = 0
    find = 0
    with app.app_context():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        import datetime
        dt = datetime.datetime.now()
        curDate = dt.strftime('%Y-%m-%d')
        while True:
            # Alt Tab
            if keyboard.is_pressed('alt') and keyboard.is_pressed('tab'):
                tab += 1
                cursor.execute('SELECT tab FROM keystrokes WHERE classID=%s AND studentID=%s AND curDate=%s', (classID, userID, curDate,))
                keyTab = cursor.fetchone()
                if keyTab == None:
                    cursor.execute('INSERT INTO keystrokes (tab, curDate, classID, studentID) VALUES (%s, %s, %s, %s)', (tab, curDate, classID, userID))
                    mysql.connection.commit()
                else:
                    cursor.execute('UPDATE keystrokes SET tab = %s WHERE curDate = %s AND classID = %s AND studentID = %s', (tab, curDate, classID, userID))
                    mysql.connection.commit()
                time.sleep(0.5)

            # Copy 
            if keyboard.is_pressed('ctrl') and keyboard.is_pressed('c'):
                copy += 1
                cursor.execute('SELECT copy FROM keystrokes WHERE curDate = %s AND classID = %s AND studentID = %s', (curDate, classID, userID,))
                keyCopy = cursor.fetchone()
                if keyCopy == None:
                    cursor.execute('INSERT INTO keystrokes (copy, curDate, classID, studentID) VALUES (%s, %s, %s, %s)', (copy, curDate, classID, userID))
                    mysql.connection.commit()
                else:
                    cursor.execute('UPDATE keystrokes SET copy = %s WHERE curDate = %s AND classID = %s AND studentID = %s', (copy, curDate, classID, userID))
                    mysql.connection.commit()
                time.sleep(0.5)
            
            # Paste 
            if keyboard.is_pressed('ctrl') and keyboard.is_pressed('v'):
                paste += 1
                cursor.execute('SELECT paste FROM keystrokes WHERE curDate = %s AND classID = %s AND studentID = %s', (curDate, classID, userID,))
                keyPaste = cursor.fetchone()
                if keyPaste == None:
                    cursor.execute('INSERT INTO keystrokes (paste, curDate, classID, studentID) VALUES (%s, %s, %s, %s)', (paste, curDate, classID, userID))
                    mysql.connection.commit()
                else:
                    cursor.execute('UPDATE keystrokes SET paste = %s WHERE curDate = %s AND classID = %s AND studentID = %s', (paste, curDate, classID, userID))
                    mysql.connection.commit()
                time.sleep(0.5)
            
            # Find 
            if keyboard.is_pressed('ctrl') and keyboard.is_pressed('f'):
                find += 1
                cursor.execute('SELECT find FROM keystrokes WHERE curDate = %s AND classID = %s AND studentID = %s', (curDate, classID, userID,))
                keyFind = cursor.fetchone()
                if keyFind == None:
                    cursor.execute('INSERT INTO keystrokes (find, curDate, classID, studentID) VALUES (%s, %s, %s, %s)', (find, curDate, classID, userID))
                    mysql.connection.commit()
                else:
                    cursor.execute('UPDATE keystrokes SET find = %s WHERE curDate = %s AND classID = %s AND studentID = %s', (find, curDate, classID, userID))
                    mysql.connection.commit()
                time.sleep(0.5)
                     
# Tracker get data

def get_log(classID, userID):
    with app.app_context():
        import datetime
        dt = datetime.datetime.now()
        curDate = dt.strftime('%Y-%m-%d')
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM activity_log WHERE classID = %s and studentID = %s and curDate = %s', (classID, userID, curDate))
        logData = cursor.fetchall()
        return logData

def get_time_entries(classID, userID):
    with app.app_context():
        import datetime
        dt = datetime.datetime.now()
        curDate = dt.strftime('%Y-%m-%d')
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT activityName, sum(hrs) as hrs, sum(mins) as mins, sum(secs) as secs FROM time_entries WHERE classID = %s and studentID = %s and curDate = %s GROUP BY activityName ORDER BY hrs DESC, mins DESC, secs DESC', (classID, userID, curDate,))
        x = cursor.fetchall()
        lists = []
        for x in x:
            total = (x['hrs'] * 3600) + (x['mins'] * 60) + x['secs']
            hrs =  total // 3600
            mins = (total % 3600) // 60
            secs = total % 60
            lists.append(x['activityName'])
            lists.append(hrs)
            lists.append(mins)
            lists.append(secs)
        
        entryData = [lists[i:i+4] for i in range(0, len(lists), 4)]
        return entryData

def get_running_apps(classID, userID):
    with app.app_context():
        import datetime
        dt = datetime.datetime.now()
        curDate = dt.strftime('%Y-%m-%d')
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT appLists FROM running_apps WHERE studentID = %s AND classID = %s AND curDate = %s', (userID, classID, curDate,))
        ca = cursor.fetchone()
        runningAppsData = []
        if ca == None:
            runningAppsData = ['no data']
        else: 
            a = []
            for x in ca.values():
                a.append(x)
            b = a[0].strip('][').split(', ')
            for b in b:
                c = b.split("'")
                runningAppsData.append(c[1])
        return runningAppsData

def get_browser_title_data(classID, userID):
    with app.app_context():
        import datetime
        dt = datetime.datetime.now()
        curDate = dt.strftime('%Y-%m-%d')
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM browser_titles WHERE studentID = %s AND classID = %s AND curDate = %s', (userID, classID, curDate,))
        titleData = cursor.fetchall()
        if titleData == None:
            titleData = []
        return titleData

def get_class_config(classID):
    with app.app_context():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT blocker, keystrokes, idle, idleTime FROM class WHERE classID = %s', (classID,))
        configData = cursor.fetchone()
        return configData

def get_prod_apps(classID):
    with app.app_context():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT appName FROM productiveApps WHERE classID = %s', (classID,))
        x = cursor.fetchall()
        data = []
        for x in x:
            for y in x:
                data.append(x[y].replace(" ", ""))
        return data

def get_prod_specific_time(total):
    hrs =  total // 3600
    mins = (total % 3600) // 60
    secs = total % 60
    return hrs, mins, secs

def get_time_prod(classID, userID):
    with app.app_context():
        entryData = get_time_entries(classID, userID)
        prodApps = get_prod_apps(classID)
        lists = [x.lower() for x in prodApps]
        import datetime
        dt = datetime.datetime.now()
        curDate = dt.strftime('%Y-%m-%d')

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT activityName, sum(hrs) as hrs, sum(mins) as mins, sum(secs) as secs FROM time_entries WHERE classID = %s and studentID = %s and curDate = %s GROUP BY activityName ORDER BY hrs DESC, mins DESC, secs DESC', (classID, userID, curDate))
        entryData = cursor.fetchall()
        prod = []
        notProd = []
        for x in entryData:
            total = (x['hrs'] * 3600) + (x['mins'] * 60) + x['secs']
            # check if activity or application is productive or not
            if x['activityName'].lower() in lists:
                prod.append(total)
            else:
                notProd.append(total)
        totalTime = sum(prod) + sum(notProd)
        
        # Specific time of productive apps
        timeProd = []
        try:
            prodPercent = int((sum(prod) / totalTime) * 100)
        except:
            prodPercent = 0
        hrs, mins, secs = get_prod_specific_time(sum(prod))
        timeProd.extend((prodPercent, hrs, mins , secs))

        # Specific time of not productive aps
        timeNotProd = []
        try:
            notProdPercent = int((sum(notProd) / totalTime) * 100)
        except:
            notProdPercent = 0
        hrs, mins, secs = get_prod_specific_time(sum(notProd))
        timeNotProd.extend((notProdPercent, hrs, mins , secs))
        
        prod = []
        prod.extend((timeProd, timeNotProd))
        return prod    

def get_total_time(classID, userID):
    with app.app_context():
        entryData = get_time_entries(classID, userID)
        prodApps = get_prod_apps(classID)
        lists = [x.lower() for x in prodApps]
        import datetime
        dt = datetime.datetime.now()
        curDate = dt.strftime('%Y-%m-%d')

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT activityName, sum(hrs) as hrs, sum(mins) as mins, sum(secs) as secs FROM time_entries WHERE classID = %s and studentID = %s and curDate = %s GROUP BY activityName ORDER BY hrs DESC, mins DESC, secs DESC', (classID, userID, curDate))
        entryData = cursor.fetchall()
        prod = []
        notProd = []
        for x in entryData:
            total = (x['hrs'] * 3600) + (x['mins'] * 60) + x['secs']
            # check if activity or application is productive or not
            if x['activityName'].lower() in lists:
                prod.append(total)
            else:
                notProd.append(total)
        totalTime = sum(prod) + sum(notProd)

        hrs, mins, secs = get_prod_specific_time(totalTime)
        a = []
        a.extend((hrs, mins, secs))
        return a

def get_keystrokes(classID, userID):
     with app.app_context():
        import datetime
        dt = datetime.datetime.now()
        curDate = dt.strftime('%Y-%m-%d')

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT tab, copy, paste, find FROM keystrokes WHERE classID = %s AND studentID = %s AND curDate = %s', (classID, userID, curDate,))
        x = cursor.fetchone()
        keyData = []

        try:
            for x in x.values():
                keyData.append(x)
        except:
            keyData.extend((0, 0, 0, 0))

        return keyData

def get_child():
    current_process = psutil.Process()
    children = current_process.children(recursive=True)
    x = []
    for child in children:
        x.append(child.pid)
    print(x)
    return x

def kill_child():
    try: 
        current_process = psutil.Process()
        children = current_process.children(recursive=True)
        for child in children:
            child.kill()
    except:
        print('no such process')

# API

app.config["CLIENT_JSON"] = "static/json"
from flask import send_file, send_from_directory, safe_join, abort
import json

@app.route("/api/web")
def web_api():
    with app.app_context():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        classID = session['classID']
        cursor.execute('SELECT blockName FROM blocker INNER JOIN class ON blocker.classID = class.classID INNER JOIN classroom ON class.classID = classroom.classID INNER JOIN users on classroom.studentID = users.userID WHERE blockType=%s and blockStatus=%s and isActive=%s and class.blocker=%s and blocker.classID=%s GROUP BY blockname', ('web', 'enable', '1', 'enable', classID))
        x = cursor.fetchall()
        web = []

        for x in x:
            for y in x:
                a = x[y].lower()
                web.append(a.replace(" ", ""))

        jsonString = json.dumps(web)

        with open('static/json/web.json', 'w') as f:
            f.write(jsonString)

        return jsonify(web)
        # filename = f"web.json"

        # try:
            # return send_from_directory(app.config["CLIENT_JSON"], path=filename, as_attachment=True)
        # except FileNotFoundError:
            # abort(404)

# Tracker

blockAppProcess = None
trackerProcess = None
runningAppsProcess = None
idleProcess = None
keystrokesProcess = None

@app.route("/classid=<classID>/tracker")
def class_tracker(classID):
    if 'loggedin' not in session:
        return redirect(url_for('sign_in'))
    
    classData = get_class(classID)
    userData = get_user(session['userID'])
    session['classID'] = classData['classID']
    if userData['type'] == 'instructor':
        studentLists = get_students(classID)
        prodApps = get_prod_apps(classID)
        return render_template("instructor/tracker.html", userData=userData, classData=classData, studentLists=studentLists, prodApps=prodApps)

    elif userData['type'] == 'student':

        if 'tracker' in session:
            return redirect(url_for('class_start_tracker', classID = classData['classID']))
        else:
            return render_template("student/tracker.html", userData=userData, classData=classData)

@app.route("/classid=<classID>/tracker/start")
def class_start_tracker(classID):
    if 'loggedin' not in session:
        return redirect(url_for('sign_in'))
    
    # get Data
    classData = get_class(classID)
    userData = get_user(session['userID'])
    configData = get_class_config(classID)
    session['classID'] = classData['classID']

    # Define Process
    global trackerProcess
    global blockAppProcess
    global runningAppsProcess
    global idleProcess
    global keystrokesProcess

    trackerProcess = multiprocessing.Process(target=tracker, args=(classID, userData['userID']), daemon=True, name='TrackerProcess')
    blockAppProcess = multiprocessing.Process(target=block_app, args=(classID,), daemon=True, name='blockAppProcess')
    runningAppsProcess = multiprocessing.Process(target=running_apps, args=(classID, userData['userID']), daemon=True, name='runningAppsProcess')
    idleProcess = multiprocessing.Process(target=idle, args=(classID, userData['userID']), daemon=True, name='idleProcess')
    keystrokesProcess = multiprocessing.Process(target=keystrokes, args=(classID, userData['userID']), daemon=True, name='keystrokesProcess')

    # Start Process
    if 'tracker' not in session:
        trackerProcess.start()
        runningAppsProcess.start()
        if configData.get('blocker') == 'enable':
            blockAppProcess.start()
        if configData.get('keystrokes') == 'enable':
            idleProcess.start()
        if configData.get('idle') == 'enable':
            keystrokesProcess.start()

        session['tracker'] = True
        status = trackerStatus()
    else: 
        status = trackerStatus()

    get_child()
    # Update user status
    active = '1'
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('UPDATE users SET isActive = %s WHERE userID = %s', (active, userData['userID']))
    mysql.connection.commit()

    return render_template("student/startTracker.html", userData=userData, classData=classData)

@app.route("/classid=<classID>/tracker/stop")
def class_stop_tracker(classID):
    if 'loggedin' not in session:
        return redirect(url_for('sign_in'))

    # get data
    status = trackerStatus()
    classData = get_class(classID)
    userData = get_user(session['userID'])
    session['classID'] = classData['classID']
    
    # update user status
    not_active = '0'
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('UPDATE users SET isActive = %s WHERE userID = %s', (not_active, userData['userID']))
    mysql.connection.commit()

    if 'tracker' in session:
        session.pop('tracker', None)
        #terminate process
        try:
            blockAppProcess.terminate()
            trackerProcess.terminate()
            runningAppsProcess.terminate()
            idleProcess.terminate()
            keystrokesProcess.terminate()
        except:
            pass

    kill_child()
    get_child()

    with open('static/json/web.json', 'w') as f:
        f.truncate()

    global notificationProcess
    notificationProcess = multiprocessing.Process(target=notif_process, args=(userData['userID'],), daemon=True, name='NotificationProcess')
    notificationProcess.start()

    return render_template("student/tracker.html", userData=userData, classData=classData)

@app.route("/classid=<classID>/tracker/view=<studentID>")
def view_track_record(classID, studentID):
    if 'loggedin' not in session:
        return redirect(url_for('sign_in'))
    import datetime
    dt = datetime.datetime.now()
    curDate = dt.strftime('%Y-%m-%d')
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM users WHERE userID = %s', (studentID,))
    studentData = cursor.fetchone()
    cursor.execute('SELECT activityName FROM activity_log WHERE studentID=%s AND classID=%s AND curDate=%s ORDER BY logID DESC LIMIT 1', (studentID, classID, curDate))
    currentAct = cursor.fetchone()
    cursor.execute('select curDate from activity_log WHERE classID = %s AND studentID = %s GROUP BY curDate ORDER BY curDate DESC;', (classID, studentID,))
    dates = cursor.fetchall()

    # get Data
    classData = get_class(classID)
    userData = get_user(session['userID'])
    logData = get_log(classID, studentID)
    entryData = get_time_entries(classID, studentID)
    runningAppsData = get_running_apps(classID, studentID)
    timeProd = get_time_prod(classID, studentID)
    titleData = get_browser_title_data(classID, studentID)
    keyData = get_keystrokes(classID, studentID)
    prodApps = get_prod_apps(classID)
    totalTime = get_total_time(classID, studentID)
    session['classID'] = classData['classID']

    return render_template('instructor/viewTrackRecord.html', userData=userData, classData=classData, studentData=studentData, logData=logData, entryData=entryData, runningAppsData=runningAppsData, timeProd=timeProd, titleData=titleData, keyData=keyData, prodApps=prodApps, currentAct=currentAct, dates=dates, totalTime=totalTime)

@app.route("/classid=<classID>/tracker/view=<studentID>/add/<appName>", methods=['GET', 'POST'])
def add_terminate_app(appName, classID, studentID):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT blockName FROM blocker WHERE blockType = %s AND classID = %s', ('app', session['classID'],))
    a = cursor.fetchall()
    lists = []
    for x in a:
        for y in x:
            lists.append(x[y])
    blockApp = [x.lower() for x in lists]

    if appName.lower() in blockApp:
        flash('Application already added', 'popup-error')
        return redirect(url_for('view_track_record', classID = session['classID'], studentID=studentID))
    else:
        cursor.execute('INSERT INTO blocker(blockName, blockType, blockStatus, classID) VALUES(%s, %s, %s, %s)', (appName, 'app', 'enable', session['classID'],))
        mysql.connection.commit()
        flash(' Successfully', 'popup-success')
        return redirect(url_for('view_track_record', classID = session['classID'], studentID=studentID))

@app.route("/classid=<classID>/tracker/view=<studentID>/add/prod/<appName>", methods=['GET', 'POST'])
def add_prod_app(appName, classID, studentID):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT appName FROM productiveApps WHERE classID = %s', (session['classID'],))
    a = cursor.fetchall()
    lists = []
    for x in a:
        for y in x:
            lists.append(x[y])
    lists_lc = [x.lower() for x in lists]
    if appName.lower() in lists_lc:
        flash('Application already added', 'popup-error')
        return redirect(url_for('view_track_record', classID = session['classID'], studentID=studentID))
    else:
        cursor.execute('INSERT INTO productiveApps(appName, classID) VALUES (%s, %s)', (appName, session['classID']))
        mysql.connection.commit()
        flash(' Successfully', 'popup-success')
        return redirect(url_for('view_track_record', classID = session['classID'], studentID=studentID))

@app.route("/save-tracker-config", methods=['GET', 'POST'])
def save_tracker_config():
    blocker = request.form['blocker'].split(',')
    keystrokes = request.form['kbLimit'].split(',')
    idle = request.form['idle'].split(',')
    idleTime = request.form['numOfIdle']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('UPDATE class SET blocker=%s, keystrokes=%s, idle=%s, idleTime=%s WHERE classID=%s', (blocker[0], keystrokes[0], idle[0], idleTime, session['classID']))
    mysql.connection.commit()
    msg = 'Saved'
    return jsonify({'msg' : msg})

@app.route("/grid-view", methods=['GET', 'POST'])
def gridView():
    with app.app_context():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        grid = request.form['gridValue']
        cursor.execute('UPDATE class SET viewType=%s WHERE classID=%s', (grid, session['classID']))
        mysql.connection.commit()
        return jsonify(grid)

@app.route("/list-view", methods=['GET', 'POST'])
def listView():
    with app.app_context():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        lists = request.form['listValue']
        cursor.execute('UPDATE class SET viewType=%s WHERE classID=%s', (lists, session['classID']))
        mysql.connection.commit()
        return jsonify(lists)

@app.route("/publish-class", methods=['GET', 'POST'])
def publishClass():
    with app.app_context():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        publishValue = request.form['publishValue']
        cursor.execute('UPDATE class SET publish=%s WHERE classID=%s', (publishValue, session['classID']))
        mysql.connection.commit()
        return jsonify(publishValue)

@app.route("/unpublish-class", methods=['GET', 'POST'])
def unpublishClass():
    with app.app_context():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        unpublishValue = request.form['unpublishValue']
        cursor.execute('UPDATE class SET publish=%s WHERE classID=%s', (unpublishValue, session['classID']))
        mysql.connection.commit()
        return jsonify(unpublishValue)

def getLogDate(classID, userID, date):
    with app.app_context():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM activity_log WHERE classID = %s and studentID = %s and curDate = %s', (classID, userID, date))
        logData = cursor.fetchall()
        return logData

def getTimeDate(classID, userID, date):
    with app.app_context():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT activityName, sum(hrs) as hrs, sum(mins) as mins, sum(secs) as secs FROM time_entries WHERE classID = %s and studentID = %s and curDate = %s GROUP BY activityName ORDER BY hrs DESC, mins DESC, secs DESC', (classID, userID, date))
        x = cursor.fetchall()
        lists = []
        for x in x:
            total = (x['hrs'] * 3600) + (x['mins'] * 60) + x['secs']
            hrs =  total // 3600
            mins = (total % 3600) // 60
            secs = total % 60
            lists.append(x['activityName'])
            lists.append(hrs)
            lists.append(mins)
            lists.append(secs)
        
        entryData = [lists[i:i+4] for i in range(0, len(lists), 4)]
        return entryData

def getRunningDate(classID, userID, date):
    with app.app_context():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT appLists FROM running_apps WHERE studentID = %s AND classID = %s AND curDate = %s', (userID, classID, date,))
        ca = cursor.fetchone()
        runningAppsData = []
        if ca == None:
            runningAppsData = ['no data']
        else: 
            a = []
            for x in ca.values():
                a.append(x)
            b = a[0].strip('][').split(', ')
            for b in b:
                c = b.split("'")
                runningAppsData.append(c[1])
        return runningAppsData

def getBrowserDate(classID, userID, date):
    with app.app_context():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM browser_titles WHERE studentID = %s AND classID = %s AND curDate = %s', (userID, classID, date,))
        titleData = cursor.fetchall()
        if titleData == None:
            titleData = []
        return titleData

def getTimeProdDate(classID, userID, date):
    with app.app_context():
        entryData = get_time_entries(classID, userID)
        prodApps = get_prod_apps(classID)
        lists = [x.lower() for x in prodApps]

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT activityName, sum(hrs) as hrs, sum(mins) as mins, sum(secs) as secs FROM time_entries WHERE classID = %s and studentID = %s and curDate = %s GROUP BY activityName ORDER BY hrs DESC, mins DESC, secs DESC', (classID, userID, date))
        entryData = cursor.fetchall()
        prod = []
        notProd = []
        for x in entryData:
            total = (x['hrs'] * 3600) + (x['mins'] * 60) + x['secs']
            # check if activity or application is productive or not
            if x['activityName'].lower() in lists:
                prod.append(total)
            else:
                notProd.append(total)
        totalTime = sum(prod) + sum(notProd)
        
        # Specific time of productive apps
        timeProd = []
        try:
            prodPercent = int((sum(prod) / totalTime) * 100)
        except:
            prodPercent = 0
        hrs, mins, secs = get_prod_specific_time(sum(prod))
        timeProd.extend((prodPercent, hrs, mins , secs))

        # Specific time of not productive aps
        timeNotProd = []
        try:
            notProdPercent = int((sum(notProd) / totalTime) * 100)
        except:
            notProdPercent = 0
        hrs, mins, secs = get_prod_specific_time(sum(notProd))
        timeNotProd.extend((notProdPercent, hrs, mins , secs))
        
        prod = []
        prod.extend((timeProd, timeNotProd))
        return prod    

def getKeyDate(classID, userID, date):
     with app.app_context():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT tab, copy, paste, find FROM keystrokes WHERE classID = %s AND studentID = %s AND curDate = %s', (classID, userID, date,))
        x = cursor.fetchone()
        keyData = []

        try:
            for x in x.values():
                keyData.append(x)
        except:
            keyData.extend((0, 0, 0, 0))

        return keyData

def get_total_time_date(classID, userID, date):
    with app.app_context():
        entryData = get_time_entries(classID, userID)
        prodApps = get_prod_apps(classID)
        lists = [x.lower() for x in prodApps]

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT activityName, sum(hrs) as hrs, sum(mins) as mins, sum(secs) as secs FROM time_entries WHERE classID = %s and studentID = %s and curDate = %s GROUP BY activityName ORDER BY hrs DESC, mins DESC, secs DESC', (classID, userID, date))
        entryData = cursor.fetchall()
        prod = []
        notProd = []
        for x in entryData:
            total = (x['hrs'] * 3600) + (x['mins'] * 60) + x['secs']
            # check if activity or application is productive or not
            if x['activityName'].lower() in lists:
                prod.append(total)
            else:
                notProd.append(total)
        totalTime = sum(prod) + sum(notProd)

        hrs, mins, secs = get_prod_specific_time(totalTime)
        a = []
        a.extend((hrs, mins, secs))
        return a

@app.route("/classid=<classID>/tracker/view=<studentID>/date=<date>")
def trackRecordDate(classID, studentID, date):
    if 'loggedin' not in session:
        return redirect(url_for('sign_in'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM users WHERE userID = %s', (studentID,))
    studentData = cursor.fetchone()
    cursor.execute('select curDate from activity_log WHERE classID = %s AND studentID = %s GROUP BY curDate;', (classID, studentID,))
    dates = cursor.fetchall()
    classData = get_class(classID)

    # get Data
    userData = get_user(session['userID'])
    logData = getLogDate(classID, studentID, date)
    entryData = getTimeDate(classID, studentID, date)
    runningAppsData = getRunningDate(classID, studentID, date)
    timeProd = getTimeProdDate(classID, studentID, date)
    titleData = getBrowserDate(classID, studentID, date)
    keyData = getKeyDate(classID, studentID, date)
    prodApps = get_prod_apps(classID)
    totalTime = get_total_time_date(classID, studentID, date)
    session['classID'] = classData['classID']

    return render_template('instructor/viewTrackRecord.html', userData=userData, classData=classData, studentData=studentData, logData=logData, entryData=entryData, runningAppsData=runningAppsData, timeProd=timeProd, titleData=titleData, keyData=keyData, prodApps=prodApps, dates=dates, totalTime=totalTime)


@app.route("/extension-exist", methods=['GET', 'POST'])
def checkExtension():
    with app.app_context():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        resp_json = request.get_data()
        params = resp_json.decode()
        if params == 'exist':
            extension = '1'
            try:
                cursor.execute('UPDATE users SET extension = %s WHERE userID = %s', (extension, session['userID'],))
                mysql.connection.commit()
            except:
                pass

        return 'Pass'

@atexit.register
def atexit():
        kill_child()
        with open('static/json/web.json', 'w') as f:
            f.truncate()
        

import webbrowser
from threading import Timer

def open_browser():
    webbrowser.open_new('http://127.0.0.1:5000/')

if __name__ ==  '__main__':
    multiprocessing.freeze_support()
    Timer(1, open_browser).start()
    app.run(use_reloader=False)