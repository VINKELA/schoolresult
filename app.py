import os
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, jsonify, url_for, make_response
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash
import re
import datetime
from flask_mail import Message, Mail
from itsdangerous import URLSafeTimedSerializer
import random
import string
from requests.models import Response

from operator import itemgetter, attrgetter

from functions import apology, login_required, database, random_string_generator, render_portfolio, term_tables, drop_tables, grade, assign_student_position, assign_subject_position, passwordGen, initials, add_student, remove_student, render_class, render_portfolio

# Configure application
app = Flask(__name__)


# generate confirmation token given email
def generate_confirmation_token(email):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=app.config['SECURITY_PASSWORD_SALT'])

# return email given confirmation token
def confirm_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token,
            salt=app.config['SECURITY_PASSWORD_SALT'],
            max_age=expiration
        )
    except:
        return False
    return email
# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["SECRET_KEY"] = "precious_two"
app.config["SECURITY_PASSWORD_SALT"] = "precious"


# send message to email
def send_email(to, subject, template, sender_email):
    msg = Message(
        subject,
        recipients=[to],
        html=template,
        sender=sender_email
    )
    mail.send(msg)


app.config.update(dict(
    DEBUG = True,
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = 587,
    MAIL_USE_TLS = True,
    MAIL_USE_SSL = False,
    MAIL_USERNAME = "orjikalukelvin@gmail.com",
    MAIL_PASSWORD = "gmailvenuse123",
))

mail = Mail(app)


# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///schools.db")

info = {}
subject_info = {}
error = None
class_scores = []
all_students = []
single_details = {}
single_subject = []



