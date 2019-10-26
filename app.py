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

from functions import login_required, database, random_string_generator, render_portfolio, term_tables, drop_tables, grade, assign_student_position, assign_subject_position, passwordGen, initials, add_student, remove_student, render_class, render_portfolio, update_grade, session_term_check, new_term, new_session, generate_pins,check_confirmed

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


error = None



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
    #clear cookies
    try:
        session["user_id"]
    except KeyError:
        # Forget any user_id
        session.clear()

        # Redirect user to login form
        return render_template("/login.html")
    else:
        db.execute("UPDATE school SET token_id = :series, token = :token WHERE id=:id", series = "", token = "", id=session["user_id"])

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
        session['general_password'] = general_password
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
        db.execute("CREATE TABLE :setting ('id' INTEGER PRIMARY KEY NOT NULL, 'classname' TEXT, 'grading_type' INTEGER, 'comment_lines' INTEGER,'student_position' INTEGER DEFAULT 1, 'surname' TEXT, 'firstname' TEXT,'password' TEXT,'section' TEXT, 'ca' INTEGER, 'test' INTEGER,'exam' INTEGER)", setting = tables["session_data"])
        # create result data
        db.execute("CREATE TABLE :result ('id' INTEGER PRIMARY KEY  NOT NULL, 'noOfStudents' INTEGER DEFAULT 0,'noOfSubjects' INTEGER DEFAULT 0, 'no_of_passes' INTEGER DEFAULT 0, 'no_of_failures' INTEGER DEFAULT 0, 'grading_type' TEXT DEFAULT 'WAEC','background_color' TEXT DEFAULT 'white','text_color' TEXT DEFAULT 'black','line_color' TEXT DEFAULT 'black','background_font' TEXT DEFAULT 'Ariel','ld_position' TEXT DEFAULT 'center','l_font' TEXT DEFAULT 'Ariel Black','l_weight' TEXT DEFAULT '900','l_color' TEXT DEFAULT 'blue','l_fontsize' TEXT DEFAULT '30px','sd_font' TEXT DEFAULT 'Ariel','sd_color' TEXT DEFAULT '#808000','sd_fontsize' TEXT DEFAULT '20px','sd_position' TEXT DEFAULT 'center','sd_email' TEXT,'admin_email' TEXT DEFAULT 'off', 'address' TEXT,'po_box' TEXT,'phone' TEXT,'next_term' TEXT,'sd_other' TEXT,'std_color' TEXT DEFAULT 'black','std_font' TEXT DEFAULT 'Arial Narrow','std_fontsize' TEXT DEFAULT '18px','std_position' TEXT DEFAULT 'left','table_type' TEXT DEFAULT 'bordered','ca' TEXT DEFAULT 'on','test' TEXT DEFAULT 'on','exam' TEXT DEFAULT 'on','combined' TEXT DEFAULT 'on','subject_total' TEXT DEFAULT 'on','class_average' TEXT DEFAULT 'on','subject_position' TEXT DEFAULT 'on','grade' TEXT DEFAULT 'on','subject_comment' TEXT DEFAULT 'off','teachers_initials' TEXT DEFAULT 'on','total_score' TEXT DEFAULT 'on','average' TEXT DEFAULT 'on','position' TEXT DEFAULT 'on','teachers_line' INTEGER DEFAULT 0,'shadow' TEXT DEFAULT 'on','principal_line' INTEGER DEFAULT 0,'teachers_signature' TEXT DEFAULT 'off','principal_signature' TEXT DEFAULT 'off','pandf' TEXT DEFAULT 'on','grade_summary' TEXT DEFAULT 'on','watermark' TEXT DEFAULT 'on')",result = tables["class_term_data"])

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
@login_required
def unconfirmed():
    user = db.execute("SELECT * FROM school WHERE id=:id", id = session["user_id"])
    if user[0]["confirmed"] == "true":
        rows = db.execute("SELECT * FROM school WHERE id = :id",id = session["user_id"])
        return render_template("portfolio.html", schoolInfo = rows)
    rows = db.execute("SELECT * FROM school WHERE id = :id",id = session["user_id"])
    return render_template('unconfirmed.html', schoolInfo=rows)

@app.route("/resend_confirmation", methods=["GET", "POST"])
@login_required
def resend_confirmation():
    user = db.execute("SELECT * FROM school WHERE id=:id", id = session["user_id"])
    general_password = passwordGen()
    db.execute("UPDATE school SET password = :gen ", gen= generate_password_hash(general_password))
    token = generate_confirmation_token(user[0]["email"])
    confirm_url = url_for('confirm_email', token=token, _external=True)
    html = render_template('confirm_email.html', confirm_url=confirm_url, password=general_password)
    subject = "Please confirm your email"
    try:
        send_email(user[0]["email"], subject, html,'Schoolresultest@gmail.com')
    except Exception as e:
        print(e)
    flash('A new confirmation email has been sent.', 'success')
    return redirect('/unconfirmed')


@app.route("/subject_check", methods=["POST"])
@login_required
@check_confirmed
def subject_check():
    tables = database(int(request.form.get("class_id")))
    # Query database for username
    subject_row = db.execute("SELECT * FROM :subjects WHERE name =:subject_name", subjects = tables["subjects"], subject_name = str(request.form.get("subject_name")).lower())
    if len(subject_row) > 0:
        return "false"
    else:
        return "true"

@app.route("/subject_name_check", methods=["POST"])
@login_required
@check_confirmed
def subject_name_check():
    tables = database(int(request.form.get("class_id")))
    if request.form.get("previous") == request.form.get("subject_name"):
        return "true"
    else:
        # Query database for subject name
        subject_row = db.execute("SELECT * FROM :subjects WHERE name =:subject_name", subjects = tables["subjects"], subject_name = str(request.form.get("subject_name")).lower())
        if len(subject_row) > 0:
            return "false"
        else:
            return "true"



@app.route("/editclass_check", methods=["POST"])
@login_required
@check_confirmed
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
            flash(error)
            return render_template("change_password_form.html", error = error)
        rows = db.execute("SELECT * FROM school WHERE email = :email",email=request.form.get("email").lower())
        if len(rows) != 1:
            error = request.form.get("email")+" not associated with any registered account"
            flash(error)
            return render_template("change_password_form.html", error = error)
        token = generate_confirmation_token(request.form.get("email"))
        confirm_url = url_for('password_changed', token=token, _external=True)
        html = render_template('password.html', confirm_url=confirm_url)
        subject = "change password"
        try:
            send_email(request.form.get("email"), subject, html, 'Schoolresultest@gmail.com')
        except Exception as e:
            print(e)
        error = "follow the link sent to "+request.form.get("email") +" to change password"
        flash(error)
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
        flash(error)
        return render_template('login.html',error=error)
    else:
        token = request.args.get('token')
        email = confirm_token(token)
        if  not email:
            error = 'The  link is invalid or has expired.'
            flash(error)
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
@login_required
@check_confirmed
def class_name():
    if request.method == "POST":
        tables = database(str(0))
        class_name=request.form.get("classname").lower()
        old_name = request.form.get("oldname").lower()
        if class_name != old_name:
            row_class = db.execute("SELECT * FROM :classes WHERE classname = :check_name", classes = tables["session_data"], check_name = class_name)
            if len(row_class) < 1: 
                return jsonify(value="pass")
            else:
                return jsonify(value="fail")
        return jsonify(value="pass")

        

@app.route("/class_name_check", methods=["POST"])
@login_required
@check_confirmed
def class_name_check():
    if request.method == "POST":
        new_name = request.form.get("new_name")
        formerly = request.form.get("former")
        tables = database(str(0))
        if new_name != formerly:
            # Query database for username
            rows = db.execute("SELECT * FROM :session_data WHERE classname = :classname",session_data=tables["session_data"],classname=request.form.get("new_name").lower())
            if len(rows) == 0:
                return "pass"
            else:
                return "fail"
        else:
            return "pass"

@app.route("/createClass", methods=["GET", "POST"])
@login_required
@check_confirmed
def createClass():
    session["info"]={}
    tables = database(str(0))
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        schoolrow = db.execute("SELECT * FROM school WHERE id = :schoolId", schoolId = session["user_id"])
        # Ensure schoolname was submitted
        if not request.form.get("class_name"):
            error = "Provide a class name"
            return render_template("createClassForm.html", error=error, school=schoolrow)
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
            int(request.form.get("no_of_students"))
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
            int(request.form.get("ca"))
        except ValueError:
            error = "Provide a number for the class maximum ca"
            return render_template("createClassForm.html", error=error, schoolInfo=schoolrow)
        try:
            int(request.form.get("test"))
        except ValueError:
            error = "Provide a number for the class maximum test"
            return render_template("createClassForm.html", error=error, schoolInfo=schoolrow)
        try:
            int(request.form.get("exam"))
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
        if len(request.form.get("password")) < 6:
            error = "password should be at least 6 digit long"
            return render_template("createClassForm.html", error=error)
        if not request.form.get("confirmation"):
            error = "Provide a password confirmation"
            return render_template("createClassForm.html", error=error)
        # Ensure password and confirmation match
        if (request.form.get("password") != request.form.get("confirmation")):
            error = "Provide a password is not equal to  confirmation"
            return render_template("createClassForm.html", error=error)
        session["info"]["surname"] = request.form.get("surname")
        session["info"]["firstname"] = request.form.get("firstname")
        session["info"].update({"className":request.form.get("class_name").upper()})
        session["info"]["ca_max"] = request.form.get("ca")
        session["info"]["test_max"] = request.form.get("test")
        session["info"]["exam_max"] = request.form.get("exam")
        session["info"]["noOfStudents"] = request.form.get("no_of_students")
        session["info"]["password"] = request.form.get("password")
        session["info"]["section"] = request.form.get("section")
        schoolrow = db.execute("SELECT * FROM school WHERE id = :schoolId", schoolId = session["user_id"])
        return render_template("classListForm.html",n = int(request.form.get("no_of_students")), schoolInfo = schoolrow, class_name=session["info"]["className"] )
    else:
        schoolId = session['user_id']
        schoolrow = db.execute("SELECT * FROM school WHERE id = :schoolId", schoolId = schoolId)
        return render_template("createClassForm.html",schoolInfo = schoolrow)

@app.route("/confirm_classlist", methods=["POST"])
@check_confirmed
@login_required
def confirm_classlist():
    session["all_students"]=[]
    #declare an array of dicts
    rows = db.execute("SELECT * FROM school WHERE id = :school_id",school_id=session["user_id"])
    #fill classlist
    g = int(session["info"]["noOfStudents"])
    # each student will be an element of the array
    for i in range(g):
        surname = "s"+str(i)
        firstname = "f"+str(i)
        othername = "o"+str(i)
        sex = "g"+str(i)
        session["all_students"].append((request.form.get(surname), request.form.get(firstname), request.form.get(othername), request.form.get(sex)))
    #return classlist.html
    return render_template("confirm_classlist.html",schoolInfo = rows, students= session["all_students"], classinfo=session['info'])


@app.route("/classCreated", methods=["POST"])
@check_confirmed
@login_required
def classCreated():
    tables = database(str(0))
    rows = db.execute("SELECT * FROM school WHERE id = :school_id",school_id=session["user_id"])
    identity = session["info"]["className"]+"_"+str(datetime.datetime.now())
    #insert class and identifer
    db.execute("INSERT INTO :classes (identifier) VALUES (:name_date)", classes = tables["classes"], name_date = identity)
    #select class id with the identifier
    classRow = db.execute("SELECT * FROM :classes WHERE identifier = :name_d",classes = tables["classes"], name_d = identity)
    classId = classRow[0]["id"]
    session_term =str(rows[0]["current_session"])+"_"+str(rows[0]["current_term"])
    db.execute("INSERT INTO :results (id, noOfStudents) values (:id, :no_of_students)",results = tables["class_term_data"],id = classId, no_of_students = session["info"]["noOfStudents"] )
    db.execute("INSERT INTO :sessions (id,:current_term) VALUES(:id, :term)", sessions = tables["sessions"], current_term = session_term,id = classId, term = session_term)
    db.execute("INSERT INTO :session_data (id,surname,firstname,classname, password,section,ca, test, exam) values (:id,:surname,:firstname,:className,:password,:section,:ca,:test,:exam)",session_data = tables["session_data"],id = classId, surname =  session["info"]["surname"],firstname =  session["info"]["firstname"], className = session["info"]["className"].lower(),password = generate_password_hash(session["info"]["password"]),section=session["info"]["section"],ca=session["info"]["ca_max"], test=session["info"]["test_max"], exam=session["info"]["exam_max"])
    term_tables(classId)
    tables = database(classId)
    # fill classlist
    sort_names = sorted(session["all_students"], key=itemgetter(0))
    #generate pins
    pins = generate_pins(10,len(sort_names))
    # fill classlist
    i = 0
    for name in sort_names:
                db.execute("INSERT INTO :classtable (surname, firstname, othername,sex,pin) VALUES (:surname, :firstname, :othername,:sex,:pin) ",classtable = tables["classlist"], surname = name[0].upper(),firstname = name[1].upper(),othername = name[2].upper(),sex=name[3], pin=pins[i])
                db.execute("INSERT INTO :catable DEFAULT VALUES ",catable = tables["ca"])
                db.execute("INSERT INTO :testtable DEFAULT VALUES ",testtable = tables["test"])
                db.execute("INSERT INTO :examtable DEFAULT VALUES ",examtable = tables["exam"])
                db.execute("INSERT INTO :mastersheet DEFAULT VALUES ",mastersheet = tables["mastersheet"])
                db.execute("INSERT INTO :subject_position DEFAULT VALUES",subject_position = tables["subject_position"])
                db.execute("INSERT INTO :grades DEFAULT VALUES ",grades = tables["grade"])
                i = i + 1
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
@check_confirmed
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
@check_confirmed
def submit_score():
    session["subject_info"] = {}
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
	    session["subject_info"]["subject"] = request.form.get("subject_name").lower()
	    session["subject_info"]["subject_teacher"] = request.form.get("subject_teacher")
	    class_id= int(request.form.get("the_class"))
	    tables = database(class_id)
	    session["subject_info"]["class_id"] = class_id
	    class_row = db.execute("select * from :classid where id = :current_class", classid = tables["classes"], current_class= tables["class_id"])
	    schoolrow = db.execute("SELECT * FROM school WHERE id = :schoolId", schoolId = session["user_id"])
	    current_setting = db.execute("SELECT * FROM :settings WHERE id = :id", settings = tables["class_term_data"], id = tables["class_id"])
	    session_setting = db.execute("SELECT * FROM :session_data WHERE id = :id", session_data = tables["session_data"], id = tables["class_id"]  )
	    class_names = db.execute("select * from :thelist ORDER BY surname", thelist = tables["classlist"])
	    return render_template("empty_scoresheet.html",schoolInfo = schoolrow, subject_info = session["subject_info"],class_names = class_names ,classinfo = class_row[0], setting = session_setting, result = current_setting)
    else:
	    tables = database(str(0))
	    classes = db.execute("SELECT * FROM :session_data", session_data = tables["session_data"])
	    schoolrow = db.execute("SELECT * FROM school WHERE id = :schoolId", schoolId = session["user_id"])
	    return render_template("submit_score_form.html",classes = classes, schoolInfo = schoolrow)

@app.route("/confirm_scoresheet", methods=["POST"])
@login_required
@check_confirmed
def confirm_scoresheet():
    #declare an array of
    session["class_scores"] = []
    tables = database(session["subject_info"]["class_id"])
    rows = db.execute("SELECT * FROM school WHERE id = :school_id",school_id=session["user_id"])
    session_setting = db.execute("SELECT * FROM :session_data WHERE id = :id", session_data = tables["session_data"], id = tables["class_id"]  )
    class_list = db.execute("SELECT * FROM :classlist", classlist = tables["classlist"])
    # each student will be an element of the array
    for student  in class_list:
        ca = "cascore"+str(student["id"])
        test = "testscore"+str(student["id"])
        exam = "examscore"+str(student["id"])
        session["class_scores"].append((student["id"], student["firstname"], student["surname"], request.form.get(ca), request.form.get(test), request.form.get(exam)))
    #return classlist.html
    return render_template("confirm_scoresheet.html",schoolInfo = rows, students=session["class_scores"], class_id = session["subject_info"]["class_id"], details=session_setting, details2 = session["subject_info"])