@app.route("/")
def index():
    if not request.cookies.get("series_id"):
        session.clear()
        return render_template("login.html")
    else:
        user = db.execute("SELECT * FROM school WHERE token_id = :series", series = request.cookies.get("series_id"))
        if len(user) != 1:
            session.clear()
            return render_template("login.html")
        if not check_password_hash(user[0]["token"], request.cookies.get("main_token")):
            session.clear()
            error = " theft dedicated, leave the site"
            return render_template("login.html", error = error)
        session["user_id"] = user[0]["id"]
        # if account is confirmed render this
        if(user[0]["confirmed"]== "true"):
            return render_portfolio()
        # else if account is not confirmed render unconfirmed view
        else:
            return redirect('/unconfirmed')

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return render_template("/login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure email was submitted
        if not request.form.get("email"):
            error = "you must provide email"
            return render_template("register.html", error = error)
        if not request.form.get("school_name"):
            error = "you must provide school name"
            return render_template("register.html", error = error)
        # Ensure term was submitted
        if not request.form.get("term"):
            error = "you must provide current term"
            return render_template("register.html", error = error)
        # ensure session was submitted
        if not request.form.get("school_session"):
            error = "you must provide current session"
            return render_template("register.html", error = error)
        # ensure username was submitted
        if not request.form.get("username"):
            error = "you must provide a unique username"
            return render_template("register.html", error = error)
        # ensure the username is not taken
        username_check = db.execute("SELECT * FROM school WHERE username = :username", username = request.form.get("username").lower())
        if  len(username_check) > 0:
            error = "username: "+request.form.get("username")+" already taken, choose another one"
            return render_template("register.html", error = error)
        email_check = db.execute("SELECT * FROM school WHERE email = :email", email = request.form.get("email").lower())
        if  len(email_check) > 0:
            error = "Another account has been opened with email: "+request.form.get("email")
            return render_template("register.html", error = error)

        # Ensure password was submitted
        if not request.form.get("password"):
            error = "you must provide password"
            return render_template("register.html", error = error)

        # Ensure confirmation was submitted
        if not request.form.get("confirmation"):
            error = "you must provide confirmation"
            return render_template("register.html", error = error)

        # Ensure password and confirmation match
        if (request.form.get("password") != request.form.get("confirmation")):
            error = "password and confirmation do not match"
            return render_template("register.html", error = error)

        password = request.form.get("password")
        if len(password) < 8:
            error = "Make sure your password is at lest 8 letters"
            return render_template("register.html", error = error)
        general_password = passwordGen()
        token = generate_confirmation_token(request.form.get("email"))
        confirm_url = url_for('confirm_email', token=token, _external=True)
        html = render_template('confirm_email.html', confirm_url=confirm_url, password = general_password)
        subject = "Please confirm your email"
        try:
            send_email(request.form.get("email"), subject, html, 'orjikalukelvin@gmail.com')
        except Exception as e:
            print(e)
        db.execute("INSERT INTO school (school_name, email,username, password,admin_password,current_session,current_term, registered_on) VALUES (:schoolname, :email, :username, :hash,  :adminPassword,:current_session,:term, :registered_on)", schoolname = request.form.get("school_name").upper(), email= request.form.get("email").lower(), username = request.form.get("username").lower(), hash = generate_password_hash(general_password), adminPassword = generate_password_hash(request.form.get("password")),current_session = request.form.get("school_session"),term=request.form.get("term"), registered_on = datetime.datetime.now())
        # Query database for username
        rows = db.execute("SELECT * FROM school WHERE username = :username",username=request.form.get("username").lower())
        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        tables = database(str(0))
        column = request.form.get("school_session")+"_"+str(request.form.get("term"))
        db.execute("CREATE TABLE :sessions ('id' INTEGER PRIMARY KEY NOT NULL, :column TEXT)", sessions = tables["sessions"], column=column)
        db.execute("CREATE TABLE :classes ('id' INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,'identifier' TEXT )", classes = tables["classes"])
        db.execute("CREATE TABLE :setting ('id' INTEGER PRIMARY KEY NOT NULL, 'classname' TEXT, 'grading_type' INTEGER, 'comment_lines' INTEGER,'student_position' INTEGER DEFAULT 1, 'surname' TEXT, 'firstname' TEXT,'othername' TEXT,'password' TEXT,'section' TEXT, 'ca' INTEGER, 'test' INTEGER,'exam' INTEGER)", setting = tables["session_data"])
        # create result data
        db.execute("CREATE TABLE :result ('id' INTEGER PRIMARY KEY  NOT NULL, 'noOfStudents' INTEGER DEFAULT 0,'noOfSubjects' INTEGER DEFAULT 0, 'no_of_passes' INTEGER DEFAULT 0, 'no_of_failures' INTEGER DEFAULT 0, 'grading_type' TEXT DEFAULT 'waec','background_color' TEXT DEFAULT 'white','text_color' TEXT DEFAULT 'black','line_color' TEXT DEFAULT 'black','background_font' TEXT DEFAULT 'Ariel','ld_position' TEXT DEFAULT 'center','l_font' TEXT DEFAULT 'Ariel Black','l_weight' TEXT DEFAULT '900','l_color' TEXT DEFAULT '#00ff40','l_fontsize' TEXT DEFAULT '30px','sd_font' TEXT DEFAULT 'Ariel','sd_color' TEXT DEFAULT '#808000','sd_fontsize' TEXT DEFAULT '20px','sd_position' TEXT DEFAULT 'center','sd_email' TEXT,'admin_email' TEXT DEFAULT 'off', 'address' TEXT,'po_box' TEXT,'phone' TEXT,'next_term' TEXT,'sd_other' TEXT,'std_color' TEXT DEFAULT 'black','std_font' TEXT DEFAULT 'Arial Narrow','std_fontsize' TEXT DEFAULT '18px','std_position' TEXT DEFAULT 'left','table_type' TEXT DEFAULT 'bordered','ca' TEXT DEFAULT 'on','test' TEXT DEFAULT 'on','exam' TEXT DEFAULT 'on','combined' TEXT DEFAULT 'on','subject_total' TEXT DEFAULT 'on','class_average' TEXT DEFAULT 'on','subject_position' TEXT DEFAULT 'on','grade' TEXT DEFAULT 'on','subject_comment' TEXT DEFAULT 'off','teachers_initials' TEXT DEFAULT 'on','total_score' TEXT DEFAULT 'on','average' TEXT DEFAULT 'on','position' TEXT DEFAULT 'on','teachers_line' INTEGER DEFAULT 0,'shadow' TEXT DEFAULT 'on','principal_line' INTEGER DEFAULT 0,'teachers_signature' TEXT DEFAULT 'off','principal_signature' TEXT DEFAULT 'off','pandf' TEXT DEFAULT 'on','grade_summary' TEXT DEFAULT 'on','watermark' TEXT DEFAULT 'on')",result = tables["class_term_data"])

        return render_template("unconfirmed.html", schoolInfo=rows)
    else:
        return render_template("register.html")


@app.route("/confirm_email", methods=["GET", "POST"])
def confirm_email():
    token = request.args.get('token')
    email = confirm_token(token)
    if  not email:
        error = 'The confirmation link is invalid or has expired.'
    else:
        user = db.execute("SELECT * FROM school WHERE email=:email", email = email)
        if user[0]["confirmed"] == "true":
            error = 'Account already confirmed. Please login.'
        else:
            db.execute("UPDATE school SET confirmed = :true WHERE email=:email ", email = email, true="true")
            db.execute("UPDATE school SET confirmed_on = :date WHERE email=:email ",email = email, date = datetime.datetime.now())
            error = 'You have confirmed your account.  Thanks!'
    session.clear()
    flash(error)
    return render_template('login.html',)

@app.route("/unconfirmed", methods=["GET", "POST"])
def unconfirmed():
    user = db.execute("SELECT * FROM school WHERE id=:id", id = session["user_id"])
    if user[0]["confirmed"] == "true":
        rows = db.execute("SELECT * FROM school WHERE id = :id",id = session["user_id"])
        return render_template("portfolio.html", schoolInfo = rows)
    rows = db.execute("SELECT * FROM school WHERE id = :id",id = session["user_id"])
    error = "Your account have not been confirmed and you dont have full access to it"
    return render_template('unconfirmed.html', schoolInfo=rows)

@app.route("/resend_confirmation", methods=["GET", "POST"])
def resend_confirmation():
    user = db.execute("SELECT * FROM school WHERE id=:id", id = session["user_id"])
    token = generate_confirmation_token(user[0]["email"])
    confirm_url = url_for('confirm_email', token=token, _external=True)
    html = render_template('confirm_email.html', confirm_url=confirm_url)
    subject = "Please confirm your email"
    try:
        send_email(user[0]["email"], subject, html,'classresultest@gmail.com')
    except Exception as e:
        print(e)
    flash('A new confirmation email has been sent.', 'success')
    return redirect('/unconfirmed')


@app.route("/subject_check", methods=["POST"])
def subject_check():
    tables = database(int(request.form.get("class_id")))
    # Query database for username
    subject_row = db.execute("SELECT * FROM :subjects WHERE name =:subject_name", subjects = tables["subjects"], subject_name = str(request.form.get("subject_name")).lower())
    if len(subject_row) > 0:
        return "false"
    else:
        return "true"



@app.route("/editclass_check", methods=["POST"])
def editclass_check():
    class_id = str(request.form.get("class_id"))
    password = request.form.get("password")
    tables = database(class_id)
    # Query database for username
    class_row = db.execute("SELECT * FROM :session_data WHERE id =:id", session_data = tables["session_data"], id=class_id)
    rows = db.execute("SELECT * FROM school WHERE id =:id", id=session["user_id"])
    if not check_password_hash(rows[0]["admin_password"],password) and not check_password_hash(class_row[0]["password"],password ):
        return "false"
    else:
        return "true"


@app.route("/username_check", methods=["POST"])
def register_check():
    if request.method == "POST":
        # Query database for username
        rows = db.execute("SELECT * FROM school WHERE username = :username",username=request.form.get("username").lower())
        if len(rows) == 0:
            return "true"
        else:
            return "false"



@app.route("/email_check", methods=["POST"])
def email_check():
    if request.method == "POST":
        # Query database for email
        rows = db.execute("SELECT * FROM school WHERE email = :email",email=request.form.get("email").lower())
        if len(rows) == 0:
            return "true"
        else:
            return "false"


@app.route("/login", methods=["POST","GET"])
def login():
    if request.method == "POST":
        if request.form.get("username")=="":
            error = "username field cannot be empty"
            return render_template("login.html", error = error)
        if request.form.get("password")=="":
            error = "password field cannot be empty"
            return render_template("login.html", error = error)
        # Query database for username
        rows = db.execute("SELECT * FROM school WHERE username = :username",username=str(request.form.get("username")).lower())
        # Remember which user has logged in
        # Ensure username exists and password is correct
        if len(rows) == 0:
            error = "user does not exist"
            return render_template ("login.html", error=error)
        if not check_password_hash(rows[0]["admin_password"], request.form.get("password")) and not check_password_hash(rows[0]["password"], request.form.get("password")):
            error = "invalid username/password"
            print(request.form.get("password"))
            return render_template("login.html", error = error)
        session["user_id"] = rows[0]["id"]
        if rows[0]["username"] == "admin":
            # select all the schools
            all_schools = db.execute("SELECT * FROM school")
            # display them in admin portfolio
            return render_template("admin_page.html", schoolInfo = all_schools)
        # if account is confirmed render this
        if(rows[0]["confirmed"]== "true"):
            tables = database(str(0))
            classRows = db.execute("SELECT * FROM :session_data ",session_data = tables["session_data"])
            # if remember me check box is checked
            if request.form.get("remember_me") == "checked":
                # generate token
                random_token = random_string_generator(12, string.ascii_letters+string.punctuation)
                # generate series id
                random_series = random_string_generator(12, string.ascii_letters+string.punctuation)
                #set cookie
                resp = make_response(render_template("portfolio.html",schoolInfo = rows, clas = classRows))
                expire_date = datetime.datetime.now()
                expire_date = expire_date + datetime.timedelta(days=90)
                resp.set_cookie("series_id",random_series,expires=expire_date)
                resp.set_cookie("main_token", random_token,expires=expire_date)
                db.execute("UPDATE school SET token_id = :series, token = :token WHERE id=:id", series = random_series, token = generate_password_hash(random_token), id=session["user_id"])
                return resp
                # return render portfolio
            return render_template("portfolio.html", schoolInfo = rows, clas = classRows)

        # else if account is not confirmed render unconfirmed view
        else:
            return redirect('/unconfirmed')
    else:
        try:
            session["user_id"]
        except KeyError:
            return render_template("login.html")
        else:
            rows = db.execute("SELECT * FROM school WHERE id = :id",id = session["user_id"])
            # if account is confirmed render this
            if(rows[0]["confirmed"]== "true"):
                tables = database(str(0))
                rows = db.execute("SELECT * FROM school WHERE id=:id", id = session["user_id"])
                classRows = db.execute("SELECT * FROM :session_data ",session_data = tables["session_data"])
                # return render portfolio
                return render_template("portfolio.html", schoolInfo = rows, clas = classRows)

            # else if account is not confirmed render unconfirmed view
            else:
                return redirect('/unconfirmed')


@app.route("/change_password", methods=["POST", "GET"])
def change_password():
    if request.method == "POST":
        # Query database for email
        if request.form.get("email") == "":
            error = "provide the email your account was registered with"
            return render_template("change_password_form.html", error = error)
        rows = db.execute("SELECT * FROM school WHERE email = :email",email=request.form.get("email").lower())
        if len(rows) != 1:
            error = request.form.get("email")+" not associated with any registered account"
            return render_template("change_password_form.html", error = error)
        token = generate_confirmation_token(request.form.get("email"))
        confirm_url = url_for('password_changed', token=token, _external=True)
        html = render_template('password.html', confirm_url=confirm_url)
        subject = "change password"
        try:
            send_email(request.form.get("email"), subject, html, 'classresultest@gmail.com')
        except Exception as e:
            print(e)
        error = "follow the link sent to "+request.form.get("email") +" to change password"
        return render_template("login.html", error=error)
    else:
        return render_template("change_password_form.html")


@app.route("/password_changed", methods=["GET", "POST"])
def password_changed():
    if request.method == "POST":
        email = request.form.get("email")
        if request.form.get("password") == "":
            error = "password is empty"
            return render_template("password_changed.html", error = error, email = email)
        if len(request.form.get("password")) < 8:
            error = "Make sure your password is at lest 8 letters"
            return render_template("password_changed.html", error = error)

        if request.form.get("confirmation") == "":
            error = "confirmation is empty"
            return render_template("password_changed.html", error = error, email = email)
        if request.form.get("password") != request.form.get("confirmation"):
            error = "password and confirmation do not match"
            return render_template("password_changed", error = error, email = email)
        #change the password
        db.execute("UPDATE school SET admin_password = :password WHERE email=:email ",password = generate_password_hash(request.form.get("password")), email = email)
        error = 'You have changed your password.  Thanks!'
        session.clear()
        return render_template('login.html',error=error)
    else:
        token = user = request.args.get('token')
        email = confirm_token(token)
        if  not email:
            error = 'The  link is invalid or has expired.'
            return render_template("login.html", error = error)
        else:
            return render_template("password_changed.html", email = email)


@app.route("/login_check", methods=["POST"])
def login_check():
    if request.method == "POST":
        # Query database for username
        rows = db.execute("SELECT * FROM school WHERE username = :theusername",theusername=request.form.get("username").lower())
        if len(rows) == 0:
            return "fail"
        # Ensure username exists and password is correct
        if check_password_hash(rows[0]["password"], request.form.get("password")):
            return "true"
        elif check_password_hash(rows[0]["admin_password"], request.form.get("password")):
            return "true"
        else:
            return "fail"

@app.route("/email_ajax", methods=["POST"])
def email_ajax():
    if request.method == "POST":
        # Query database for username
        rows = db.execute("SELECT * FROM school WHERE email = :email",email=request.form.get("email"))
        # Remember which user has logged in
        # Ensure username exists and password is correct
        if len(rows) < 1:
            return "fail"
        else:
            return "pass"

@app.route("/class_name", methods=["POST"])
def class_name():
    if request.method == "POST":
        tables = database(str(0))
        # Query database for username
        rows = db.execute("SELECT * FROM :session_data WHERE classname = :classname",session_data=tables["session_data"],classname=request.form.get("classname").lower())
        if len(rows) == 0:
            return "pass"
        else:
            return "fail"



@app.route("/createClass", methods=["GET", "POST"])
@login_required
def createClass():
    tables = database(str(0))
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        schoolrow = db.execute("SELECT * FROM school WHERE id = :schoolId", schoolId = session["user_id"])
        # Ensure schoolname was submitted
        if not request.form.get("class_name"):
            error = "Provide a class name"
            return render_template("createClassForm.html", error=error, schoolInfo=schoolrow)
        row = db.execute("SELECT * FROM :session_data WHERE classname = :class_name",session_data=tables["session_data"], class_name = request.form.get("class_name").lower() )
        if len(row) > 0:
            error = "class already exist"
            return render_template("createClassForm.html", error=error, schoolInfo=schoolrow)
        if not request.form.get("section"):
            error = "Provide your section"
            return render_template("createClassForm.html", error=error, schoolInfo=schoolrow)
        if not request.form.get("firstname"):
            error = "Provide your firstname"
            return render_template("createClassForm.html", error=error, schoolInfo=schoolrow)
        if not request.form.get("surname"):
            error = "Provide your surname"
            return render_template("createClassForm.html", error=error, schoolInfo=schoolrow)
        if not request.form.get("no_of_students"):
            error = "Provide the number of students in class"
            return render_template("createClassForm.html", error=error, schoolInfo=schoolrow)
        try:
            val = int(request.form.get("no_of_students"))
        except ValueError:
            error = "Provide a number for the students in class"
            return render_template("createClassForm.html", error=error, schoolInfo=schoolrow)
        if not request.form.get("ca"):
            error = "Provide the maximum ca score"
            return render_template("createClassForm.html", error=error, schoolInfo=schoolrow)
        if not request.form.get("test"):
            error = "Provide the maximum test score"
            return render_template("createClassForm.html", error=error, schoolInfo=schoolrow)
        if not request.form.get("exam"):
            error = "Provide the maximum exam score"
            return render_template("createClassForm.html", error=error, schoolInfo=schoolrow)
        try:
            val = int(request.form.get("ca"))
        except ValueError:
            error = "Provide a number for the class maximum ca"
            return render_template("createClassForm.html", error=error, schoolInfo=schoolrow)
        try:
            val = int(request.form.get("test"))
        except ValueError:
            error = "Provide a number for the class maximum test"
            return render_template("createClassForm.html", error=error, schoolInfo=schoolrow)
        try:
            val = int(request.form.get("exam"))
        except ValueError:
            error = "Provide a number for the class maximum exam"
            return render_template("createClassForm.html", error=error, schoolInfo=schoolrow)
        sum = int(request.form.get("ca"))+int(request.form.get("exam"))+int(request.form.get("test"))
        if sum != 100:
            error = "ca + exam + test must be equal to 100"
            return render_template("createClassForm.html", error=error)
        if not request.form.get("password"):
            error = "Provide a class password"
            return render_template("createClassForm.html", error=error)
        if not request.form.get("confirmation"):
            error = "Provide a password confirmation"
            return render_template("createClassForm.html", error=error)
        # Ensure password and confirmation match
        if (request.form.get("password") != request.form.get("confirmation")):
            error = "Provide a password is not equal to  confirmation"
            return render_template("createClassForm.html", error=error)
        info["surname"] = request.form.get("surname")
        info["firstname"] = request.form.get("firstname")
        info["othername"] = request.form.get("othername")
        info["className"] = request.form.get("class_name").upper()
        info["ca_max"] = request.form.get("ca")
        info["test_max"] = request.form.get("test")
        info["exam_max"] = request.form.get("exam")
        info["noOfStudents"] = request.form.get("no_of_students")
        info["password"] = request.form.get("password")
        info["section"] = request.form.get("section")
        schoolrow = db.execute("SELECT * FROM school WHERE id = :schoolId", schoolId = session["user_id"])
        return render_template("classListForm.html",n = int(request.form.get("no_of_students")), schoolInfo = schoolrow )
    else:
        schoolId = session['user_id']
        schoolrow = db.execute("SELECT * FROM school WHERE id = :schoolId", schoolId = schoolId)
        return render_template("createClassForm.html",schoolInfo = schoolrow)

@app.route("/confirm_classlist", methods=["POST"])
@login_required
def confirm_classlist():
    all_students.clear()
    #declare an array of dicts
    tables = database(str(0))
    rows = db.execute("SELECT * FROM school WHERE id = :school_id",school_id=session["user_id"])
    #fill classlist
    g = int(info["noOfStudents"])
    # each student will be an element of the array
    for i in range(g):
        surname = "s"+str(i)
        firstname = "f"+str(i)
        othername = "o"+str(i)
        sex = "g"+str(i)
        all_students.append((request.form.get(surname), request.form.get(firstname), request.form.get(othername), request.form.get(sex)))
    #return classlist.html
    return render_template("confirm_classlist.html",schoolInfo = rows, students= all_students )


@app.route("/classCreated", methods=["POST"])
@login_required
def classCreated():
    tables = database(str(0))
    rows = db.execute("SELECT * FROM school WHERE id = :school_id",school_id=session["user_id"])
    schoolClass = tables["classes"]
    identity = info["className"]+"_"+str(datetime.datetime.now())
    #insert class and identifer
    db.execute("INSERT INTO :classes (identifier) VALUES (:name_date)", classes = tables["classes"], name_date = identity)
    #select class id with the identifier
    classRow = db.execute("SELECT * FROM :classes WHERE identifier = :name_d",classes = tables["classes"], name_d = identity)
    classId = classRow[0]["id"]
    session_term =str(rows[0]["current_session"])+"_"+str(rows[0]["current_term"])
    db.execute("INSERT INTO :results (id, noOfStudents) values (:id, :no_of_students)",results = tables["class_term_data"],id = classId, no_of_students = info["noOfStudents"] )
    db.execute("INSERT INTO :sessions (id,:current_term) VALUES(:id, :term)", sessions = tables["sessions"], current_term = session_term,id = classId, term = session_term)
    db.execute("INSERT INTO :session_data (id,surname,firstname,othername, classname, password,section,ca, test, exam) values (:id,:surname,:firstname,:othername,:className,:password,:section,:ca,:test,:exam)",session_data = tables["session_data"],id = classId, surname =  info["surname"],firstname =  info["firstname"],othername =  info["othername"], className = info["className"].lower(),password = generate_password_hash(info["password"]),section=info["section"],ca=info["ca_max"], test=info["test_max"], exam=info["exam_max"])
    term_tables(classId)
    tables = database(classId)
    # fill classlist
    sort_names = sorted(all_students, key=itemgetter(0))
    for name in sort_names:
                db.execute("INSERT INTO :classtable (surname, firstname, othername,sex) VALUES (:surname, :firstname, :othername,:sex) ",classtable = tables["classlist"], surname = name[0].upper(),firstname = name[1].upper(),othername = name[2].upper(),sex=name[3])
                db.execute("INSERT INTO :catable DEFAULT VALUES ",catable = tables["ca"])
                db.execute("INSERT INTO :testtable DEFAULT VALUES ",testtable = tables["test"])
                db.execute("INSERT INTO :examtable DEFAULT VALUES ",examtable = tables["exam"])
                db.execute("INSERT INTO :mastersheet DEFAULT VALUES ",mastersheet = tables["mastersheet"])
                db.execute("INSERT INTO :subject_position DEFAULT VALUES",subject_position = tables["subject_position"])
                db.execute("INSERT INTO :grades DEFAULT VALUES ",grades = tables["grade"])

    classRows = db.execute("SELECT * FROM :session_data ",session_data = tables["session_data"])
    classRow = db.execute("SELECT * FROM :session_data WHERE id=:id ",session_data = tables["session_data"], id=classId )
    # send email to admin about subject scoresheet
    html = render_template('new_class.html',classInfo = classRow)
    subject = classRow[0]["classname"]+" created for  "+ classRow[0]["section"]+" section"
    try:
        send_email(rows[0]["email"], subject, html, 'classclass_term_dataest@gmail.com')
    except Exception as e:
        print(e)
    # return classlist.html
    return render_class(classId)

@app.route("/how_to_use", methods=["GET"])
def how_to_use():
        try:
            session["user_id"]
        except KeyError:
            return render_template("how_to_use.html")
        schoolrow = db.execute("SELECT * FROM school WHERE id = :schoolId", schoolId = session["user_id"])
        return render_template("how_to_use.html", schoolInfo = schoolrow )

@app.route("/about_us", methods=["GET"])
def about_us():
        try:
            session["user_id"]
        except KeyError:
            return render_template("about_us.html")
        schoolrow = db.execute("SELECT * FROM school WHERE id = :schoolId", schoolId = session["user_id"])
        return render_template("about_us.html", schoolInfo = schoolrow )

@app.route("/delete_school", methods=["POST"])
@login_required
def delete_school():
    #get school id
    school_id = request.form.get("id")
    session["user_id"] = school_id
    tables = database(str(0))
    #select classes
    classes = db.execute("SELECT * FROM :classes",classes = tables["classes"])
    #for each class in classes
    for klass in classes:
        #select sessions
        sessions_row = db.execute("SELECT * FROM :sessions WHERE id=:id",sessions = tables["sessions"], id = klass["id"])
        if len(sessions_row) > 0:
            #get values
            sessions = sessions_row[0].values()
            #for each term in sessions
            for term in sessions:
                if term != klass["id"] and term:
                    terms = str(term).split("_")
                    #get term
                    term = terms[1]
                    #get session
                    current_session = terms[0]
                    #change session
                    db.execute("UPDATE school SET current_session=:this_session, current_term = :current_term WHERE id=:id", this_session = current_session, current_term = term , id = school_id)
                    #call database
                    tables = database(klass["id"])
                    #call drop term_tables
                    drop_tables(klass["id"])
    # drop session_data
    db.execute("DROP TABLE :session_data", session_data = tables["session_data"])
    # drop session_data
    db.execute("DROP TABLE :class_term_data", class_term_data = tables["class_term_data"])

    # drop classes
    db.execute("DROP TABLE :classes", classes = tables["classes"])
    # drop sessions
    db.execute("DROP TABLE :sessions", sessions = tables["sessions"])
    session["user_id"] = 1
    # delete drow from schools
    db.execute("DELETE FROM school WHERE id = :schoolid", schoolid = school_id )
    # select all the schools
    all_schools = db.execute("SELECT * FROM school")
    # display them in admin portfolio
    return render_template("admin_page.html", schoolInfo = all_schools)

@app.route("/submit_score", methods =["POST","GET"])
@login_required
def submit_score():
    class_scores.clear()
    tables = database(str(0))

    if request.method == "POST":

	    if not request.form.get("subject_name"):
	        error = " provide the subject name"
	        classes = db.execute("SELECT * FROM :session_data", session_data = tables["session_data"])
	        schoolId = session['user_id']
	        schoolrow = db.execute("SELECT * FROM school WHERE id = :schoolId", schoolId = schoolId)
	        return render_template("submit_score_form.html",classes = classes, schoolInfo = schoolrow, error = error)

	    if not request.form.get("the_class"):
	        error = "select one class"
	        classes = db.execute("SELECT * FROM :session_data", session_data = tables["session_data"])
	        schoolId = session['user_id']
	        schoolrow = db.execute("SELECT * FROM school WHERE id = :schoolId", schoolId = schoolId, error = error)

	        return render_template("submit_score_form.html",classes = classes, schoolInfo = schoolrow)
	    tables = database(str(request.form.get("the_class")))
	    subject_row =db.execute("SELECT * FROM :subjects WHERE name =:subject_name", subjects = tables["subjects"], subject_name = request.form.get("subject_name").lower())

	    if len(subject_row) > 0:
	        error = "subject already have a scoresheet"
	        classes = db.execute("SELECT * FROM :session_data", session_data = tables["session_data"])
	        schoolId = session['user_id']
	        schoolrow = db.execute("SELECT * FROM school WHERE id = :schoolId", schoolId = schoolId)
	        return render_template("submit_score_form.html",classes = classes, schoolInfo = schoolrow, error = error)
	    if not request.form.get("subject_teacher"):
	        error = "provide your name"
	        classes = db.execute("SELECT * FROM :session_data", session_data = tables["session_data"])
	        schoolId = session['user_id']
	        schoolrow = db.execute("SELECT * FROM school WHERE id = :schoolId", schoolId = schoolId)
	        return render_template("submit_score_form.html",classes = classes, schoolInfo = schoolrow, error = error)
	    subject_info["subject"] = request.form.get("subject_name").lower()
	    subject_info["subject_teacher"] = request.form.get("subject_teacher")
	    class_id= int(request.form.get("the_class"))
	    tables = database(class_id)
	    subject_info["class_id"] = class_id
	    class_row = db.execute("select * from :classid where id = :current_class", classid = tables["classes"], current_class= tables["class_id"])
	    schoolrow = db.execute("SELECT * FROM school WHERE id = :schoolId", schoolId = session["user_id"])
	    session_setting = db.execute("SELECT * FROM :session_data WHERE id = :id", session_data = tables["session_data"], id = tables["class_id"]  )
	    class_names = db.execute("select * from :thelist ORDER BY surname", thelist = tables["classlist"])
	    return render_template("empty_scoresheet.html",schoolInfo = schoolrow, subject_info = subject_info,class_names = class_names ,classinfo = class_row[0], setting = session_setting)
    else:
	    tables = database(str(0))
	    classes = db.execute("SELECT * FROM :session_data", session_data = tables["session_data"])
	    schoolrow = db.execute("SELECT * FROM school WHERE id = :schoolId", schoolId = session["user_id"])
	    return render_template("submit_score_form.html",classes = classes, schoolInfo = schoolrow)

@app.route("/submitted", methods=["POST"])
@login_required
def submitted():
    tables = database(request.form.get("button"))
    db.execute("INSERT INTO :subjects (name, teachers_name) VALUES (:subject, :teacher) ",subjects = tables["subjects"], subject = subject_info["subject"], teacher=subject_info["subject_teacher"])
    subject_list = db.execute("SELECT * FROM :subject WHERE name=:subject_name", subject = tables["subjects"],subject_name = subject_info["subject"])
    db.execute("UPDATE :classresult SET noOfSubjects = noOfSubjects + 1 WHERE id= :class_id", classresult = tables["class_term_data"], class_id=tables["class_id"])
    subject_id = str(subject_list[0]["id"])
    db.execute("ALTER TABLE :cascore_table ADD COLUMN :subject TEXT ", cascore_table = tables["ca"], subject = subject_id)
    db.execute("ALTER TABLE :test_table ADD COLUMN :subject TEXT ", test_table = tables["test"], subject = subject_id)
    db.execute("ALTER TABLE :exam_table ADD COLUMN :subject TEXT ", exam_table = tables["exam"], subject = subject_id)
    db.execute("ALTER TABLE :grade_table ADD COLUMN :subject TEXT ", grade_table= tables["grade"], subject = subject_id)
    db.execute("ALTER TABLE :subject_p ADD COLUMN :subject TEXT", subject_p = tables["subject_position"], subject = subject_id)
    db.execute("ALTER TABLE :mastersheet ADD COLUMN :subject TEXT ", mastersheet = tables["mastersheet"], subject = subject_id)
    class_list_row = db.execute("SELECT * FROM :classlist", classlist = tables["classlist"])
    rows = db.execute("SELECT * FROM school WHERE id = :school_id ",school_id = session["user_id"])
    class_info = db.execute("SELECT * FROM :classresult WHERE id=:class_id", classresult = tables["class_term_data"], class_id = tables["class_id"])
    subject_total = 0
    term_failed = 0
    term_passed = 0
    for  student in class_scores:
        total_score = 0
        subject_list = db.execute("SELECT * FROM :subject WHERE name=:subject_name", subject = tables["subjects"],subject_name = subject_info["subject"])
        student_row = db.execute("SELECT * FROM :master WHERE id=:student_id", master=tables["mastersheet"],student_id=student[0])
        db.execute("UPDATE :catable SET :subject = :score WHERE id =:id", catable = tables["ca"], subject = subject_id,score =student[3], id = student[0])
        db.execute("UPDATE :testtable SET :subject = :score WHERE id =:id", testtable = tables["test"], subject = subject_id,score =student[4], id = student[0])
        db.execute("UPDATE :examtable SET :subject = :score WHERE id =:id", examtable = tables["exam"], subject = subject_id,score =student[5], id = student[0])
        if student[3]:
            total_score = total_score + int(student[3])
        if student[4]:
            total_score = total_score + int(student[4])
        if student[5]:
            total_score = total_score + int(student[5])

        db.execute("UPDATE :master SET :subject = :score WHERE id =:id", master = tables["mastersheet"], subject = subject_id,score =total_score, id = student[0])

        if int(total_score) < 40:
            db.execute("UPDATE :master SET subject_failed = :value WHERE id=:id", master = tables["mastersheet"], value = int(student_row[0]["subject_failed"])+1, id = student[0])
            db.execute("UPDATE :subject SET no_failed = :value WHERE id=:id", subject = tables["subjects"], value = int(subject_list[0]["no_failed"])+1, id = subject_id)
        else:
            db.execute("UPDATE :master SET subject_passed = :value WHERE id=:id", master = tables["mastersheet"], value = int(student_row[0]["subject_passed"])+1, id = student[0])
            db.execute("UPDATE :subject SET no_passed = :value WHERE id=:id", subject = tables["subjects"], value = int(subject_list[0]["no_passed"])+1, id = subject_id)

        no_of_grade = db.execute("SELECT * FROM :grade WHERE id=:student_id", grade=tables["grade"],student_id=student[0])
        new_total = student_row[0]["total_score"] + total_score
        student_grade = grade(total_score)
        subject_total = subject_total + total_score
        grade_col = "no_of_"+str(student_grade[0]).upper()
        new_average = new_total / class_info[0]["noOfSubjects"]
        if int(new_average) > 40:
            term_passed = term_passed + 1
        else:
            term_failed = term_failed + 1

        db.execute("UPDATE :master SET total_score=:n_total WHERE id=:student_id", master = tables["mastersheet"], n_total = new_total, student_id = student[0])
        db.execute("UPDATE :master SET average = :n_average WHERE id=:student_id ", master = tables["mastersheet"],  n_average =new_average, student_id = student[0])
        db.execute("UPDATE :grades SET :subject = :subject_grade WHERE id =:id", grades = tables["grade"], subject = subject_id,subject_grade = grade(total_score), id = student[0])
        db.execute("UPDATE :grade_table SET :no_of_g = :value  WHERE id =:id", grade_table = tables["grade"], no_of_g = grade_col,value = int(no_of_grade[0][str(grade_col)]) + 1, id = student[0])
        db.execute("UPDATE :subject_table SET :no_of_g = :no_subject  WHERE id =:id", subject_table = tables["subjects"], no_of_g = grade_col, no_subject = int(subject_list[0][grade_col]+1), id = subject_id)
    #sort students position
    assign_student_position(int(tables["class_id"]))
    db.execute("UPDATE :result SET no_of_passes = :new_passes  WHERE id =:id", result = tables["class_term_data"],new_passes = term_passed, id = tables["class_id"])
    db.execute("UPDATE :result SET no_of_failures = :new_fails  WHERE id =:id", result = tables["class_term_data"],new_fails = term_failed, id = tables["class_id"])

    classRows = db.execute("SELECT * FROM :session_data WHERE id=:id ",session_data = tables["session_data"], id =tables["class_id"])
    #sort subject position
    assign_subject_position(int(tables["class_id"]),subject_id)
    class_result = db.execute("SELECT * FROM :results WHERE id=:id", results = tables["class_term_data"], id = tables["class_id"])
    no_of_students = class_result[0]["noOfStudents"]
    subject_average = subject_total / no_of_students
    db.execute("UPDATE :subject SET class_average = :n_average WHERE id=:id ", subject = tables["subjects"],  n_average =subject_average, id = subject_id)
    db.execute("UPDATE :subject SET total_score = :total WHERE id=:id ", subject = tables["subjects"],  total =subject_total, id = subject_id)
    # calculate and insert ppass for subject and class and repair passed and failed for class 
    initial_array = str(subject_info["subject_teacher"]).split()
    teacher_initials = ""
    for name in initial_array:
        if teacher_initials == "":
            teacher_initials = initials(name)
        else:
            teacher_initials = teacher_initials+initials(name)
    db.execute("UPDATE :subject SET teachers_initial = :abbr WHERE id=:id ", subject = tables["subjects"],  abbr =teacher_initials, id = subject_id)
    # send email to admin about subject scoresheet
    html = render_template('new_score.html',subject = subject_info, class_info=classRows[0])
    subject = subject_info["subject"]+" scoreesheet submitted for  "+ classRows[0]["classname"]
    try:
        send_email(rows[0]["email"], subject, html, 'classresultest@gmail.com')
    except Exception as e:
        print(e)
    classRows = db.execute("SELECT * FROM :session_data ",session_data = tables["session_data"])
    error = subject_info["subject"]+" scoresheet submitted successfully"
    # return classlist.html
    return render_class(tables["class_id"],error)

@app.route("/confirm_scoresheet", methods=["POST"])
@login_required
def confirm_scoresheet():
    #declare an array of
    class_scores.clear()
    tables = database(subject_info["class_id"])
    rows = db.execute("SELECT * FROM school WHERE id = :school_id",school_id=session["user_id"])
    class_list = db.execute("SELECT * FROM :classlist", classlist = tables["classlist"])
    # each student will be an element of the array
    for student  in class_list:
        ca = "cascore"+str(student["id"])
        test = "testscore"+str(student["id"])
        exam = "examscore"+str(student["id"])
        class_scores.append((student["id"], student["firstname"], student["surname"], request.form.get(ca), request.form.get(test), request.form.get(exam)))
    #return classlist.html
    return render_template("confirm_scoresheet.html",schoolInfo = rows, students=class_scores, class_id = subject_info["class_id"])


@app.route("/veiwclass", methods=["post", "get"])
@login_required
def veiwclass():
    return render_class(request.form.get("veiw_class"))


@app.route("/scoresheet", methods=["POST"])
@login_required
def scoresheet():
    array_id = str(request.form.get("scoresheet")).split("_")
    subject_id = int(array_id[0])
    class_id = int(array_id[1])
    tables=database(class_id)
    student_row = db.execute("SELECT * FROM :classlist", classlist=tables["classlist"])
    classrow = db.execute("SELECT * FROM :session_data WHERE id = :classId", session_data = tables["session_data"], classId = tables["class_id"])
    schoolrow = db.execute("SELECT * FROM school WHERE id = :schoolId", schoolId = session["user_id"])
    carow = db.execute("SELECT * FROM :catable",catable = tables["ca"])
    testrow = db.execute("SELECT * FROM :testtable",testtable = tables["test"])
    examrow = db.execute("SELECT * FROM :examtable",examtable = tables["exam"])
    subjectrow = db.execute("SELECT * FROM :subjecttable WHERE id=:id",subjecttable = tables["subjects"], id=subject_id)
    classlistrow = db.execute("SELECT * FROM :classlist",classlist = tables["classlist"])
    mastersheet_rows = db.execute("SELECT * FROM :mastersheet", mastersheet = tables["mastersheet"])
    subject_position_row = db.execute("SELECT * FROM :subject_position", subject_position = tables["subject_position"])
    results = db.execute("SELECT * FROM :result WHERE id=:id", result = tables["class_term_data"], id = tables["class_id"])
    return render_template("scoresheet.html",result = results[0],sub_id=subject_id, schoolInfo = schoolrow, classData = classrow, caData = carow, testData = testrow, examData = examrow, subjectData = subjectrow,class_list = classlistrow, mastersheet = mastersheet_rows, subject_position = subject_position_row)


@app.route("/result_sheet", methods=["POST"])
@login_required
def result_sheet():
    array_id = str(request.form.get("result_sheet")).split("_")
    student_id = int(array_id[0])
    class_id = int(array_id[1])
    tables= database(class_id)
    classrow = db.execute("SELECT * FROM :session_data WHERE id = :classId", session_data = tables["session_data"], classId = tables["class_id"])
    schoolrow = db.execute("SELECT * FROM school WHERE id = :schoolId", schoolId = tables["school_id"])
    carow = db.execute("SELECT * FROM :catable where id=:id",catable = tables["ca"], id= student_id)
    testrow = db.execute("SELECT * FROM :testtable where id=:id",testtable = tables["test"], id= student_id)
    examrow = db.execute("SELECT * FROM :examtable where id=:id",examtable = tables["exam"], id= student_id)
    subjectrow = db.execute("SELECT * FROM :subjecttable",subjecttable = tables["subjects"])
    grades = db.execute("SELECT * FROM :grade_s where id=:id ",grade_s = tables["grade"], id=student_id)
    classlistrow = db.execute("SELECT * FROM :classlist where id=:id",classlist = tables["classlist"], id=student_id)
    mastersheet_rows = db.execute("SELECT * FROM :mastersheet where id=:id", mastersheet = tables["mastersheet"], id= student_id)
    subject_position_row = db.execute("SELECT * FROM :subject_position where id=:id", subject_position = tables["subject_position"], id= student_id)
    results = db.execute("SELECT * FROM :result WHERE id=:id", result = tables["class_term_data"], id = tables["class_id"])
    return render_template("result_sheet.html",gradeRows = grades,result = results[0], schoolInfo = schoolrow, classData = classrow, caData = carow, testData = testrow, examData = examrow, subjectData = subjectrow,class_list = classlistrow, mastersheet = mastersheet_rows, subject_position = subject_position_row)


@app.route("/edit_scoresheet", methods=["POST"])
def edit_scoresheet():
    password = request.form.get("password")
    array_id = str(request.form.get("edit_scoresheet")).split("_")
    subject_id = int(array_id[0])
    class_id = int(array_id[1])
    tables= database(class_id)
    classrow = db.execute("SELECT * FROM :classes WHERE id = :classId", classes = tables["classes"], classId = tables["class_id"])
    schoolrow = db.execute("SELECT * FROM school WHERE id = :schoolId", schoolId = tables["school_id"])
    if check_password_hash(classrow[0]["password"], password) or check_password_hash(schoolrow[0]["admin_password"], password ):
        carow = db.execute("SELECT * FROM :catable",catable = tables["ca"])
        testrow = db.execute("SELECT * FROM :testtable",testtable = tables["test"])
        examrow = db.execute("SELECT * FROM :examtable",examtable = tables["exam"])
        subjectrow = db.execute("SELECT * FROM :subjecttable WHERE id=:id",subjecttable = tables["subjects"], id=subject_id)
        teachersrow = db.execute("SELECT * FROM :teacherstable",teacherstable = tables["teachers"])      
        classlistrow = db.execute("SELECT * FROM :classlist",classlist = tables["classlist"])
        mastersheet_rows = db.execute("SELECT * FROM :mastersheet", mastersheet = tables["mastersheet"])
        subject_position_row = db.execute("SELECT * FROM :subject_position", subject_position = tables["subject_position"])
        return render_template("edit_scoresheet.html",sub_id=subject_id, schoolInfo = schoolrow, classData = classrow, caData = carow, testData = testrow, examData = examrow, subjectData = subjectrow, teachersData = teachersrow,class_list = classlistrow, mastersheet = mastersheet_rows, subject_position = subject_position_row)
    else:
        error = "admin or class password incorrect"
        return render_class(class_id, error)

        
@app.route("/edited_scoresheet", methods=["POST"])
def edited_scoresheet():
    array_id = str(request.form.get("edited_scoresheet")).split("_")
    subject_id = int(array_id[0])
    class_id = int(array_id[1])
    tables = database(class_id)
    classes = tables["classes"]
    class_list = tables["classlist"]
    cascore_table = tables["ca"]
    test_table = tables["test"]
    exam_table = tables["exam"]
    subject_position = tables["subject_position"]
    mastersheet = tables["mastersheet"]
    teachers_table = tables["teachers"]
    subject_table = tables["subjects"]
    class_list_row = db.execute("SELECT * FROM :classlist", classlist = class_list)
    subject_row = db.execute("SELECT * FROM :subjects WHERE id=:id", subjects=subject_table, id=subject_id)

    rows = db.execute("SELECT * FROM school WHERE id = :school_id ",school_id = session["user_id"])

    
    for  student in class_list_row:
        cascore = "cascore"+ str(student["id"])
        testscore = "testscore"+str(student["id"])
        examscore = "examscore"+str(student["id"])
        ca_score = request.form.get(cascore)
        test_score = request.form.get(testscore)
        exam_score = request.form.get(examscore)
        db.execute("UPDATE :catable SET :subject = :score WHERE id =:id", catable = cascore_table, subject = subject_row[0]["name"],score =ca_score, id = student["id"])
        db.execute("UPDATE :testtable SET :subject = :score WHERE id =:id", testtable = test_table, subject = subject_row[0]["name"],score =test_score, id = student["id"])
        db.execute("UPDATE :examtable SET :subject = :score WHERE id =:id", examtable = exam_table, subject = subject_row[0]["name"],score =exam_score, id = student["id"])
    
    return render_class(class_id)



@app.route("/delete_scoresheet", methods=["POST"])
def delete_scoresheet():
    array_id = str(request.form.get("delete_scoresheet")).split("_")
    subject_id = int(array_id[0])
    class_id = int(array_id[1])
    tables = database(class_id)
    classes = tables["classes"]
    class_list = tables["classlist"]
    cascore_table = tables["ca"]
    test_table = tables["test"]
    exam_table = tables["exam"]
    subject_position = tables["subject_position"]
    mastersheet = tables["mastersheet"]
    teachers_table = tables["teachers"]
    subject_table = tables["subjects"]
    class_list_row = db.execute("SELECT * FROM :classlist", classlist = class_list)
    
    subject_row = db.execute("SELECT * FROM :subjects WHERE id=:id", subjects=subject_table, id=subject_id)

    db.execute("ALTER TABLE :cascore DROP COLUMN   :subject_name", cascore=cascore_table, subject_name=subject_row[0]["name"])
    db.execute("ALTER TABLE :testscore DROP COLUMN :subject", testscore=test_table, subject=subject_row[0]["name"] )
    db.execute("ALTER TABLE :examscore DROP COLUMN :subject", examscore=exam_table, subject=subject_row[0]["name"] )
    db.execute("ALTER TABLE :mastersheet DROP COLUMN :subject", mastersheet=mastersheet, subject=subject_row[0]["name"] )
    db.execute("ALTER TABLE :subject_p DROP COLUMN :subject", subject_p=subject_position, subject=subject_row[0]["name"] )
    db.execute("DELETE FROM :teachers WHERE subject=:subject", teachers=teachers_table, subject=subject_row[0]["name"])
    db.execute("DELETE FROM :subject WHERE id=:id", subjects=subject_table, id=subject_row[0]["id"])
    db.execute("UPDATE :classes set no_of_subjects = no_of_subjects - 1 WHERE id=:id", classes=classes, id=class_id)
    
    return render_class(class_id)

@app.route("/verify_scoresheet", methods=["POST"])
def verify_scoresheet():
    array_id = str(request.form.get("edit_scoresheet")).split("_")
    subject_id = int(array_id[0])
    class_id = int(array_id[1])
    tables= database(class_id)
    classrow = db.execute("SELECT * FROM :classes WHERE id = :classId", classes = tables["classes"], classId = tables["class_id"])
    schoolrow = db.execute("SELECT * FROM school WHERE id = :schoolId", schoolId = tables["school_id"])
    subjectrow = db.execute("SELECT * FROM :subjecttable WHERE id=:id",subjecttable = tables["subjects"], id=subject_id)
    return render_template("verify_scoresheet.html",sub_id=subject_id,  classData = classrow, schoolInfo=schoolrow)
    
    
@app.route("/edit_student", methods=["POST"])
def edit_student():
    password = request.form.get("password")
    student_id = request.form.get("student_id")
    class_id = request.form.get("class_id")
    tables= database(class_id)
    classrow = db.execute("SELECT * FROM :classes WHERE id = :classId", classes = tables["session_data"], classId = tables["class_id"])
    schoolrow = db.execute("SELECT * FROM school WHERE id = :schoolId", schoolId = tables["school_id"])
    if check_password_hash(classrow[0]["password"], password) or check_password_hash(schoolrow[0]["admin_password"], password ):
        studentrow = db.execute("SELECT * FROM :classlist WHERE id=:id", classlist=tables["classlist"], id=student_id)
        return render_template("edit_student.html",id=student_id, schoolInfo = schoolrow, classData=classrow,student=studentrow[0])
    else:
        error= ' The admin or class password is incorrect.'
        return render_class(class_id, error)

@app.route("/edited_student", methods=["POST"])
def edited_student():
    student_id = request.form.get("student_id")
    class_id = request.form.get("class_id")
    tables= database(class_id)
    surname = "s"+str(student_id)
    if not request.form.get(surname):
        error= "provide surname"
        studentrow = db.execute("SELECT * FROM :classlist WHERE id=:id", classlist=tables["classlist"], id=student_id)
        flash(error,'success')
        return render_template("edit_student.html",id=student_id, schoolInfo = schoolrow, classData=classrow,student=studentrow[0])
    firstname = "f"+str(student_id)
    if not request.form.get(firstname):
        error= "provide firstname"
        studentrow = db.execute("SELECT * FROM :classlist WHERE id=:id", classlist=tables["classlist"], id=student_id)
        flash(error,'success')
        return render_template("edit_student.html",id=student_id, schoolInfo = schoolrow, classData=classrow,student=studentrow[0])
    othername = "o"+str(student_id)
    sex = "g"+str(student_id)
    db.execute("UPDATE :classlist SET surname = :surname, firstname=:firstname, othername=:othername, sex=:sex WHERE id =:student_id", classlist = tables["classlist"], surname = request.form.get(surname).upper(),firstname =request.form.get(firstname).upper(), othername = request.form.get(othername).upper(), sex=request.form.get(sex), student_id= student_id)
    rows = db.execute("SELECT * FROM school WHERE id = :school_id ",school_id = session["user_id"])
    classrows = db.execute("SELECT * FROM :classes ", classes = tables["session_data"])
    return render_class(class_id)

@app.route("/unregister_student", methods=["POST"])
def unregister_student():
    student_id = request.form.get("student_id")
    class_id = request.form.get("class_id")
    tables= database(class_id)
    remove_student(student_id, class_id)
    rows = db.execute("SELECT * FROM school WHERE id = :school_id ",school_id = session["user_id"])
    classrows = db.execute("SELECT * FROM :classes ", classes = tables["session_data"])
    error="student deleted successfully"
    return render_class(class_id,error)

@app.route("/verify_customize", methods=["POST"])
def verify_customize():
   class_id = request.form.get("class_id")
   tables= database(class_id)
   classrow = db.execute("SELECT * FROM :classes WHERE id = :classId", classes = tables["classes"], classId = tables["class_id"])
   schoolrow = db.execute("SELECT * FROM school WHERE id = :schoolId", schoolId = tables["school_id"])
   return render_template("verify_customize.html", classData = classrow, schoolInfo=schoolrow)

@app.route("/verified_customize", methods=["POST"])
def verified_customize():
    class_id = request.form.get("class_id")
    tables = database(class_id)
    password = request.form.get("password")
    schoolrow = db.execute("SELECT * FROM school WHERE id = :schoolId", schoolId = tables["school_id"])
    classRows = db.execute("SELECT * FROM :class_data WHERE id=:id ",class_data = tables["session_data"], id=class_id)
    class_info = db.execute("SELECT * FROM :classes WHERE id=:id",classes=tables["classes"], id=class_id)
    class_settings = db.execute("SELECT * FROM :settings WHERE id=:id",settings=tables["class_term_data"], id=class_id)

    #select all the subjects
    subject = db.execute("SELECT * FROM :class_subjects",class_subjects = tables["subjects"] )
    # return classlist.html
    if not password:
        error = "provide admin or class password"
        flash(error,'success')
        return render_template("verify_customize.html", classData = classrow, schoolInfo=schoolrow)

    if check_password_hash(classRows[0]["password"], password) or check_password_hash(schoolrow[0]["admin_password"], password):
        return render_template("customize.html", schoolInfo = schoolrow,classData=classRows,subjects = subject, classInfo=class_info[0], class_setting=class_settings[0])
    else:
        classrow = db.execute("SELECT * FROM :classes ", classes = tables["classes"])
        error = "admin or class password incorrect"
        return render_class(class_id, error)



@app.route("/verify_add_student", methods=["POST"])
def verify_add_student():
   class_id = request.form.get("class_id")
   tables= database(class_id)
   classrow = db.execute("SELECT * FROM :classes WHERE id = :classId", classes = tables["classes"], classId = tables["class_id"])
   schoolrow = db.execute("SELECT * FROM school WHERE id = :schoolId", schoolId = tables["school_id"])
   return render_template("verify_add_student.html", classData = classrow, schoolInfo=schoolrow)


@app.route("/verified_add_student", methods=["POST"])
def verified_add_student():
    class_id = request.form.get("class_id")
    tables = database(class_id)
    password = request.form.get("password")
    schoolrow = db.execute("SELECT * FROM school WHERE id = :schoolId", schoolId = tables["school_id"])
    classRows = db.execute("SELECT * FROM :class_data WHERE id=:id ",class_data = tables["session_data"], id=class_id)
    class_info = db.execute("SELECT * FROM :classes WHERE id=:id",classes=tables["classes"], id=class_id)
    #select all the subjects
    subject = db.execute("SELECT * FROM :class_subjects",class_subjects = tables["subjects"] )
    # return classlist.html
    if not password:
        error = "provide admin or class password"
        flash(error,'success')
        return render_template("verify_add_student.html", classData = classrow, schoolInfo=schoolrow)

    if check_password_hash(classRows[0]["password"], password) or check_password_hash(schoolrow[0]["admin_password"], password):
        return render_template("add_student.html", schoolInfo = schoolrow,clas=classRows,subjects = subject, classInfo=class_info[0])
    else:
        classrow = db.execute("SELECT * FROM :classes ", classes = tables["classes"])
        error = "admin or class password incorrect"
        return render_class(class_id, error)
 
@app.route("/confirm_details", methods=["POST"])
def confirm_details():
    single_details.clear()
    single_subject.clear()
    class_id = request.form.get("class_id")
    tables= database(class_id)
    class_session = db.execute("SELECT * FROM :class_s WHERE id=:id", class_s = tables["session_data"], id= class_id )
    single_details["class_id"] = class_id
    single_details["class_name"] = class_session[0]["classname"]
    if not request.form.get("surname"):
        error = "you must provide students surname"
        schoolrow = db.execute("SELECT * FROM school WHERE id = :schoolId", schoolId = tables["school_id"])
        classRows = db.execute("SELECT * FROM :class_data WHERE id=:id ",class_data = tables["session_data"], id=class_id)
        class_info = db.execute("SELECT * FROM :classes WHERE id=:id",classes=tables["classes"], id=class_id)
        #select all the subjects
        subject = db.execute("SELECT * FROM :class_subjects",class_subjects = tables["subjects"] )
        flash(error,'success')
        return render_template("add_student.html", schoolInfo = schoolrow,clas=classRows,subjects = subject, classInfo=class_info[0])


    if not request.form.get("firstname"):
        error = "you must provide students firstname"
        schoolrow = db.execute("SELECT * FROM school WHERE id = :schoolId", schoolId = tables["school_id"])
        classRows = db.execute("SELECT * FROM :class_data WHERE id=:id ",class_data = tables["session_data"], id=class_id)
        class_info = db.execute("SELECT * FROM :classes WHERE id=:id",classes=tables["classes"], id=class_id)
        #select all the subjects
        subject = db.execute("SELECT * FROM :class_subjects",class_subjects = tables["subjects"] )
        flash(error,'success')
        return render_template("add_student.html", schoolInfo = schoolrow,clas=classRows,subjects = subject, classInfo=class_info[0])
    single_details["surname"] = request.form.get("surname")
    single_details["firstname"] = request.form.get("firstname")
    single_details["othername"] = request.form.get("othername")
    single_details["sex"] = request.form.get("sex")
    class_subjects = db.execute("SELECT * FROM :subs", subs = tables["subjects"])
    for subject in class_subjects:
        sub = {}
        ca = "cascore"+str(subject["id"])
        test = "testscore"+str(subject["id"])
        exam = "examscore"+str(subject["id"])
        sub["name"] = subject["name"]
        sub["id"] = subject["id"]
        sub["ca"] = request.form.get(ca)
        sub["test"] = request.form.get(test)
        sub["exam"] = request.form.get(exam)
        single_subject.append(sub)
    rows = db.execute("SELECT * FROM school WHERE id = :school_id",school_id=tables["school_id"])
    
    # return classlist.html
    return render_template("confirm_single_scoresheet.html", schoolInfo = rows, subjects= class_subjects, details = single_details, student_subjects=single_subject)

@app.route("/student_added", methods=["POST"])
def student_added():
    class_id = single_details["class_id"]
    tables= database(class_id)
    db.execute("INSERT INTO :classlist (surname, firstname, othername, sex) VALUES (:surname, :firstname, :othername, :sex)", classlist=tables["classlist"], surname= single_details["surname"].upper(), firstname=single_details["firstname"].upper(), othername=single_details["othername"].upper(), sex=single_details["sex"])
    student_row = db.execute("SELECT * FROM :classlist WHERE surname=:surname AND firstname=:firstname AND othername = :othername", classlist=tables["classlist"], surname = single_details["surname"].upper() ,firstname=single_details["firstname"].upper(), othername=single_details["othername"].upper())
    student_id = student_row[-1]["id"]
    db.execute("INSERT INTO :catable (id) VALUES (:id) ",catable = tables["ca"], id=student_id)
    db.execute("INSERT INTO :testtable (id )VALUES (:id) ",testtable = tables["test"], id=student_id)
    db.execute("INSERT INTO :examtable (id ) VALUES (:id) ",examtable = tables["exam"], id=student_id)
    db.execute("INSERT INTO :mastersheet (id)  VALUES (:id )",mastersheet = tables["mastersheet"], id=student_id)
    db.execute("INSERT INTO :grades (id) VALUES (:id) ",grades = tables["grade"], id=student_id)
    db.execute("INSERT INTO :subject_position (id)   VALUES (:id) ",subject_position = tables["subject_position"], id=student_id )
    term_data = db.execute("SELECT * FROM :term_data WHERE id =:id", term_data = tables["class_term_data"], id=class_id)
    new = int(term_data[0]["noOfStudents"]) + 1
    db.execute("UPDATE :term_data SET noOfStudents = :no_of_students WHERE id=:id", term_data =tables["class_term_data"], no_of_students = new, id=class_id)
    for subject in single_subject:
        ntotal = 0
        db.execute("UPDATE :ca SET :col=:subject_score WHERE id=:id",ca = tables["ca"], col=str(subject["id"]), subject_score = subject["ca"],id=student_id)
        db.execute("UPDATE :test SET :col=:subject_score WHERE id=:id",test = tables["test"], col=str(subject["id"]), subject_score = subject["test"],id=student_id)
        db.execute("UPDATE :exam SET :col=:subject_score WHERE id=:id", exam = tables["exam"], col=str(subject["id"]), subject_score = subject["exam"],id=student_id )
        if subject["ca"]:
            ntotal = ntotal + int(subject["ca"])
        if subject["test"]:
            ntotal = ntotal + int(subject["test"])
        if subject["exam"]:
            ntotal = ntotal + int(subject["exam"])
        db.execute("UPDATE :mastersheet SET :col=:subject_score WHERE id=:id",mastersheet = tables["mastersheet"], col=str(subject["id"]), subject_score = ntotal, id=student_id)
        db.execute("UPDATE :grades SET :col=:subject_grade WHERE id=:id", grades = tables["grade"], col=str(subject["id"]), subject_grade = grade(ntotal),id=student_id )

    add_student(student_id, class_id)
    # return classlist.html
    return render_class(class_id)

@app.route("/edit_class", methods=["GET"])
def edit_class():
   class_id = str(request.args.get("class_id"))
   tables= database(class_id)
   classrow = db.execute("SELECT * FROM :classes WHERE id = :classId", classes = tables["session_data"], classId = class_id)
   schoolrow = db.execute("SELECT * FROM school WHERE id = :schoolId", schoolId = tables["school_id"])
   return render_template("verify_admin.html", classData = classrow, schoolInfo=schoolrow)


@app.route("/verified_admin", methods=["POST"])
def verified_admin():        
    class_id = request.form.get("class_id")
    password = request.form.get("password")
    tables= database(str(class_id))
    classrow = db.execute("SELECT * FROM :classes WHERE id = :classId", classes = tables["session_data"], classId = class_id)
    schoolrow = db.execute("SELECT * FROM school WHERE id = :schoolId", schoolId = tables["school_id"])
    if check_password_hash(schoolrow[0]["admin_password"], password ):
        return render_template("edit_class.html", schoolInfo = schoolrow, classData=classrow)
    else:
        return render_class(class_id)

@app.route("/edited_class", methods=["POST"])
def edited_class():
    class_id = request.form.get("id")
    tables= database(class_id)
    if  request.form.get("firstname") != " ":
        db.execute("UPDATE :classes set firstname=:firstname where id=:id", classes = tables["classes"], firstname=request.form.get("firstname").upper(), id = tables["class_id"])
    if(request.form.get("surname") != ""):
        db.execute("UPDATE :classes set surname=:surname where id=:id", classes = tables["classes"], surname=request.form.get("surname").upper(), id = tables["class_id"])
    if(request.form.get("othername") != ""):
        db.execute("UPDATE :classes set othername=:othername where id=:id", classes = tables["classes"], othername=request.form.get("othername").upper(), id = tables["class_id"])
    if(request.form.get("class_name") != ""):
        db.execute("UPDATE :classes set name=:name where id=:id", classes = tables["classes"], name=request.form.get("class_name").upper(), id = tables["class_id"])
    rows = db.execute("SELECT * FROM school WHERE id = :school_id ",school_id = session["user_id"])
    classrows = db.execute("SELECT * FROM :classes ", classes = tables["classes"])
    return render_template("portfolio.html", schoolInfo = rows, clas = classrows)

@app.route("/delete_class", methods=["POST"])
def delete_class():
    class_id = request.form.get("delete_class")
    tables= database(class_id)
    db.execute("DROP TABLE :cascore", cascore= tables["ca"])
    db.execute("DROP TABLE :test", test= tables["test"])
    db.execute("DROP TABLE :exam", exam= tables["exam"])
    db.execute("DROP TABLE :mastersheet", mastersheet= tables["mastersheet"])
    db.execute("DROP TABLE :subject_position", subject_position= tables["subject_position"])
    db.execute("DROP TABLE :class_term", class_term= tables["class_term_data"])
    db.execute("DROP TABLE :classlist", classlist= tables["classlist"])
    db.execute("DROP TABLE :teachers", teachers= tables["teachers"])
    db.execute("DROP TABLE :subjects", subjects= tables["subjects"])
    db.execute("DELETE  FROM :classes where id=:id", classes= tables["classes"], id=tables["class_id"])
    # db.execute("UPDATE schools set no_of_classes = no_of_classes - 1 where id=:id" id=tables["class_id"])
    rows = db.execute("SELECT * FROM school WHERE id = :school_id ",school_id = session["user_id"])
    classrows = db.execute("SELECT * FROM :classes ", classes = tables["classes"])
    return render_template("portfolio.html", schoolInfo = rows, clas = classrows)

@app.route("/verify_edit_student", methods=["GET"])
def verify_edit_student():
   class_id = request.args.get("class_id")
   student_id = request.args.get("student_id")
   tables= database(class_id)
   classrow = db.execute("SELECT * FROM :classes WHERE id = :classId", classes = tables["classes"], classId = tables["class_id"])
   schoolrow = db.execute("SELECT * FROM school WHERE id = :schoolId", schoolId = tables["school_id"])
   return render_template("verify_teacher.html", classData = classrow, schoolInfo=schoolrow, id = student_id)

@app.route("/mastersheet", methods=["POST"])
@login_required
def mastersheet():
    class_id = request.form.get("class_id")
    tables = database(class_id)
    classrow = db.execute("SELECT * FROM :session_data WHERE id = :classId", session_data = tables["session_data"], classId = tables["class_id"])
    schoolrow = db.execute("SELECT * FROM school WHERE id = :schoolId", schoolId = session["user_id"])
    subjectrow = db.execute("SELECT * FROM :subjecttable",subjecttable = tables["subjects"])
    classlistrow = db.execute("SELECT * FROM :classlist",classlist = tables["classlist"])
    carow = db.execute("SELECT * FROM :ca",ca = tables["ca"])
    testrow = db.execute("SELECT * FROM :te",te = tables["test"])
    examrow = db.execute("SELECT * FROM :ex",ex = tables["exam"])
    mastersheet_rows = db.execute("SELECT * FROM :master", master= tables["mastersheet"])
    subject_p = db.execute("SELECT * FROM :subjectposition", subjectposition = tables["subject_position"])
    results = db.execute("SELECT * FROM :result WHERE id=:id", result = tables["class_term_data"], id = tables["class_id"])
    return render_template("mastersheet.html",result = results[0], caData = carow, testData = testrow, examData = examrow, classData = classrow, schoolInfo = schoolrow, subjectData=subjectrow,class_list = classlistrow, mastersheet = mastersheet_rows, subject_position= subject_p)


@app.route("/customize", methods=["POST"])
@login_required
def customize():
    class_id = request.form.get("class_id")
    tables = database(class_id)
    current_settings = db.execute("SELECT * FROM :settings WHERE id = :id", settings = tables["class_term_data"], id=class_id)
    setting = current_settings[0]
    if  request.form.get("background_color") != setting["background_color"] :
        db.execute("UPDATE :settings SET background_color = :background_color WHERE id=:id", settings= tables["class_term_data"], background_color = request.form.get("background_color"), id=class_id)
   
    if request.form.get("line_color") != setting["line_color"]:
        db.execute("UPDATE :settings SET line_color = :line_color WHERE id=:id", settings = tables["class_term_data"], line_color = request.form.get("line_color"), id=class_id)
    
    if request.form.get("text_color") and request.form.get("text_color") != setting["text_color"]:
        db.execute("UPDATE :settings SET text_color = :text_color WHERE id=:id" , settings = tables["class_term_data"], text_color = request.form.get("text_color"), id=class_id)

    if request.form.get("background_font") and request.form.get("background_font") != setting["background_font"]:
        db.execute("UPDATE :settings SET background_font = :background_font WHERE id=:id", settings = tables["class_term_data"], background_font = request.form.get("background_font"), id=class_id)
    
    if request.form.get("ld_position") and request.form.get("ld_position") != setting["ld_position"]:
        db.execute("UPDATE :settings SET ld_position = :ld_position WHERE id=:id", settings = tables["class_term_data"], ld_position = request.form.get("ld_position"), id=class_id)

    if request.form.get("l_font") and request.form.get("l_font") != setting["l_font"]:
        db.execute("UPDATE :settings SET l_font = :ld_font WHERE id=:id", settings = tables["class_term_data"], ld_font = request.form.get("l_font"), id=class_id)

    if request.form.get("l_color") and request.form.get("l_color") != setting["l_color"]:
        db.execute("UPDATE :settings SET l_color = :ld_color WHERE id=:id", settings = tables["class_term_data"], ld_color = request.form.get("l_color"), id=class_id)
   
    if request.form.get("l_font-size") and request.form.get("l_font-size") != setting["l_fontsize"]:
        db.execute("UPDATE :settings SET l_fontsize = :l_fontsize WHERE id=:id", settings = tables["class_term_data"], l_fontsize = request.form.get("l_font-size"), id=class_id)
 
    if request.form.get("l_weight") and request.form.get("l_weight") != setting["l_weight"]:
        db.execute("UPDATE :settings SET l_weight = :l_weight WHERE id=:id", settings = tables["class_term_data"], l_weight = request.form.get("l_weight"), id=class_id)

    if request.form.get("sd_font") and request.form.get("sd_font") != setting["sd_font"]:
        db.execute("UPDATE :settings SET sd_font = :sd_font WHERE id=:id", settings = tables["class_term_data"], sd_font = request.form.get("sd_font"), id=class_id)

    if request.form.get("sd_color") and request.form.get("sd_color") != setting["sd_color"]:
        db.execute("UPDATE :settings SET sd_color = :sd_color WHERE id=:id", settings = tables["class_term_data"], sd_color = request.form.get("sd_color"), id=class_id)
   
    if request.form.get("sd_fontsize") and request.form.get("sd_fontsize") != setting["sd_fontsize"]:
        db.execute("UPDATE :settings SET sd_fontsize = :sd_fontsize WHERE id=:id", settings = tables["class_term_data"], sd_fontsize = request.form.get("sd_fontsize"), id=class_id)

    if request.form.get("sd_position") and request.form.get("sd_position") != setting["sd_position"]:
        db.execute("UPDATE :settings SET sd_position = :sd_position WHERE id=:id", settings = tables["class_term_data"], sd_position = request.form.get("sd_position"), id=class_id)

    if  request.form.get("sd_email") != setting["sd_email"] and request.form.get("sd_email") != 'None':
        db.execute("UPDATE :settings SET sd_email = :sd_email WHERE id=:id", settings = tables["class_term_data"], sd_email = request.form.get("sd_email"), id=class_id)
    
    if request.form.get("admin_email") != setting["admin_email"]:
        if request.form.get("admin_email") == 'on':
            db.execute("UPDATE :settings SET admin_email = :admin_email WHERE id=:id", settings = tables["class_term_data"], admin_email = 'on', id=class_id)
        else:
            db.execute("UPDATE :settings SET admin_email = :admin_email WHERE id=:id", settings = tables["class_term_data"], admin_email = 'off', id=class_id)

    if  request.form.get("address") != setting["address"] and request.form.get("address") != 'None' :
        db.execute("UPDATE :settings SET address = :address WHERE id=:id", settings = tables["class_term_data"], address = request.form.get("address"), id=class_id)
   
    if  request.form.get("po_box") != setting["po_box"] and request.form.get("po_box") != 'None':
        db.execute("UPDATE :settings SET po_box = :po_box WHERE id=:id", settings = tables["class_term_data"], po_box = request.form.get("po_box"), id=class_id)

    if  request.form.get("phone") != setting["phone"] and request.form.get("phone") != 'None':
        db.execute("UPDATE :settings SET phone = :phone WHERE id=:id", settings = tables["class_term_data"], phone = request.form.get("phone"), id=class_id)
    
    if  request.form.get("sd_other") != setting["sd_other"] and request.form.get("sd_other") != 'None':
        db.execute("UPDATE :settings SET sd_other = :sd_other WHERE id=:id", settings = tables["class_term_data"], sd_other = request.form.get("sd_other"), id=class_id)

    if  request.form.get("next_term") != setting["next_term"] and request.form.get("next_term") != 'None' :
        db.execute("UPDATE :settings SET next_term = :next_term WHERE id=:id", settings = tables["class_term_data"], next_term = request.form.get("next_term"), id=class_id)
  
    if  request.form.get("address") != setting["address"] and request.form.get("address") != 'None' :
        db.execute("UPDATE :settings SET address = :address WHERE id=:id", settings = tables["class_term_data"], address = request.form.get("address"), id=class_id)

    if request.form.get("std_font") and request.form.get("std_font") != setting["std_font"]:
        db.execute("UPDATE :settings SET std_font = :std_font WHERE id=:id", settings = tables["class_term_data"], std_font = request.form.get("std_font"), id=class_id)

    if request.form.get("std_color") and request.form.get("std_color") != setting["std_color"]:
        db.execute("UPDATE :settings SET std_color = :std_color WHERE id=:id", settings = tables["class_term_data"], std_color = request.form.get("std_color"), id=class_id)
   
    if request.form.get("std_fontsize") and request.form.get("std_fontsize") != setting["std_fontsize"]:
        db.execute("UPDATE :settings SET std_fontsize = :std_fontsize WHERE id=:id", settings = tables["class_term_data"], std_fontsize = request.form.get("std_fontsize"), id=class_id)

    if request.form.get("std_position") and request.form.get("std_position") != setting["std_position"]:
        db.execute("UPDATE :settings SET std_position = :std_position WHERE id=:id", settings = tables["class_term_data"], std_position = request.form.get("std_position"), id=class_id)

    if request.form.get("table_type") and request.form.get("table_type") != setting["table_type"]:
        db.execute("UPDATE :settings SET table_type = :table WHERE id=:id", settings = tables["class_term_data"], table = request.form.get("table_type"), id=class_id)

    if  request.form.get("ca") != setting["ca"]:
        if request.form.get("ca"):
            db.execute("UPDATE :settings SET ca = :ca WHERE id=:id", settings = tables["class_term_data"], ca = 'on', id=class_id)
        else :
            db.execute("UPDATE :settings SET ca = :ca WHERE id=:id", settings = tables["class_term_data"], ca = 'off', id=class_id)


    if  request.form.get("test") != setting["test"]:
        if request.form.get("test"):
            db.execute("UPDATE :settings SET test = :test WHERE id=:id", settings = tables["class_term_data"], test ='on', id=class_id)
        else:
            db.execute("UPDATE :settings SET test = :test WHERE id=:id", settings = tables["class_term_data"], test = 'off', id=class_id)

  
    if  request.form.get("combined") != setting["combined"]:
        if request.form.get("combined"):
            db.execute("UPDATE :settings SET combined = :combined WHERE id=:id", settings = tables["class_term_data"], combined = 'on', id=class_id)
        else:
            db.execute("UPDATE :settings SET combined = :combined WHERE id=:id", settings = tables["class_term_data"], combined = 'off', id=class_id)

    if  request.form.get("exam") != setting["exam"]:
        if request.form.get("exam"):
            db.execute("UPDATE :settings SET exam = :exam WHERE id=:id", settings = tables["class_term_data"], exam = 'on', id=class_id)
        else :
            db.execute("UPDATE :settings SET exam = :exam WHERE id=:id", settings = tables["class_term_data"], exam = 'off', id=class_id)
   
    if  request.form.get("subject_total") != setting["subject_total"]:
        if request.form.get("subject_total"):
            db.execute("UPDATE :settings SET subject_total = :subject_total WHERE id=:id", settings = tables["class_term_data"], subject_total = 'on', id=class_id)
        else :
            db.execute("UPDATE :settings SET subject_total = :subject_total WHERE id=:id", settings = tables["class_term_data"], subject_total = 'off', id=class_id)
    
    if  request.form.get("subject_comment") != setting["subject_comment"]:
        if request.form.get("subject_comment"):
            db.execute("UPDATE :settings SET subject_comment = :subject_comment WHERE id=:id", settings = tables["class_term_data"], subject_comment = 'on', id=class_id)
        else :
            db.execute("UPDATE :settings SET subject_comment = :subject_comment WHERE id=:id", settings = tables["class_term_data"], subject_comment = 'off', id=class_id)

    if request.form.get("class_average") != setting["class_average"]:
        if request.form.get("class_average"):
            db.execute("UPDATE :settings SET class_average = :class_average WHERE id=:id", settings = tables["class_term_data"], class_average = 'on', id=class_id)
        else :
            db.execute("UPDATE :settings SET class_average = :class_average WHERE id=:id", settings = tables["class_term_data"], class_average = 'off', id=class_id)

    if request.form.get("grade") != setting["grade"]:
        if request.form.get("grade"): 
            db.execute("UPDATE :settings SET grade = :grade WHERE id=:id", settings = tables["class_term_data"], grade = 'on', id=class_id)
        else :
            db.execute("UPDATE :settings SET grade = :grade WHERE id=:id", settings = tables["class_term_data"], grade = 'off', id=class_id)
    
    if  request.form.get("teachers_initials") != setting["teachers_initials"]:
        if request.form.get("teachers_initials"): 
            db.execute("UPDATE :settings SET teachers_initials = :teachers_initials WHERE id=:id", settings = tables["class_term_data"], teachers_initials = 'on', id=class_id)
        else:
            db.execute("UPDATE :settings SET teachers_initials = :teachers_initials WHERE id=:id", settings = tables["class_term_data"], teachers_initials = 'off', id=class_id)

    if request.form.get("total_score") != setting["total_score"]:
        if request.form.get("total_score"):
            db.execute("UPDATE :settings SET total_score = :total_score WHERE id=:id", settings = tables["class_term_data"], total_score = 'on', id=class_id)
        else:
            db.execute("UPDATE :settings SET total_score = :total_score WHERE id=:id", settings = tables["class_term_data"], total_score = 'off', id=class_id)

    if request.form.get("average_score") != setting["average"]:
        if request.form.get("average_score"):
            db.execute("UPDATE :settings SET average = :average_score WHERE id=:id", settings = tables["class_term_data"], average_score = 'on', id=class_id)
        else:
            db.execute("UPDATE :settings SET average = :average_score WHERE id=:id", settings = tables["class_term_data"], average_score = 'off', id=class_id)

    if  request.form.get("position") != setting["position"]:
        if request.form.get("position"): 
            db.execute("UPDATE :settings SET position = :position WHERE id=:id", settings = tables["class_term_data"], position = 'on', id=class_id)
        else :
            db.execute("UPDATE :settings SET position = :position WHERE id=:id", settings = tables["class_term_data"], position = 'off', id=class_id)
    


    if  request.form.get("watermark") != setting["watermark"]:
        if request.form.get("watermark"):
            db.execute("UPDATE :settings SET watermark = :watermark WHERE id=:id", settings = tables["class_term_data"], watermark = 'on', id=class_id)
        else :
            db.execute("UPDATE :settings SET watermark = :watermark WHERE id=:id", settings = tables["class_term_data"], watermark = 'off', id=class_id)

    if  request.form.get("teachers_line") != setting["teachers_line"] and request.form.get("teachers_line") != 'None':
        db.execute("UPDATE :settings SET teachers_line = :teachers_line WHERE id=:id", settings = tables["class_term_data"], teachers_line = request.form.get("teachers_line"), id=class_id)
    

    if  request.form.get("principal_line") != setting["principal_line"] and request.form.get("principal_line") != 'None':
        db.execute("UPDATE :settings SET principal_line = :principal_line WHERE id=:id", settings = tables["class_term_data"], principal_line = request.form.get("principal_line"), id=class_id)

    if  request.form.get("teachers_signature") != setting["teachers_signature"]:
        if request.form.get("teachers_signature"):
            db.execute("UPDATE :settings SET teachers_signature = :teachers_signature WHERE id=:id", settings = tables["class_term_data"], teachers_signature = 'on', id=class_id)
        else:
            db.execute("UPDATE :settings SET teachers_signature = :teachers_signature WHERE id=:id", settings = tables["class_term_data"], teachers_signature = 'off', id=class_id)
   
    if request.form.get("principal_signature") != setting["principal_signature"]:
        if request.form.get("principal_signature"):
            db.execute("UPDATE :settings SET principal_signature = :principal_signature WHERE id=:id", settings = tables["class_term_data"], principal_signature = 'on', id=class_id)
        else:
            db.execute("UPDATE :settings SET principal_signature = :principal_signature WHERE id=:id", settings = tables["class_term_data"], principal_signature = 'off', id=class_id)

    if request.form.get("subject_position") != setting["subject_position"]:
        if request.form.get("subject_position"):
            db.execute("UPDATE :settings SET subject_position = :subject_position WHERE id=:id", settings = tables["class_term_data"], subject_position = 'on', id=class_id)
        else:
            db.execute("UPDATE :settings SET subject_position = :subject_position WHERE id=:id", settings = tables["class_term_data"], subject_position = 'off', id=class_id)

    if request.form.get("average_score") != setting["average"]:
        if request.form.get("average_score"):
            db.execute("UPDATE :settings SET average = :average_score WHERE id=:id", settings = tables["class_term_data"], average_score = 'on', id=class_id)
        else:
            db.execute("UPDATE :settings SET average = :average_score WHERE id=:id", settings = tables["class_term_data"], average_score = 'off', id=class_id)


    if request.form.get("pandf") != setting["pandf"]:
        if request.form.get("pandf"):
            db.execute("UPDATE :settings SET pandf = :pandf WHERE id=:id", settings = tables["class_term_data"], pandf = 'on', id=class_id)
        else:
            db.execute("UPDATE :settings SET pandf = :pandf WHERE id=:id", settings = tables["class_term_data"], pandf = 'off', id=class_id)

    if request.form.get("grade_summary") != setting["grade_summary"]:
        if request.form.get("pandf"):
            db.execute("UPDATE :settings SET grade_summary = :grade_summary WHERE id=:id", settings = tables["class_term_data"], grade_summary = 'on', id=class_id)
        else:
            db.execute("UPDATE :settings SET grade_summary = :grade_summary WHERE id=:id", settings = tables["class_term_data"], grade_summary = 'off', id=class_id)
    
    if request.form.get("shadow") != setting["shadow"]:
        if request.form.get("shadow") == 'on':
            db.execute("UPDATE :settings SET shadow = :shadow WHERE id=:id", settings = tables["class_term_data"], shadow = 'on', id=class_id)
        else:
            db.execute("UPDATE :settings SET shadow = :shadow WHERE id=:id", settings = tables["class_term_data"], shadow = 'off', id=class_id)


    return render_class(class_id, error ="setting updated successfully")