@app.route("/submitted", methods=["POST"])
@login_required
@check_confirmed
def submitted():
    tables = database(request.form.get("button"))
    db.execute("INSERT INTO :subjects (name, teachers_name) VALUES (:subject, :teacher) ",subjects = tables["subjects"], subject = session["subject_info"]["subject"], teacher=session["subject_info"]["subject_teacher"])
    subject_list = db.execute("SELECT * FROM :subject WHERE name=:subject_name", subject = tables["subjects"],subject_name = session["subject_info"]["subject"])
    db.execute("UPDATE :Schoolresult SET noOfSubjects = noOfSubjects + 1 WHERE id= :class_id", Schoolresult = tables["class_term_data"], class_id=tables["class_id"])
    subject_id = str(subject_list[0]["id"])
    db.execute("ALTER TABLE :cascore_table ADD COLUMN :subject TEXT ", cascore_table = tables["ca"], subject = subject_id)
    db.execute("ALTER TABLE :test_table ADD COLUMN :subject TEXT ", test_table = tables["test"], subject = subject_id)
    db.execute("ALTER TABLE :exam_table ADD COLUMN :subject TEXT ", exam_table = tables["exam"], subject = subject_id)
    db.execute("ALTER TABLE :grade_table ADD COLUMN :subject TEXT ", grade_table= tables["grade"], subject = subject_id)
    db.execute("ALTER TABLE :subject_p ADD COLUMN :subject TEXT", subject_p = tables["subject_position"], subject = subject_id)
    db.execute("ALTER TABLE :mastersheet ADD COLUMN :subject TEXT ", mastersheet = tables["mastersheet"], subject = subject_id)
    rows = db.execute("SELECT * FROM school WHERE id = :school_id ",school_id = session["user_id"])
    class_info = db.execute("SELECT * FROM :Schoolresult WHERE id=:class_id", Schoolresult = tables["class_term_data"], class_id = tables["class_id"])
    subject_total = 0
    term_failed = 0
    term_passed = 0

    for  student in session["class_scores"]:
        subject_list = db.execute("SELECT * FROM :subject WHERE name=:subject_name", subject = tables["subjects"],subject_name = session["subject_info"]["subject"])
        student_row = db.execute("SELECT * FROM :master WHERE id=:student_id", master=tables["mastersheet"],student_id=student[0])
        no_of_grade = db.execute("SELECT * FROM :grade WHERE id=:student_id", grade=tables["grade"],student_id=student[0])
        total_score = 0
        if student[3]:
            total_score = total_score + int(student[3])
        if student[4]:
            total_score = total_score + int(student[4])
        if student[5]:
            total_score = total_score + int(student[5])

        new_total = student_row[0]["total_score"] + total_score
        student_grade = grade(total_score)
        subject_total = subject_total + total_score
        grade_col = "no_of_"+str(student_grade[0]).upper()
        new_average = new_total / class_info[0]["noOfSubjects"]
        if int(new_average) > 40:
            term_passed = term_passed + 1
        else:
            term_failed = term_failed + 1


        db.execute("UPDATE :catable SET :subject = :score WHERE id =:id", catable = tables["ca"], subject = subject_id,score =student[3], id = student[0])
        db.execute("UPDATE :testtable SET :subject = :score WHERE id =:id", testtable = tables["test"], subject = subject_id,score =student[4], id = student[0])
        db.execute("UPDATE :examtable SET :subject = :score WHERE id =:id", examtable = tables["exam"], subject = subject_id,score =student[5], id = student[0])


        if int(total_score) < 40:
            db.execute("UPDATE :master SET subject_failed = :value:subject = :score,total_score=:n_total,average = :n_average WHERE id=:id", master = tables["mastersheet"], value = int(student_row[0]["subject_failed"])+1, id = student[0],subject = subject_id,score =total_score, n_total = new_total,n_average =new_average)
            db.execute("UPDATE :subject SET no_failed = :value,:no_of_g = :no_subject WHERE id=:id", subject = tables["subjects"], value = int(subject_list[0]["no_failed"])+1, id = subject_id,no_of_g = grade_col, no_subject = int(subject_list[0][grade_col]+1))
        else:
            db.execute("UPDATE :master SET subject_passed = :value,:subject = :score,total_score=:n_total,average = :n_average  WHERE id=:id", master = tables["mastersheet"], value = int(student_row[0]["subject_passed"])+1, id = student[0],subject = subject_id,score =total_score, n_total = new_total,n_average =new_average)
            db.execute("UPDATE :subject SET no_passed = :value,:no_of_g = :no_subject WHERE id=:id", subject = tables["subjects"], value = int(subject_list[0]["no_passed"])+1, id = subject_id,no_of_g = grade_col, no_subject = int(subject_list[0][grade_col]+1))

        db.execute("UPDATE :grades SET :subject = :subject_grade,:no_of_g = :value WHERE id =:id", grades = tables["grade"], subject = subject_id,subject_grade = grade(total_score), id = student[0], no_of_g = grade_col,value = int(no_of_grade[0][str(grade_col)]) + 1)
    #sort students position
    assign_student_position(int(tables["class_id"]))
    db.execute("UPDATE :result SET no_of_passes = :new_passes,no_of_failures = :new_fails  WHERE id =:id",new_fails = term_failed, result = tables["class_term_data"],new_passes = term_passed, id = tables["class_id"])

    classRows = db.execute("SELECT * FROM :session_data WHERE id=:id ",session_data = tables["session_data"], id =tables["class_id"])
    #sort subject position
    assign_subject_position(int(tables["class_id"]),subject_id)
    no_of_students = class_info[0]["noOfStudents"]
    subject_average = subject_total / no_of_students
    # calculate and insert ppass for subject and class and repair passed and failed for class 
    initial_array = str(session["subject_info"]["subject_teacher"]).split()
    teacher_initials = ""
    for name in initial_array:
        if teacher_initials == "":
            teacher_initials = initials(name)
        else:
            teacher_initials = teacher_initials+initials(name)
    db.execute("UPDATE :subject SET class_average = :n_average,total_score = :total,teachers_initial = :abbr WHERE id=:id ",abbr =teacher_initials, total =subject_total,subject = tables["subjects"],  n_average =subject_average, id = subject_id)

    # send email to admin about subject scoresheet
    html = render_template('new_score.html',subject = session["subject_info"], class_info=classRows[0])
    subject = session["subject_info"]["subject"]+" scoreesheet submitted for  "+ classRows[0]["classname"]
    try:
        send_email(rows[0]["email"], subject, html, 'Schoolresultest@gmail.com')
    except Exception as e:
        print(e)
    classRows = db.execute("SELECT * FROM :session_data ",session_data = tables["session_data"])
    error = session["subject_info"]["subject"]+" scoresheet submitted successfully"
    # return classlist.html
    return render_class(tables["class_id"],error)




@app.route("/veiwclass", methods=["post", "get"])
@login_required
@check_confirmed
def veiwclass():
    return render_class(request.form.get("veiw_class"))


@app.route("/scoresheet", methods=["POST"])
@login_required
@check_confirmed
def scoresheet():
    array_id = str(request.form.get("scoresheet")).split("_")
    subject_id = int(array_id[0])
    class_id = int(array_id[1])
    tables=database(class_id)
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
@check_confirmed
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



        
@app.route("/edited_scoresheet", methods=["POST"])
@login_required
@check_confirmed
def edited_scoresheet():
    array_id = str(request.form.get("edited_scoresheet")).split("_")
    subject_id = int(array_id[0])
    class_id = int(array_id[1])
    tables = database(class_id)
    class_list = tables["classlist"]
    cascore_table = tables["ca"]
    test_table = tables["test"]
    exam_table = tables["exam"]
    subject_table = tables["subjects"]
    class_list_row = db.execute("SELECT * FROM :classlist", classlist = class_list)
    subject_row = db.execute("SELECT * FROM :subjects WHERE id=:id", subjects=subject_table, id=subject_id)

    rows = db.execute("SELECT * FROM school WHERE id = :school_id ",school_id = session["user_id"])
    class_info = db.execute("SELECT * FROM :Schoolresult WHERE id=:class_id", Schoolresult = tables["class_term_data"], class_id = tables["class_id"])
    subject_total = 0
    term_failed = 0
    term_passed = 0
    subject_list = db.execute("SELECT * FROM :subject WHERE id=:id", subject = tables["subjects"],id = subject_id)

    for  student in class_list_row:
        total_score = 0
        student_row = db.execute("SELECT * FROM :master WHERE id=:student_id", master=tables["mastersheet"],student_id=student["id"])
        ca_row = db.execute("SELECT * FROM :ca WHERE id=:student_id", ca=tables["ca"],student_id=student["id"])
        test_row = db.execute("SELECT * FROM :test WHERE id=:student_id", test=tables["test"],student_id=student["id"])
        exam_row = db.execute("SELECT * FROM :exam WHERE id=:student_id", exam=tables["exam"],student_id=student["id"])

        cascore = "cascore"+ str(student["id"])
        testscore = "testscore"+str(student["id"])
        examscore = "examscore"+str(student["id"])
        ca_score = request.form.get(cascore)
        test_score = request.form.get(testscore)
        exam_score = request.form.get(examscore)
        if  ca_score != ca_row[0][str(subject_id)] : 
            db.execute("UPDATE :catable SET :subject = :score WHERE id =:id", catable = cascore_table, subject = str(subject_row[0]["id"]),score =ca_score, id = student["id"])
        if  test_score != test_row[0][str(subject_id)] : 
            db.execute("UPDATE :testtable SET :subject = :score WHERE id =:id", testtable = test_table, subject = str(subject_row[0]["id"]),score =test_score, id = student["id"])
        if  exam_score != exam_row[0][str(subject_id)]: 
            db.execute("UPDATE :examtable SET :subject = :score WHERE id =:id", examtable = exam_table, subject = str(subject_row[0]["id"]),score =exam_score, id = student["id"])
        if ca_score:
            total_score = total_score + int(ca_score)
        if test_score:
            total_score = total_score + int(test_score)
        if exam_score:
            total_score = total_score + int(exam_score)
        subject_total = subject_total + total_score

        if int(total_score) !=  int(student_row[0][str(subject_id)]):
            db.execute("UPDATE :master SET :subject = :score WHERE id =:id", master = tables["mastersheet"], subject = str(subject_id),score =total_score, id = student["id"])
            if int(total_score) < 40 and int(student_row[0][str(subject_id)]) > 40:
                db.execute("UPDATE :master SET subject_failed = :value WHERE id=:id", master = tables["mastersheet"], value = int(student_row[0]["subject_failed"])+1, id = student["id"])
                db.execute("UPDATE :subject SET no_failed = :value WHERE id=:id", subject = tables["subjects"], value = int(subject_list[0]["no_failed"])+1, id = subject_id)
                db.execute("UPDATE :master SET subject_passed = :value WHERE id=:id", master = tables["mastersheet"], value = int(student_row[0]["subject_passed"])-1, id = student["id"])
                db.execute("UPDATE :subject SET no_passed = :value WHERE id=:id", subject = tables["subjects"], value = int(subject_list[0]["no_passed"])-1, id = subject_id)

            elif int(total_score) > 40 and int(student_row[0][str(subject_id)]) < 40:
                db.execute("UPDATE :master SET subject_passed = :value WHERE id=:id", master = tables["mastersheet"], value = int(student_row[0]["subject_passed"])+1, id = student["id"])
                db.execute("UPDATE :subject SET no_passed = :value WHERE id=:id", subject = tables["subjects"], value = int(subject_list[0]["no_passed"])+1, id = subject_id)
                db.execute("UPDATE :master SET subject_failed = :value WHERE id=:id", master = tables["mastersheet"], value = int(student_row[0]["subject_failed"])-1, id = student["id"])
                db.execute("UPDATE :subject SET no_failed = :value WHERE id=:id", subject = tables["subjects"], value = int(subject_list[0]["no_failed"])-1, id = subject_id)

            no_of_grade = db.execute("SELECT * FROM :grade WHERE id=:student_id", grade=tables["grade"],student_id=student["id"])
            new_total = int(student_row[0]["total_score"]) - int(student_row[0][str(subject_id)])
            new_total = new_total + total_score
            student_grade = grade(total_score, str(class_info[0]["grading_type"]))
            grade_col = "no_of_"+str(student_grade[0]).upper()
            new_average = new_total / class_info[0]["noOfSubjects"]
            # no of students that passed overall or failed, remember to edit old record instead changing it completely
            if float(new_average) > 40 and float(student_row[0]["average"]) < 40.0 :
                # increase number of students that passed
                db.execute("UPDATE :class_table SET no_of_passes = :new_passes where id = :id", class_table = tables["class_term_table"], new_passes = int(class_info[0]["no_of_passes"]) + 1, id = class_id )
                # reduce number of students that failed
                db.execute("UPDATE :class_table SET no_of_failures = :new_failures where id = :id", class_table = tables["class_term_table"], new_failures = int(class_info[0]["no_of_failures"]) - 1, id = class_id )
            elif float(new_average) < 40 and float(student_row[0]["average"]) > 40.0 :
                # increase number of students that passed
                db.execute("UPDATE :class_table SET no_of_passes = :new_passes where id = :id", class_table = tables["class_term_table"], new_passes = int(class_info[0]["no_of_passes"]) - 1, id = class_id )
                # reduce number of students that failed
                db.execute("UPDATE :class_table SET no_of_failures = :new_failures where id = :id", class_table = tables["class_term_table"], new_failures = int(class_info[0]["no_of_failures"]) + 1, id = class_id )

            db.execute("UPDATE :master SET total_score=:n_total WHERE id=:student_id", master = tables["mastersheet"], n_total = new_total, student_id = student["id"])
            db.execute("UPDATE :master SET average = :n_average WHERE id=:student_id ", master = tables["mastersheet"],  n_average =new_average, student_id = student["id"])
            db.execute("UPDATE :grades SET :subject = :subject_grade WHERE id =:id", grades = tables["grade"], subject = str(subject_id),subject_grade = grade(total_score), id = student["id"])
            db.execute("UPDATE :grade_table SET :no_of_g = :value  WHERE id =:id", grade_table = tables["grade"], no_of_g = grade_col,value = int(no_of_grade[0][str(grade_col)]) + 1, id = student["id"])
            db.execute("UPDATE :subject_table SET :no_of_g = :no_subject  WHERE id =:id", subject_table = tables["subjects"], no_of_g = grade_col, no_subject = int(subject_list[0][grade_col]+1), id = str(subject_id))
    #sort students position
    assign_student_position(int(tables["class_id"]))
    db.execute("UPDATE :result SET no_of_passes = :new_passes  WHERE id =:id", result = tables["class_term_data"],new_passes = term_passed, id = tables["class_id"])
    db.execute("UPDATE :result SET no_of_failures = :new_fails  WHERE id =:id", result = tables["class_term_data"],new_fails = term_failed, id = tables["class_id"])
    classRows = db.execute("SELECT * FROM :session_data WHERE id=:id ",session_data = tables["session_data"], id =tables["class_id"])
    #sort subject position
    assign_subject_position(int(tables["class_id"]),subject_id)
    class_result = db.execute("SELECT * FROM :results WHERE id=:id", results = tables["class_term_data"], id = tables["class_id"])
    if int(subject_list[0]["total_score"]) != subject_total:
        no_of_students = class_result[0]["noOfStudents"]
        subject_average = subject_total / no_of_students
        # calculate and insert ppass for subject and class and repair passed and failed for class 
        db.execute("UPDATE :subject SET class_average = :n_average WHERE id=:id ", subject = tables["subjects"],  n_average =subject_average, id = subject_id)
        db.execute("UPDATE :subject SET total_score = :total WHERE id=:id ", subject = tables["subjects"],  total =subject_total, id = subject_id)
    if subject_list[0]["name"] != request.form.get("subject_name"):
        db.execute("UPDATE :subject SET name = :subject_name WHERE id=:id ", subject = tables["subjects"],  subject_name =request.form.get("subject_name").upper(), id = subject_id)


    if subject_list[0]["teachers_name"] != request.form.get("teachers_name"):
        db.execute("UPDATE :subject SET teachers_name = :teacher WHERE id=:id ", subject = tables["subjects"],  teacher =request.form.get("teachers_name").upper(), id = subject_id)
        initial_array = str(request.form.get("teachers_name")).split()
        teacher_initials = ""
        for name in initial_array:
            if teacher_initials == "":
                teacher_initials = initials(name)
            else:
                teacher_initials = teacher_initials+initials(name)
        db.execute("UPDATE :subject SET teachers_initial = :abbr WHERE id=:id ", subject = tables["subjects"],  abbr =teacher_initials, id = subject_id)
    subject = request.form.get("subject_name")+" edited successfully"
    error = request.form.get("subject_name")+" scoresheet edited successfully"
    # send email to admin about subject scoresheet
    html = render_template('new_score.html',subject = session["subject_info"], class_info=classRows[0])
    try:
        send_email(rows[0]["email"], subject, html, 'Schoolresultest@gmail.com')
    except Exception as e:
        print(e)
    classRows = db.execute("SELECT * FROM :session_data ",session_data = tables["session_data"])
    # return classlist.html
    return render_class(tables["class_id"],error)


@app.route("/delete_scoresheet", methods=["POST"])
@login_required
@check_confirmed
def delete_scoresheet():
    class_id = str(request.form.get("class_id"))
    subject_id = str(request.form.get("subject_id"))
    tables = database(class_id)
    class_details = db.execute("SELECT * FROM :class_term WHERE id=:id", class_term = tables["class_term_data"], id=class_id)
    mastersheet = db.execute("SELECT * FROM :master", master = tables["mastersheet"])
    subject = db.execute("SELECT * FROM :subjects WHERE id=:id", subjects=tables["subjects"], id=subject_id)
    student_pass = 0
    student_fail = 0
    for student in mastersheet:
        students_total = int(student["total_score"])
        subject_total = int(student[subject_id])
        new_total= students_total - subject_total
        if (int(class_details[0]["noOfSubjects"])-1) != 0:
            new_average = new_total/(int(class_details[0]["noOfSubjects"])-1)
        else:
            new_average = 0
        if subject_total > 40:
            subject_passed = int(student["subject_passed"]) - 1
            db.execute("UPDATE :master SET subject_passed=:subject_p  WHERE id=:student_id",master = tables["mastersheet"], subject_p = subject_passed, student_id = student["id"])
        else:
            subject_failed = int(student["subject_failed"]) - 1
            db.execute("UPDATE :master SET subject_failed=:subject_f WHERE id=:student_id",master = tables["mastersheet"], subject_f = subject_failed, student_id = student["id"])

        if float(new_average) > 40.00:
            student_pass = student_pass + 1
        else:
            student_fail = student_fail + 1
        student_grade = grade(subject_total,class_details[0]["grading_type"])
        grade_col = "no_of_"+student_grade[0]
        grades = db.execute("SELECT * FROM :grades WHERE id =:id", grades = tables["grade"], id = student["id"])
        db.execute("UPDATE :grading SET :no_col = :col WHERE id = :id", grading = tables["grade"], no_col = grade_col, col = int(grades[0][grade_col])-1, id = student["id"])
        db.execute("UPDATE :master SET total_score=:new_t, average = :new_a  WHERE id=:student_id",master = tables["mastersheet"], new_t = new_total, new_a = new_average, student_id = student["id"])
    #db.execute("ALTER TABLE :cascore DROP :subject_name", cascore=tables["ca"], subject_name=str(subject_id))
    #db.execute("ALTER TABLE :testscore DROP  :subject", testscore=tables["test"], subject=subject_id )
    #db.execute("ALTER TABLE :examscore DROP  :subject", examscore=tables["exam"], subject=subject_id)
    #db.execute("ALTER TABLE :mastersheet DROP  :subject", mastersheet=tables["mastersheet"], subject=subject_id)
    #db.execute("ALTER TABLE :subject_p DROP  :subject", subject_p=tables["subject_position"], subject=subject_id )
    #db.execute("ALTER TABLE :grade DROP  :subject", grade=tables["grade"], subject=subject_id)
    db.execute("UPDATE :classes set noOfSubjects = :no_of_subjects, no_of_passes=:passes, no_of_failures=:fail WHERE id=:id", classes=tables["class_term_data"],no_of_subjects=int(class_details[0]["noOfSubjects"])-1,passes = student_pass, fail=student_fail, id=class_id)
    db.execute("DELETE  FROM :subject WHERE id=:id", subject=tables["subjects"], id=subject_id)
    assign_student_position(class_id)
    error=subject[0]["name"]+"deleted successfully"
    return render_class(tables["class_id"],error)


@app.route("/cancel", methods=["POST"])
@login_required
@check_confirmed

def cancel():
    class_id = str(request.form.get("class_id"))
    return render_class(class_id)


@app.route("/cancel_portfolio", methods=["POST"])
@login_required
@check_confirmed
def cancel_portfolio():
    return render_portfolio()

@app.route("/verify_scoresheet", methods=["POST"])
@login_required
@check_confirmed
def verify_scoresheet():
    array_id = str(request.form.get("edit_scoresheet")).split("_")
    subject_id = int(array_id[0])
    class_id = int(array_id[1])
    tables= database(class_id)
    classrow = db.execute("SELECT * FROM :classes WHERE id = :classId", classes = tables["classes"], classId = tables["class_id"])
    schoolrow = db.execute("SELECT * FROM school WHERE id = :schoolId", schoolId = tables["school_id"])
    return render_template("verify_scoresheet.html",sub_id=subject_id,  classData = classrow, schoolInfo=schoolrow)
    
    
@app.route("/edit_student", methods=["POST"])
@login_required
@check_confirmed
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

@app.route("/edit_scoresheet", methods=["POST"])
@login_required
@check_confirmed
def edit_scoresheet():
    password = request.form.get("password")
    subject_id = request.form.get("subject_id")
    class_id = request.form.get("class_id")
    tables= database(class_id)
    classrow = db.execute("SELECT * FROM :classes WHERE id = :classId", classes = tables["session_data"], classId = tables["class_id"])
    schoolrow = db.execute("SELECT * FROM school WHERE id = :schoolId", schoolId = tables["school_id"])
    if check_password_hash(classrow[0]["password"], password) or check_password_hash(schoolrow[0]["admin_password"], password ):
        carow = db.execute("SELECT * FROM :catable",catable = tables["ca"])
        testrow = db.execute("SELECT * FROM :testtable",testtable = tables["test"])
        examrow = db.execute("SELECT * FROM :examtable",examtable = tables["exam"])
        subjectrow = db.execute("SELECT * FROM :subjecttable WHERE id=:id",subjecttable = tables["subjects"], id=subject_id)
        classlistrow = db.execute("SELECT * FROM :classlist",classlist = tables["classlist"])
        mastersheet_rows = db.execute("SELECT * FROM :mastersheet", mastersheet = tables["mastersheet"])
        subject_position_row = db.execute("SELECT * FROM :subject_position", subject_position = tables["subject_position"])
        current_settings = db.execute("SELECT * FROM :settings WHERE id = :id", settings = tables["class_term_data"], id=class_id)
        setting = current_settings[0]
        return render_template("edit_scoresheet.html",sub_id=subject_id, schoolInfo = schoolrow, classData = classrow, caData = carow, testData = testrow, examData = examrow, subjectData = subjectrow,class_list = classlistrow, mastersheet = mastersheet_rows, subject_position = subject_position_row, result = setting)
    else:
        error= ' The admin or class password is incorrect.'
        return render_class(class_id, error)


@app.route("/edited_student", methods=["POST"])
@login_required
@check_confirmed
def edited_student():
    student_id = request.form.get("student_id")
    class_id = request.form.get("class_id")
    tables= database(class_id)
    surname = "s"+str(student_id)
    schoolrow = db.execute("SELECT * FROM school WHERE id=:id", id = session["user_id"])
    classrow = db.execute("SELECT * FROM :classes ", classes = tables["session_data"])
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
    return render_class(class_id)

@app.route("/unregister_student", methods=["POST"])
@login_required
@check_confirmed
def unregister_student():
    student_id = request.form.get("student_id")
    class_id = request.form.get("class_id")
    remove_student(student_id, class_id)
    error="student deleted successfully"
    return render_class(class_id,error)

@app.route("/verify_customize", methods=["POST"])
@login_required
@check_confirmed
def verify_customize():
   class_id = request.form.get("class_id")
   tables= database(class_id)
   classrow = db.execute("SELECT * FROM :classes WHERE id = :classId", classes = tables["classes"], classId = tables["class_id"])
   schoolrow = db.execute("SELECT * FROM school WHERE id = :schoolId", schoolId = tables["school_id"])
   return render_template("verify_customize.html", classData = classrow, schoolInfo=schoolrow)

@app.route("/verified_customize", methods=["POST"])
@login_required
@check_confirmed
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
        return render_template("verify_customize.html", classData = classRows, schoolInfo=schoolrow)

    if check_password_hash(classRows[0]["password"], password) or check_password_hash(schoolrow[0]["admin_password"], password):
        return render_template("customize.html", schoolInfo = schoolrow,classData=classRows,subjects = subject, classInfo=class_info[0], class_setting=class_settings[0])
    else:
        error = "admin or class password incorrect"
        return render_class(class_id, error)



@app.route("/verify_add_student", methods=["POST"])
@login_required
@check_confirmed
def verify_add_student():
   class_id = request.form.get("class_id")
   tables= database(class_id)
   classrow = db.execute("SELECT * FROM :classes WHERE id = :classId", classes = tables["classes"], classId = tables["class_id"])
   schoolrow = db.execute("SELECT * FROM school WHERE id = :schoolId", schoolId = tables["school_id"])
   return render_template("verify_add_student.html", classData = classrow, schoolInfo=schoolrow)


@app.route("/verified_add_student", methods=["POST"])
@login_required
@check_confirmed
def verified_add_student():
    class_id = request.form.get("class_id")
    tables = database(class_id)
    password = request.form.get("password")
    schoolrow = db.execute("SELECT * FROM school WHERE id = :schoolId", schoolId = tables["school_id"])
    classrow = db.execute("SELECT * FROM :class_data WHERE id=:id ",class_data = tables["session_data"], id=class_id)
    class_info = db.execute("SELECT * FROM :classes WHERE id=:id",classes=tables["classes"], id=class_id)
    #select all the subjects
    subject = db.execute("SELECT * FROM :class_subjects",class_subjects = tables["subjects"] )
    # return classlist.html
    if not password:
        error = "provide admin or class password"
        flash(error,'success')
        return render_template("verify_add_student.html", classData = classrow, schoolInfo=schoolrow)

    if check_password_hash(classrow[0]["password"], password) or check_password_hash(schoolrow[0]["admin_password"], password):
        return render_template("add_student.html", schoolInfo = schoolrow,clas=classrow,subjects = subject, classInfo=class_info[0])
    else:
        classrow = db.execute("SELECT * FROM :classes ", classes = tables["classes"])
        error = "admin or class password incorrect"
        return render_class(class_id, error)
 
@app.route("/confirm_details", methods=["POST"])
@login_required
@check_confirmed
def confirm_details():
    session["single_details"]={}
    session["single_subject"]=[]
    class_id = request.form.get("class_id")
    tables= database(class_id)
    class_session = db.execute("SELECT * FROM :class_s WHERE id=:id", class_s = tables["session_data"], id= class_id )
    session["single_details"]["class_id"] = class_id
    session["single_details"]["class_name"] = class_session[0]["classname"]
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
    session["single_details"]["surname"] = request.form.get("surname")
    session["single_details"]["firstname"] = request.form.get("firstname")
    session["single_details"]["othername"] = request.form.get("othername")
    if not request.form.get("sex"):
        session["single_details"]["sex"] = "male"
    else:
        session["single_details"]["sex"] = request.form.get("sex")
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
        session["single_subject"].append(sub)
    rows = db.execute("SELECT * FROM school WHERE id = :school_id",school_id=tables["school_id"])
    
    # return classlist.html
    return render_template("confirm_single_scoresheet.html", schoolInfo = rows, subjects= class_subjects, details = session["single_details"], student_subjects=session["single_subject"])

@app.route("/student_added", methods=["POST"])
@login_required
@check_confirmed
def student_added():
    class_id = session["single_details"]["class_id"]
    tables= database(class_id)
    pins = generate_pins(10, 1)
    db.execute("INSERT INTO :classlist (surname, firstname, othername, sex, pin ) VALUES (:surname, :firstname, :othername, :sex, :pin)", classlist=tables["classlist"], surname= session["single_details"]["surname"].upper(), firstname=session["single_details"]["firstname"].upper(), othername=session["single_details"]["othername"].upper(), sex=session["single_details"]["sex"], pin = pins[0])
    student_row = db.execute("SELECT * FROM :classlist WHERE surname=:surname AND firstname=:firstname AND othername = :othername", classlist=tables["classlist"], surname = session["single_details"]["surname"].upper() ,firstname=session["single_details"]["firstname"].upper(), othername=session["single_details"]["othername"].upper())
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
    for subject in session["single_subject"]:
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
@login_required
@check_confirmed
def edit_class():
   class_id = str(request.args.get("class_id"))
   tables= database(class_id)
   classrow = db.execute("SELECT * FROM :classes WHERE id = :classId", classes = tables["session_data"], classId = class_id)
   schoolrow = db.execute("SELECT * FROM school WHERE id = :schoolId", schoolId = tables["school_id"])
   return render_template("verify_admin.html", classData = classrow, schoolInfo=schoolrow)


@app.route("/verified_admin", methods=["POST"])
@login_required
@check_confirmed
def verified_admin():        
    class_id = request.form.get("class_id")
    password = request.form.get("password")
    tables= database(str(class_id))
    classrow = db.execute("SELECT * FROM :classes WHERE id = :classId", classes = tables["session_data"], classId = class_id)
    schoolrow = db.execute("SELECT * FROM school WHERE id = :schoolId", schoolId = tables["school_id"])
    if check_password_hash(schoolrow[0]["admin_password"], password ):
        return render_template("edit_class.html", schoolInfo = schoolrow, classData=classrow)
    else:
        error = "admin password incorrect"
        return render_portfolio(error)

@app.route("/edited_class", methods=["POST"])
@login_required
@check_confirmed
def edited_class():
    class_id = request.form.get("id")
    tables= database(class_id)
    firstname = request.form.get("firstname")
    surname = request.form.get("surname")
    class_name = request.form.get("class_name")
    section = request.form.get("section")
    password = request.form.get("password")
    classrow = db.execute("SELECT * FROM :classes WHERE id = :classId", classes = tables["session_data"], classId = class_id)
    schoolrow = db.execute("SELECT * FROM school WHERE id = :schoolId", schoolId = tables["school_id"])
    if  firstname == " ":
        error = "class teachers firstname is empty"
        flash(error)
        return render_template("edit_class.html", schoolInfo = schoolrow, classData=classrow)
    if  surname == " ":
        error = "class teacher's surname is empty"
        flash(error)
        return render_template("edit_class.html", schoolInfo = schoolrow, classData=classrow)

    if  section == " ":
        error = "class section  is empty"
        flash(error)
        return render_template("edit_class.html", schoolInfo = schoolrow, classData=classrow)

    if  class_name == " ":
        error = "class name is empty"
        flash(error)
        return render_template("edit_class.html", schoolInfo = schoolrow, classData=classrow)
   
    if  password == " ":
        error = "password is empty"
        flash(error)
        return render_template("edit_class.html", schoolInfo = schoolrow, classData=classrow)
    class_name = class_name.lower()
    if class_name != classrow[0]["classname"]:
        row_class = db.execute("SELECT * FROM :classes WHERE classname = :check_name", classes = tables["session_data"], check_name = request.form.get("class_name").lower())
        if len(row_class) < 1: 
            db.execute("UPDATE :classes set classname=:name where id=:id", classes = tables["session_data"], name=request.form.get("class_name").lower(), id = tables["class_id"])
        else:
            error = "class with name "+class_name+" already exist"
            flash(error)
            return render_template("edit_class.html", schoolInfo = schoolrow, classData=classrow)
    firstname = firstname.lower()
    if  firstname != classrow[0]["firstname"]:
        db.execute("UPDATE :classes set firstname=:new_firstname where id=:id", classes = tables["session_data"], new_firstname=firstname, id = tables["class_id"])
    
    if  password != classrow[0]["password"]:
        db.execute("UPDATE :classes set password=:new_password where id=:id", classes = tables["session_data"], new_password=generate_password_hash(password), id = tables["class_id"])
    surname = surname.lower()
    if surname != classrow[0]["surname"]:
        db.execute("UPDATE :classes set surname=:new_surname where id=:id", classes = tables["session_data"], new_surname=surname, id = tables["class_id"])
    section = section.lower()
    if section != classrow[0]["section"]:
        db.execute("UPDATE :classes set section=:new_section where id=:id", classes = tables["session_data"], new_section = section, id = tables["class_id"])

    error = "class edited successfully"
    return render_portfolio(error)

@app.route("/delete_class", methods=["POST"])
@login_required
@check_confirmed
def delete_class():
    class_id = request.form.get("delete_class")
    tables= database(class_id)
    class_details = db.execute("SELECT * FROM :this_class WHERE id=:id", this_class=tables["session_data"], id=class_id)
    db.execute("DROP TABLE :cascore", cascore= tables["ca"])
    db.execute("DROP TABLE :test", test= tables["test"])
    db.execute("DROP TABLE :exam", exam= tables["exam"])
    db.execute("DROP TABLE :grade", grade= tables["grade"])
    db.execute("DROP TABLE :mastersheet", mastersheet= tables["mastersheet"])
    db.execute("DROP TABLE :subject_position", subject_position= tables["subject_position"])
    db.execute("DROP TABLE :subjects", subjects= tables["subjects"])
    db.execute("DROP TABLE :classlist", classlist= tables["classlist"])
    db.execute("DELETE  FROM :class_term where id=:id", class_term= tables["class_term_data"], id=tables["class_id"])
    db.execute("DELETE  FROM :session_term where id=:id", session_term= tables["session_data"], id=tables["class_id"])
    school = db.execute("SELECT * FROM school WHERE id=:id", id=session["user_id"])
    current_session = school[0]["current_session"]
    current_term = school[0]["current_term"]
    col = current_session+"_"+current_term
    db.execute("UPDATE :session_d SET :coln=:value  where id=:id", session_d= tables["sessions"], id=tables["class_id"], coln = col, value = None)
    error = class_details[0]["classname"]+" successfully deleted from "+current_term+" term "+current_session+" academic session"
    return render_portfolio(error)


@app.route("/delete_clas", methods=["POST"])
@login_required
@check_confirmed
def delete_clas():
    class_id = request.form.get("delete_class")
    tables= database(class_id)
    sessions = db.execute("SELECT * FROM :terms WHERE id=:id", terms = tables["sessions"], id=class_id)
    removed = False
    for term in sessions[0]:
        if sessions[0][term] and term != "id":
            current_session = term.split("_")
            this_session = current_session[0]
            this_term = current_session[1]
            classIdentifier = str(class_id)+"_"+str(this_term)+"_"+str(this_session)+"_"+str(tables["school_id"])
            ca_table  = "catable"+"_"+classIdentifier
            test_table = "testtable"+"_"+classIdentifier
            exam_table = "examtable"+"_"+classIdentifier
            subject_table = "subjects"+"_"+classIdentifier
            mastersheet_table = "mastersheet"+"_"+classIdentifier
            subject_position_table = "subject_position"+"_"+classIdentifier
            grade_table = "grade"+"_"+classIdentifier
            term_table = "class_term_data"+"_"+str(this_term)+"_"+str(this_session)+"_"+str(tables["school_id"])
            db.execute("DROP TABLE :cascore", cascore= ca_table)
            db.execute("DROP TABLE :test", test= test_table)
            db.execute("DROP TABLE :exam", exam= exam_table)
            db.execute("DROP TABLE :grade", grade= grade_table)
            db.execute("DROP TABLE :mastersheet", mastersheet= mastersheet_table)
            db.execute("DROP TABLE :subject_position", subject_position= subject_position_table)
            db.execute("DROP TABLE :subjects", subjects= subject_table)
            db.execute("DELETE  FROM :class_term where id=:id", class_term= term_table, id=tables["class_id"])
            if this_term == "3":
                session_data = "session_data"+"_"+str(session["user_id"])+"_"+this_session
                db.execute("DELETE  FROM :session_d where id=:id", session_d= session_data, id=tables["class_id"])
                removed = True
    db.execute("DELETE  FROM :classes where id=:id", classes= tables["classes"], id=tables["class_id"])
    if not removed:
        session_data = "session_data"+"_"+str(session["user_id"])+"_"+this_session
        db.execute("DELETE  FROM :session_d where id=:id", session_d= session_data, id=tables["class_id"])


    db.execute("DROP TABLE :classlist", classlist= tables["classlist"])
    db.execute("DELETE  FROM :school_session where id=:id", school_session= tables["sessions"], id=tables["class_id"])
    error = "success!"
    return render_portfolio(error)



@app.route("/verify_edit_student", methods=["GET"])
@login_required
@check_confirmed
def verify_edit_student():
   class_id = request.args.get("class_id")
   student_id = request.args.get("student_id")
   tables= database(class_id)
   classrow = db.execute("SELECT * FROM :classes WHERE id = :classId", classes = tables["classes"], classId = tables["class_id"])
   schoolrow = db.execute("SELECT * FROM school WHERE id = :schoolId", schoolId = tables["school_id"])
   return render_template("verify_teacher.html", classData = classrow, schoolInfo=schoolrow, id = student_id)


@app.route("/verify_edit_scoresheet", methods=["GET"])
@login_required
@check_confirmed
def verify_edit_scoresheet():
   class_id = request.args.get("class_id")
   subject_id = request.args.get("subject_id")
   tables= database(class_id)
   classrow = db.execute("SELECT * FROM :classes WHERE id = :classId", classes = tables["classes"], classId = tables["class_id"])
   schoolrow = db.execute("SELECT * FROM school WHERE id = :schoolId", schoolId = tables["school_id"])
   return render_template("verify_editor.html", classData = classrow, schoolInfo=schoolrow, id = subject_id)

@app.route("/mastersheet", methods=["POST"])
@login_required
@check_confirmed
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
    return render_template("printable_mastersheet.html",result = results[0], caData = carow, testData = testrow, examData = examrow, classData = classrow, schoolInfo = schoolrow, subjectData=subjectrow,class_list = classlistrow, mastersheet = mastersheet_rows, subject_position= subject_p)


@app.route("/customize", methods=["POST"])
@login_required
@check_confirmed
def customize():
    class_id = request.form.get("class_id")
    tables = database(class_id)
    current_settings = db.execute("SELECT * FROM :settings WHERE id = :id", settings = tables["class_term_data"], id=class_id)
    setting = current_settings[0]
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
    if request.form.get("grading_type") and request.form.get("grading_type") != setting["grading_type"]:
        db.execute("UPDATE :settings SET grading_type = :grading_type WHERE id=:id", settings = tables["class_term_data"], grading_type = request.form.get("grading_type"), id=class_id)
        update_grade(class_id)

    return render_class(class_id, error ="setting updated successfully")

@app.route("/admin_verification", methods=["POST"])
@login_required
@check_confirmed
def admin_verification():        
    password = request.form.get("password")
    tables= database(0)
    classrow = db.execute("SELECT * FROM :classes", classes = tables["session_data"],)
    schoolrow = db.execute("SELECT * FROM school WHERE id = :schoolId", schoolId = tables["school_id"])
    settings = db.execute("SELECT * FROM :setting", setting = tables["class_term_data"])
    if check_password_hash(schoolrow[0]["admin_password"], password ):
        return render_template("customize_school.html", schoolInfo = schoolrow, classData=classrow, class_setting = settings)
    else:
        error = "admin password incorrect"
        flash(error)
        return render_template("admin_verification.html",schoolInfo = schoolrow, error=error)


@app.route("/school_settings", methods=["GET"])
@login_required
@check_confirmed
def school_settings():        
    tables= database(0)
    classrow = db.execute("SELECT * FROM :classes", classes = tables["session_data"],)
    schoolrow = db.execute("SELECT * FROM school WHERE id = :schoolId", schoolId = tables["school_id"])
    return render_template("admin_verification.html", schoolInfo = schoolrow, classData=classrow)

@app.route("/customize_school", methods=["POST"])
@login_required
@check_confirmed
def customize_school():
    tables = database("0")
    school_info = db.execute("SELECT * FROM school WHERE id=:id", id=session["user_id"])
    current_settings = db.execute("SELECT * FROM :settings", settings = tables["class_term_data"])
    if len(current_settings) > 0:
        setting = current_settings[0]
        if  request.form.get("background_color") != setting["background_color"] :
            db.execute("UPDATE :settings SET background_color = :background_color", settings= tables["class_term_data"], background_color = request.form.get("background_color"))
    
        if request.form.get("line_color") != setting["line_color"]:
            db.execute("UPDATE :settings SET line_color = :line_color", settings = tables["class_term_data"], line_color = request.form.get("line_color"))
        
        if request.form.get("text_color") and request.form.get("text_color") != setting["text_color"]:
            db.execute("UPDATE :settings SET text_color = :text_color" , settings = tables["class_term_data"], text_color = request.form.get("text_color"))

        if request.form.get("background_font") and request.form.get("background_font") != setting["background_font"]:
            db.execute("UPDATE :settings SET background_font = :background_font ", settings = tables["class_term_data"], background_font = request.form.get("background_font") )
        
        if request.form.get("ld_position") and request.form.get("ld_position") != setting["ld_position"]:
            db.execute("UPDATE :settings SET ld_position = :ld_position  ", settings = tables["class_term_data"], ld_position = request.form.get("ld_position") )

        if request.form.get("l_font") and request.form.get("l_font") != setting["l_font"]:
            db.execute("UPDATE :settings SET l_font = :ld_font  ", settings = tables["class_term_data"], ld_font = request.form.get("l_font") )

        if request.form.get("l_color") and request.form.get("l_color") != setting["l_color"]:
            db.execute("UPDATE :settings SET l_color = :ld_color  ", settings = tables["class_term_data"], ld_color = request.form.get("l_color") )
    
        if request.form.get("l_font-size") and request.form.get("l_font-size") != setting["l_fontsize"]:
            db.execute("UPDATE :settings SET l_fontsize = :l_fontsize", settings = tables["class_term_data"], l_fontsize = request.form.get("l_font-size") )
    
        if request.form.get("l_weight") and request.form.get("l_weight") != setting["l_weight"]:
            db.execute("UPDATE :settings SET l_weight = :l_weight  ", settings = tables["class_term_data"], l_weight = request.form.get("l_weight") )

        if request.form.get("sd_font") and request.form.get("sd_font") != setting["sd_font"]:
            db.execute("UPDATE :settings SET sd_font = :sd_font  ", settings = tables["class_term_data"], sd_font = request.form.get("sd_font") )

        if request.form.get("sd_color") and request.form.get("sd_color") != setting["sd_color"]:
            db.execute("UPDATE :settings SET sd_color = :sd_color  ", settings = tables["class_term_data"], sd_color = request.form.get("sd_color") )
    
        if request.form.get("sd_fontsize") and request.form.get("sd_fontsize") != setting["sd_fontsize"]:
            db.execute("UPDATE :settings SET sd_fontsize = :sd_fontsize  ", settings = tables["class_term_data"], sd_fontsize = request.form.get("sd_fontsize") )

        if request.form.get("sd_position") and request.form.get("sd_position") != setting["sd_position"]:
            db.execute("UPDATE :settings SET sd_position = :sd_position  ", settings = tables["class_term_data"], sd_position = request.form.get("sd_position") )

        if  request.form.get("sd_email") != setting["sd_email"] and request.form.get("sd_email") != 'None':
            db.execute("UPDATE :settings SET sd_email = :sd_email  ", settings = tables["class_term_data"], sd_email = request.form.get("sd_email") )
        
        if request.form.get("admin_email") != setting["admin_email"]:
            if request.form.get("admin_email") == 'on':
                db.execute("UPDATE :settings SET admin_email = :admin_email  ", settings = tables["class_term_data"], admin_email = 'on' )
            else:
                db.execute("UPDATE :settings SET admin_email = :admin_email  ", settings = tables["class_term_data"], admin_email = 'off' )

        if  request.form.get("address") != setting["address"] and request.form.get("address") != 'None' :
            db.execute("UPDATE :settings SET address = :address  ", settings = tables["class_term_data"], address = request.form.get("address") )
    
        if  request.form.get("po_box") != setting["po_box"] and request.form.get("po_box") != 'None':
            db.execute("UPDATE :settings SET po_box = :po_box  ", settings = tables["class_term_data"], po_box = request.form.get("po_box") )

        if  request.form.get("phone") != setting["phone"] and request.form.get("phone") != 'None':
            db.execute("UPDATE :settings SET phone = :phone  ", settings = tables["class_term_data"], phone = request.form.get("phone") )
        
        if  request.form.get("sd_other") != setting["sd_other"] and request.form.get("sd_other") != 'None':
            db.execute("UPDATE :settings SET sd_other = :sd_other ", settings = tables["class_term_data"], sd_other = request.form.get("sd_other") )

        if  request.form.get("next_term") != setting["next_term"] and request.form.get("next_term") != 'None' :
            db.execute("UPDATE :settings SET next_term = :next_term  ", settings = tables["class_term_data"], next_term = request.form.get("next_term") )
    
        if  request.form.get("address") != setting["address"] and request.form.get("address") != 'None' :
            db.execute("UPDATE :settings SET address = :address  ", settings = tables["class_term_data"], address = request.form.get("address") )

        if request.form.get("std_font") and request.form.get("std_font") != setting["std_font"]:
            db.execute("UPDATE :settings SET std_font = :std_font  ", settings = tables["class_term_data"], std_font = request.form.get("std_font") )

        if request.form.get("std_color") and request.form.get("std_color") != setting["std_color"]:
            db.execute("UPDATE :settings SET std_color = :std_color  ", settings = tables["class_term_data"], std_color = request.form.get("std_color") )
    
        if request.form.get("std_fontsize") and request.form.get("std_fontsize") != setting["std_fontsize"]:
            db.execute("UPDATE :settings SET std_fontsize = :std_fontsize  ", settings = tables["class_term_data"], std_fontsize = request.form.get("std_fontsize") )

        if  request.form.get("watermark") != setting["watermark"]:
            if request.form.get("watermark"):
                db.execute("UPDATE :settings SET watermark = :watermark ", settings = tables["class_term_data"], watermark = 'on')
            else :
                db.execute("UPDATE :settings SET watermark = :watermark ", settings = tables["class_term_data"], watermark = 'off')
        
        if request.form.get("std_position") and request.form.get("std_position") != setting["std_position"]:
            db.execute("UPDATE :settings SET std_position = :std_position  ", settings = tables["class_term_data"], std_position = request.form.get("std_position") )
    # if new term is selected or new session is selected 
    if (request.form.get("term") or request.form.get("session")):
        session_data = db.execute("SELECT * FROM :school_session", school_session = tables["session_data"])
        selected_session = request.form.get("session")
        selected_term = request.form.get("term")
        if not selected_session:
            selected_session = school_info[0]["current_session"]
        if not selected_term:
            selected_term = "1"

        # if term and session combination is not in existence  
        if not session_term_check(selected_session, selected_term):
            # if the selected session is the current session
            if selected_session == school_info[0]["current_session"]:
                new_term(selected_session, selected_term)
            else:
                return render_template("session_update.html", selected_session = selected_session, selected_term = selected_term, schoolInfo = school_info, session_data = session_data)
        else:
            db.execute("UPDATE school SET current_term = :cur, current_session=:sess WHERE id=:id", cur= selected_term, sess=selected_session, id= session["user_id"])
    return render_portfolio()


@app.route("/session_update", methods=["POST"])
@login_required
@check_confirmed
def session_update():
    new_term( request.form.get("selected_session"),request.form.get("selected_term"))
    db.execute("UPDATE school SET current_session=:c_s WHERE id=:id", c_s = request.form.get("selected_session"), id = session["user_id"])
    tables = database(0)
    classes = db.execute("SELECT * FROM :session_data", session_data = tables["session_data"])
    for  clas in classes:
        id = str(clas["id"])
        name = "name"+id
        ca = "ca"+id
        test ="test"+id
        exam = "exam"+id
        section = "section"+id
        form = request.form.get("formmaster").split(" ")
        firstname = None
        secondname = None
        othername = None
        if request.form.get("formmaster"):
            form = request.form.get("formmaster").split(" ")
            length = len(form)
            if length  > 0:
                firstname = form[0]
            if length > 1:
                secondname = form[1]
            if length > 2:
                othername = form[2]
        db.execute("UPDATE :data SET classname=:name,firstname = :first, surname = :sur, othername = :other, ca=:cs, test = :ts, exam =:ex, section =:sec",data = tables["session_data"], name=request.form.get(name), first = firstname, sur = secondname, other = othername, cs = request.form.get(ca), ts = request.form.get(test), ex = request.form.get(exam), sec=request.form.get(section))
    error = "session changed successfully"
    return render_portfolio(error)
         


@app.route("/check_results", methods=["POST","GET"])
def check_results():
    if request.method == "POST":
        if session:
            session.clear()
        #if reg number is empty
        if not request.form.get("regnumber"):
            error = "provide students regnumber"
            flash(error)
            return render_template("login.html")
        #if reg number is empty
        if  not request.form.get("pin"):
            error = "provide students pin"
            flash(error)
            return render_template("login.html")

        # get user digit
        reg_number = request.form.get("regnumber")
        pin = request.form.get("pin")
        #if len of user string is less than 10 render invalid regnumber
        if len(reg_number) < 7:
            session.clear()
            error = "reg number invalid"
            flash(error)
            return render_template("login.html")

        #collect student id class id and school id
        student_id = reg_number[0]+reg_number[1]+reg_number[2]
        while student_id[0] == "0":
            student_id = student_id.strip("0")

        class_id = reg_number[3]+reg_number[4]+reg_number[5]
        if class_id[0] == "0":
            class_id = class_id.strip("0")
        if class_id[0] == "0":
            class_id = class_id.strip("0")
        school_length = len(reg_number) - 6
        school_id = reg_number[-school_length:]
        #check if school exist else
        schoolInfo = db.execute("SELECT * FROM school WHERE id=:id", id = school_id)
        if len(schoolInfo) != 1:
            error ="reg number invalid"
            flash(error)
            return render_template("login.html")
            
        session["user_id"] = schoolInfo[0]["id"]
        tables = database(0)
        #check if class exist else "reg doesnt exist"
        classInfo = db.execute("SELECT * FROM :classes WHERE id = :id", classes = tables["classes"], id = class_id)
        if len(classInfo) != 1:
            error = "reg number invalid"
            session.clear()
            flash(error)
            return render_template("login.html")
        
        tables = database(str(classInfo[0]["id"]))
        #check if student exist in class else "reg doesnt exist"
        studentInfo = db.execute("SELECT * FROM :classlist WHERE id=:id", classlist=tables["classlist"], id=student_id)
        if len(studentInfo) != 1:
            error = "regnumber invalid"
            session.clear()
            flash(error)
            return render_template("login.html")
        
        #check if pin is same with given pin is students pin else pin is incorrect
        if pin != str(studentInfo[0]["pin"]):
            error = "pin invalid"
            session.clear()
            flash(error)
            return render_template("login.html")
        tables= database(class_id)
        classrow = db.execute("SELECT * FROM :session_data WHERE id = :classId", session_data = tables["session_data"], classId = tables["class_id"])
        schoolrow = db.execute("SELECT * FROM school WHERE id = :schoolId", schoolId = school_id)
        carow = db.execute("SELECT * FROM :catable where id=:id",catable = tables["ca"], id= student_id)
        testrow = db.execute("SELECT * FROM :testtable where id=:id",testtable = tables["test"], id= student_id)
        examrow = db.execute("SELECT * FROM :examtable where id=:id",examtable = tables["exam"], id= student_id)
        subjectrow = db.execute("SELECT * FROM :subjecttable",subjecttable = tables["subjects"])
        grades = db.execute("SELECT * FROM :grade_s where id=:id ",grade_s = tables["grade"], id=student_id)
        classlistrow = db.execute("SELECT * FROM :classlist where id=:id",classlist = tables["classlist"], id=student_id)
        mastersheet_rows = db.execute("SELECT * FROM :mastersheet where id=:id", mastersheet = tables["mastersheet"], id= student_id)
        subject_position_row = db.execute("SELECT * FROM :subject_position where id=:id", subject_position = tables["subject_position"], id= student_id)
        results = db.execute("SELECT * FROM :result WHERE id=:id", result = tables["class_term_data"], id = tables["class_id"])
        session.clear()
        return render_template("result_sheet.html",gradeRows = grades,result = results[0], schoolInfo = schoolrow, classData = classrow, caData = carow, testData = testrow, examData = examrow, subjectData = subjectrow,class_list = classlistrow, mastersheet = mastersheet_rows, subject_position = subject_position_row)
    else:
        return render_template("check_result.html")
            

@app.route("/result_check", methods=["POST"])
def result_check():
    # get user digit
    reg_number = request.form.get("regnumber")
    pin = request.form.get("pin")

    if len(reg_number) < 7:
        session.clear()
        return jsonify(value="fail")

    #collect student id class id and school id
    student_id = reg_number[0]+reg_number[1]+reg_number[2]
    while student_id[0] == "0":
        student_id = student_id.strip("0")

    class_id = reg_number[3]+reg_number[4]+reg_number[5]
    if class_id[0] == "0":
        class_id = class_id.strip("0")

    if class_id[0] == "0":
        class_id = class_id.strip("0")

    school_length = len(reg_number) - 6
    school_id = reg_number[-school_length:]
    
    #check if school exist else
    schoolInfo = db.execute("SELECT * FROM school WHERE id=:id", id = school_id)
    if len(schoolInfo) != 1:
        return jsonify(value="fail")
        
    session["user_id"] = schoolInfo[0]["id"]
    tables = database(0)
    #check if class exist else "reg doesnt exist"
    classInfo = db.execute("SELECT * FROM :classes WHERE id = :id", classes = tables["classes"], id = class_id)
    if len(classInfo) != 1:
        session.clear()
        return jsonify(value="fail")
    
    tables = database(str(classInfo[0]["id"]))
    #check if student exist in class else "reg doesnt exist"
    studentInfo = db.execute("SELECT * FROM :classlist WHERE id=:id", classlist=tables["classlist"], id=student_id)
    if len(studentInfo) != 1:
        session.clear()
        return jsonify(value="fail")
    
    #check if pin is same with given pin is students pin else pin is incorrect
    if pin != str(studentInfo[0]["pin"]):
        session.clear()
        return jsonify(value="pin invalid")
    
    else:
        return jsonify(value="pass")


@app.route("/admin_check", methods=["POST"])
@login_required
@check_confirmed
def admin_check():
    password = request.form.get("password")
    school = db.execute("SELECT * FROM school WHERE id=:id", id= session["user_id"])
    if check_password_hash(school[0]["admin_password"],password):
        return "correct"
    else:
        return "incorrect password"



@app.route("/terms", methods=["GET"])
def terms():
    return render_template("terms.html")

@app.route("/privacy", methods=["GET"])
def privacy():
    return render_template("privacy.html")


@app.route("/print_pins", methods=["GET"])
@login_required
@check_confirmed
def print_pins():        
    tables= database(0)
    classrow = db.execute("SELECT * FROM :classes", classes = tables["session_data"],)
    schoolrow = db.execute("SELECT * FROM school WHERE id = :schoolId", schoolId = tables["school_id"])
    return render_template("pin_verification.html", schoolInfo = schoolrow, classData=classrow)


@app.route("/admin_verified", methods=["POST"])
@login_required
@check_confirmed
def admin_verified():        
    password = request.form.get("password")
    tables= database(0)
    classrow = db.execute("SELECT * FROM :classes", classes = tables["session_data"],)
    schoolrow = db.execute("SELECT * FROM school WHERE id = :schoolId", schoolId = tables["school_id"])
    settings = db.execute("SELECT * FROM :setting", setting = tables["class_term_data"])
    classlist = []
    if check_password_hash(schoolrow[0]["admin_password"], password ):
        for klass in classrow:
            tables=database(klass["id"])
            classlis= db.execute("SELECT * FROM :classlist",classlist=tables["classlist"])
            classlist.append(classlis)
        return render_template("pins.html", schoolInfo = schoolrow, classData=classrow, result = settings[0], classlists= classlist)
    else:
        error = "admin password incorrect"
        flash(error)
        return render_template("pin_verification.html",schoolInfo = schoolrow, error=error)

@app.route("/manage_password", methods=["GET"])
@login_required
@check_confirmed
def manage_password():        
    tables= database(0)
    schoolrow = db.execute("SELECT * FROM school WHERE id = :schoolId", schoolId = tables["school_id"])
    return render_template("password_verification.html", schoolInfo = schoolrow)


@app.route("/password_verified", methods=["POST"])
@login_required
@check_confirmed
def password_verified():        
    password = request.form.get("password")
    tables= database(0)
    classrow = db.execute("SELECT * FROM :classes", classes = tables["session_data"],)
    schoolrow = db.execute("SELECT * FROM school WHERE id = :schoolId", schoolId = tables["school_id"])
    if check_password_hash(schoolrow[0]["admin_password"], password ):
        return render_template("change_passwords.html", schoolInfo = schoolrow, classData=classrow)
    else:
        error = "admin password incorrect"
        flash(error)
        return render_template("password_verification.html",schoolInfo = schoolrow, error=error)


@app.route("/password_changer", methods=["POST"])
@check_confirmed
@login_required
def password_changer():        
    tables= database(0)
    classrow = db.execute("SELECT * FROM :classes", classes = tables["session_data"])
    user_input = request.form.get("general")
    if user_input:
        db.execute("UPDATE school SET password = :general WHERE id=:id",general=generate_password_hash(request.form.get("general")), id=session["user_id"])
    for klass in classrow:
        if request.form.get(klass["id"]):
            db.execute("UPDATE :data SET password=:new_password",data = tables["session_data"], new_password=generate_password_hash(request.form.get(klass["id"])))
    error="password changed successfully"
    return render_portfolio(error)

