import requests
from cs50 import SQL
from flask import redirect, render_template, request, session, flash
from functools import wraps
from operator import itemgetter, attrgetter
from itsdangerous import URLSafeTimedSerializer
import random
import string

from flask_mail import Message, Mail


# mail session_data
MAIL_SERVER = 'smtp.googlemail.com'
MAIL_PORT = 465
MAIL_USE_TLS = False
MAIL_USE_SSL = True


# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///schools.db")


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def check_confirmed(func):
	@wraps(func)
	def decorated_function(*args, **kwargs):
		current_user = db.execute("SELECT * FROM school WHERE id=:id", id=session.get("user_id"))
		if current_user[0]["confirmed"] != "true":
			flash('Please confirm your account!', 'warning')
			return redirect("/unconfirmed")
		return func(*args, **kwargs)
	return decorated_function



# gives the initial of a name
def initials (name):
    return name[0].upper()
# returns the grade of any given score
def grade(score,grading_type="WAEC",from_user= False, a_min=False, a_max=False,b_min=False,b_max=False,c_min=False,c_max=False,d_max=False,d_min=False,e_max=False,e_min=False):
	score = int(score)
	if grading_type == "WAEC":
		pass_mark = 40
		if score < 40:
			score_grade = "F9"
		elif score > 39 and score < 46:
			score_grade = "E8"
		elif score > 44 and score < 50:
			score_grade = "D7"
		elif score > 49 and score < 55:
			score_grade = "C6"
		elif score > 54 and score < 60:
			score_grade = "C5"
		elif score > 59 and score < 65:
			score_grade = "C4"
		elif score > 64 and score < 70:
			score_grade = "B3"
		elif score > 69 and score < 75:
			score_grade = "B2"
		else:
			score_grade = "A1"
	elif grading_type == "SUBEB":
		pass_mark = 30
		if score < 29:
			score_grade = "F"
		elif score > 29 and score < 40:
			score_grade = "E"
		elif score > 39 and score < 50:
			score_grade = "D"
		elif score > 49 and score < 60:
			score_grade = "C"
		elif score > 59 and score < 70:
			score_grade = "B"
		else:
			score_grade = "A"
	else:
		pass_mark = from_user
		if score > (e_min - 1) and score < (e_max + 1):
			score_grade = "E"
		if score > (d_min - 1) and score < (d_max + 1):
			score_grade ="D"
		if score > (c_min -1) and score < (c_max + 1):
			score_grade = "C"
		if score > (b_min - 1) and score < (b_max + 1):
			score_grade = "B"
		if score > (a_min - 1) and score < (a_max + 1):
			score_grade = "A"
		if score < e_min:
			score_grade = "F"
		else:
			score_grade = "Non"
	grading ={}
	grading["score_grade"] = score_grade
	grading["pass_mark"] = pass_mark
	return grading

# forms the result data given the id of the class
def database(id):
    tables = {}
    # format class tables names
    school = db.execute("SELECT * FROM school WHERE id=:id", id=session["user_id"])
    current_session = school[0]["current_session"]
    current_term = school[0]["current_term"]
    tables["class_id"] = id
    tables["school_id"] = session["user_id"]
    schoolId = session["user_id"]
    tables["classes"] = "classes"+"_"+str(tables["school_id"])
    tables["sessions"] = "sessions"+"_"+str(tables["school_id"])
    classIdentifier = str(tables["class_id"])+"_"+str(current_term)+"_"+str(current_session)+"_"+str(tables["school_id"])
    tables["classlist"] = "classlist"+"_"+classIdentifier
    tables["ca"]  = "catable"+"_"+classIdentifier
    tables["test"] = "testtable"+"_"+classIdentifier
    tables["exam"] = "examtable"+"_"+classIdentifier
    tables["subjects"] = "subjects"+"_"+classIdentifier
    tables["mastersheet"] = "mastersheet"+"_"+classIdentifier
    tables["subject_position"] = "subject_position"+"_"+classIdentifier
    tables["grade"] = "grade"+"_"+classIdentifier
    tables["class_term_data"] = "class_term_data"+"_"+str(current_term)+"_"+str(current_session)+"_"+str(tables["school_id"])
    tables["session_data"] = "session_data"+"_"+str(current_term)+"_"+str(current_session)+"_"+str(tables["school_id"])

    return tables
#check array for duplicate
def has_duplicate(arr):
	if len(set(arr)) != len(arr):
		return True
	else:
		return False




def render_class(class_id, error=None):
    # format class tables names
    tables = database(class_id)
    #query database
    classrow = db.execute("SELECT * FROM :session_data WHERE id = :classId", session_data = tables["session_data"], classId = tables["class_id"])
    schoolrow = db.execute("SELECT * FROM school WHERE id = :schoolId", schoolId = session["user_id"])
    subjectrow = db.execute("SELECT * FROM :subjecttable",subjecttable = tables["subjects"])
    classlistrow = db.execute("SELECT * FROM :classlist",classlist = tables["classlist"])
    # render class veiw
    if error:
    	flash(error,'failure')
    return render_template("classView.html", schoolInfo = schoolrow, classData = classrow, subjectData = subjectrow,class_list = classlistrow, error=error)

def render_portfolio(error=None):
    tables = database(0)
    rows = db.execute("SELECT * FROM school WHERE id = :school_id ",school_id = session["user_id"])
    classrows = db.execute("SELECT * FROM :session_data ", session_data = tables["session_data"])
    if error:
    	flash(error,'failure')
    return render_template("portfolio.html", schoolInfo = rows, clas = classrows, error=error)
def ith_position(num):
	if num == 1:
		return str(1) + "st"
	elif num == 2:
		return str(2) + "nd"
	elif num == 3:
		return str(3) + "rd"
	else:
		return str(num)+"th"

def assign_student_position(class_id):
	tables = database(class_id)
	student_position  = db.execute("SELECT * FROM :mastersheet", mastersheet = tables["mastersheet"])
	student_position = sorted(student_position, key = itemgetter('average'), reverse=True)
	j = 0
	i = 0
	previous = 101
	for person in student_position:
		if previous == person["average"]:
			db.execute("UPDATE :mastersheet SET position = :sposition  WHERE id =:id", mastersheet = tables["mastersheet"],  sposition = ith_position(j), id = person["id"])
		else:
			j = i + 1
			db.execute("UPDATE :mastersheet SET position = :sposition  WHERE id =:id", mastersheet = tables["mastersheet"],  sposition = ith_position(j), id = person["id"])
		i = i + 1
		previous = person["average"]


def assign_subject_position(class_id, subject_id):
	tables = database(class_id)
	subject = str(subject_id)
	subject_position  = db.execute("SELECT * FROM :mastersheet",  mastersheet = tables["mastersheet"])
	subject_pos = sorted(subject_position, key = itemgetter(subject), reverse=True)
	j = 0
	i = 0
	previous = 101
	for person in subject_pos:
		if previous == person[subject]:
			db.execute("UPDATE :positIon_table SET :subject = :position    WHERE id =:id", positIon_table = tables["subject_position"],subject = subject,  position = ith_position(j), id = person["id"])
		else:
			j = i + 1
			db.execute("UPDATE :positIon_table SET :subject = :position    WHERE id =:id", positIon_table = tables["subject_position"],subject = subject,  position = ith_position(j), id = person["id"])
		i = i + 1
		previous = person[subject]


def random_string_generator(str_size, allowed_chars):
    return ''.join(random.choice(allowed_chars) for x in range(str_size))

def term_tables(classid):
	tables = database(classid)

	db.execute("CREATE TABLE :classsubjects ('id' INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, 'name' TEXT, 'total_score' INTEGER DEFAULT 0,'ppass' INTEGER DEFAULT 0,'class_average' INTEGER DEFAULT 0,'no_of_A' INTEGER DEFAULT 0, no_of_B INTEGER DEFAULT 0, no_of_C INTEGER DEFAULT 0,no_of_D INTEGER DEFAULT 0,no_of_E INTEGER DEFAULT 0,no_of_F INTEGER DEFAULT 0,'no_failed' INTEGER DEFAULT 0,'no_passed' INTEGER DEFAULT 0,'teachers_name' TEXT ,'teachers_initial' TEXT )",classsubjects = tables["subjects"] )

	# create  catable
	db.execute("CREATE TABLE :catable ('id' INTEGER PRIMARY KEY   NOT NULL)",catable = tables["ca"] )

	# create  grade
	db.execute("CREATE TABLE :grade ('id' INTEGER PRIMARY KEY   NOT NULL, 'no_of_A' INTEGER DEFAULT 0,'no_of_B' INTEGER DEFAULT 0,'no_of_C' INTEGER DEFAULT 0,'no_of_D' INTEGER DEFAULT 0,'no_of_E' INTEGER DEFAULT 0,'no_of_F' INTEGER DEFAULT 0)",grade = tables["grade"] )

	# create testtable
	db.execute("CREATE TABLE :testtable ('id' INTEGER PRIMARY KEY   NOT NULL)",testtable = tables["test"] )

	# create examtable
	db.execute("CREATE TABLE :examtable ('id' INTEGER PRIMARY KEY  NOT NULL)",examtable = tables["exam"] )
	
	# create mastersheet
	db.execute("CREATE TABLE :mastersheet ('id' INTEGER PRIMARY KEY  NOT NULL, 'total_score' INTEGER DEFAULT 0, 'average' INTEGER DEFAULT 0, 'subject_passed' INTEGER DEFAULT 0,'subject_failed' INTEGER DEFAULT 0, 'position' TEXT )",mastersheet = tables["mastersheet"] )

	# create subject_position
	db.execute("CREATE TABLE :subjectposition ('id' INTEGER PRIMARY KEY  NOT NULL)",subjectposition = tables['subject_position'] )

	# create classlist
	db.execute("CREATE TABLE :classlist ('id' INTEGER PRIMARY KEY  NOT NULL, 'surname' TEXT,'firstname' TEXT,'othername' TEXT,'sex' TEXT, 'pin' TEXT)",classlist = tables["classlist"] )


def drop_tables(classid):
	tables = database(classid)
	db.execute("DROP TABLE :classsubjects ",classsubjects = tables["subjects"] )

	# create  catable
	db.execute("DROP TABLE :catable",catable = tables["ca"] )

	# create  grade
	db.execute("DROP TABLE :grade",grade = tables["grade"] )

	# create testtable
	db.execute("DROP TABLE :testtable",testtable = tables["test"] )

	# create examtable
	db.execute("DROP TABLE :examtable ",examtable = tables["exam"] )

	# create mastersheet
	db.execute("DROP TABLE :mastersheet",mastersheet = tables["mastersheet"] )

	# create subject_position
	db.execute("DROP TABLE :subjectposition",subjectposition = tables['subject_position'] )

	# create classlist
	db.execute("DROP TABLE :classlist",classlist = tables['classlist'] )

def passwordGen(stringLength=8):
    """Generate a random string of fixed length """
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))
def percent(first, second):
	return (int(first)/int(second)) * 100

def remove_student(student_id, class_id,):
	tables= database(class_id)
	student_grade = db.execute("SELECT * FROM :grades WHERE id=:id", grades=tables["grade"], id=student_id)
	subjects = db.execute("SELECT * FROM :all_subjects", all_subjects = tables["subjects"])
	totals = db.execute("SELECT * FROM :mastersheet WHERE id = :id", mastersheet= tables["mastersheet"], id=student_id)
	class_details = db.execute("SELECT * FROM :class_table WHERE id=:id", class_table=tables["class_term_data"], id=class_id)
	#for each subject in grades
	for subject in subjects:
	#get students grade in this subject
		the_grade = student_grade[0][str(subject["id"])]
		if the_grade[0] == "F":
			db.execute("UPDATE :subjects SET no_failed = :new WHERE id = :id", subjects=tables["subjects"], new = int(subject["no_failed"])-1, id =subject["id"] ) 
		else:
			db.execute("UPDATE :subjects SET no_passed = :new WHERE id = :id", subjects=tables["subjects"], new = int(subject["no_passed"])-1, id =subject["id"] ) 
	#form the column string for no_of_column
		the_column = "no_of_"+str(the_grade[0])
		current = int(subject[the_column])
		#subract 1 from that no_of_column in subjects
		db.execute("UPDATE :subjects SET :no_of_grade = :new WHERE id = :id", subjects=tables["subjects"], no_of_grade=the_column,new=current -1, id =subject["id"] ) 
		new_total = int(subject["total_score"]) - int(totals[0][str(subject["id"])])
		#subtract students total from subjects total 
		db.execute("UPDATE :subjects SET total_score = :new WHERE id = :id", subjects=tables["subjects"], new= new_total , id =subject["id"]) 
		#recalculate subject average
		new_average = new_total / (int(class_details[0]["noOfStudents"]) -1)
		db.execute("UPDATE :subjects SET class_average = :new WHERE id = :id", subjects=tables["subjects"], new= new_average, id =subject["id"]) 

	db.execute("DELETE  FROM :ca where id=:id", ca = tables["ca"], id=student_id)
	db.execute("DELETE  FROM :grades where id=:id", grades = tables["grade"], id=student_id)
	db.execute("DELETE  FROM :test where id=:id", test = tables["test"], id=student_id)
	db.execute("DELETE  FROM :exam where id=:id", exam = tables["exam"], id=student_id)
	db.execute("DELETE  FROM :mastersheet where id=:id", mastersheet = tables["mastersheet"], id=student_id)
	db.execute("DELETE  FROM :subject_position where id=:id", subject_position = tables["subject_position"], id=student_id)
	db.execute("DELETE  FROM :classlist where id=:id", classlist = tables["classlist"], id=student_id)
	db.execute("UPDATE :class_details SET noOfStudents= :new_no WHERE id=:id",class_details = tables["class_term_data"],new_no=int(class_details[0]["noOfStudents"]) - 1, id=class_id)
	assign_student_position(class_id)

	for subject in subjects:
		assign_subject_position(class_id, subject["id"])


def add_student(student_id, class_id):
	tables= database(class_id)
	student_grade = db.execute("SELECT * FROM :grades WHERE id=:id", grades=tables["grade"], id=student_id)
	subjects = db.execute("SELECT * FROM :all_subjects", all_subjects = tables["subjects"])
	totals = db.execute("SELECT * FROM :mastersheet WHERE id = :id", mastersheet= tables["mastersheet"], id=student_id)
	class_details = db.execute("SELECT * FROM :class_table WHERE id=:id", class_table=tables["class_term_data"], id=class_id)
	#for each subject in grades
	student_total = 0
	passed = 0
	failed = 0
	new_total = 0
	for subject in subjects:
		student_total = student_total + int(totals[0][str(subject["id"])])
		the_grade = student_grade[0][str(subject["id"])][0]
		if the_grade == "F":
			db.execute("UPDATE :subjects SET no_failed = :new WHERE id = :id", subjects=tables["subjects"], new = int(subject["no_failed"])+1, id =subject["id"] )
			failed = failed + 1 

		else:
			db.execute("UPDATE :subjects SET no_passed = :new WHERE id = :id", subjects=tables["subjects"], new = int(subject["no_passed"])+1, id =subject["id"] ) 
			passed = passed + 1
		#form the column string for no_of_column
		the_column = "no_of_"+str(the_grade)
		current = int(subject[the_column])
		#subract 1 from that no_of_column in subjects
		db.execute("UPDATE :subjects SET :no_of_grade = :new WHERE id = :id", subjects=tables["subjects"], no_of_grade=the_column,new=current + 1, id =subject["id"] ) 
		previous = db.execute("SELECT * FROM  :grades WHERE id = :id", grades=tables["grade"], id =student_id )
		new_no = int(previous[0][the_column])  + 1
		db.execute("UPDATE :grades SET :no_of_grade = :new  WHERE id = :id", grades=tables["grade"], no_of_grade=the_column,new=new_no, id =student_id ) 

		db.execute("UPDATE :mastersheet SET subject_failed = :new WHERE id = :id", mastersheet=tables["mastersheet"], new = failed, id =student_id) 
		db.execute("UPDATE :mastersheet SET subject_passed = :new WHERE id = :id", mastersheet=tables["mastersheet"], new = passed, id =student_id) 

		new_total = int(subject["total_score"]) + int(totals[0][str(subject["id"])])
		#subtract students total from subjects total 
		db.execute("UPDATE :subjects SET total_score = :new WHERE id = :id", subjects=tables["subjects"], new= new_total , id =subject["id"]) 
		#recalculate subject average
		new_average = new_total / int(class_details[0]["noOfStudents"])
		db.execute("UPDATE :subjects SET class_average = :new WHERE id = :id", subjects=tables["subjects"], new= new_average, id =subject["id"]) 
	if len(subjects) > 	0:
		student_average = student_total/len(subjects)
		db.execute("UPDATE :mastersheet SET average = :new WHERE id=:id", mastersheet=tables["mastersheet"], new=student_average, id=student_id)
		db.execute("UPDATE :mastersheet SET total_score = :new WHERE id=:id", mastersheet=tables["mastersheet"], new=student_total, id=student_id)
		assign_student_position(class_id)
		for subject in subjects:
			assign_subject_position(class_id, subject["id"])


def update_grade(class_id):
	tables = database(class_id)
	classroom = db.execute("SELECT * FROM :classes WHERE id = :class_id", classes = tables["classes"], class_id= tables["class_id"])
	current_settings = db.execute("SELECT * FROM :settings WHERE id = :id", settings = tables["class_term_data"], id=class_id)
	subjects  = db.execute("SELECT * FROM :subjects", subjects = tables["subjects"])
	db.execute("UPDATE :grades SET :a = 0,  :b = 0,  :c =0 , :d = 0, :e = 0, :f = 0", grades = tables["grade"],a = "no_of_A", b = "no_of_B", c = "no_of_C", d = "no_of_D", e = "no_of_E", f = "no_of_F")
	db.execute("UPDATE :mastersheet SET subject_passed = 0, subject_failed= 0", mastersheet = tables["mastersheet"])


	for subject in subjects:
		subject_col = str(subject["id"])
		sj_f = 0
		sj_a = 0
		sj_b = 0
		sj_c = 0
		sj_d = 0
		sj_e = 0
		sj_passes = 0
		sj_failures = 0
		mastersheet_data = db.execute("SELECT * FROM :mastersheet", mastersheet = tables["mastersheet"])
		for student in mastersheet_data:
			total = student[subject_col]
			sub_grade = grade(total, str(current_settings[0]["grading_type"]))
			sub_grade = sub_grade["score_grade"]
			grade_col = "no_of_"+sub_grade[0]
			db.execute("UPDATE :grades SET :subject_c = :grade WHERE id=:id", grades = tables["grade"], subject_c = subject_col,grade = sub_grade, id = student["id"] )
			current_grades = db.execute("SELECT * FROM :grades WHERE id=:id", grades = tables["grade"], id = student["id"])
			if sub_grade[0] == "F":
				db.execute("UPDATE :master SET subject_failed = :value WHERE id=:id", master = tables["mastersheet"], value = int(student["subject_failed"])+1, id = student["id"])
				db.execute("UPDATE :grades SET :grade = :value WHERE id=:id", grades = tables["grade"], grade = grade_col, value = int(current_grades[0][grade_col])+1, id = student["id"])
				sj_failures = sj_failures + 1
				sj_f = sj_f + 1
			else:
				db.execute("UPDATE :master SET subject_passed = :value WHERE id=:id", master = tables["mastersheet"], value = int(student["subject_passed"])+1, id = student["id"])
				sj_passes = sj_passes + 1
			if sub_grade[0] ==  "A":
				sj_a = sj_a + 1
				db.execute("UPDATE :grades SET :grade = :value WHERE id=:id", grades = tables["grade"], grade = grade_col, value = int(current_grades[0][grade_col])+1, id = student["id"])
			elif sub_grade[0] ==  "B":
				sj_b = sj_b + 1
				db.execute("UPDATE :grades SET :grade = :value WHERE id=:id", grades = tables["grade"], grade = grade_col, value = int(current_grades[0][grade_col])+1, id = student["id"])
			elif sub_grade[0] ==  "C":
				sj_c = sj_c + 1
				db.execute("UPDATE :grades SET :grade = :value WHERE id=:id", grades = tables["grade"], grade = grade_col, value = int(current_grades[0][grade_col])+1, id = student["id"])
			elif sub_grade[0] ==  "D":
				sj_d = sj_d + 1
				#increase no of D for student
				db.execute("UPDATE :grades SET :grade = :value WHERE id=:id", grades = tables["grade"], grade = grade_col, value = int(current_grades[0][grade_col])+1, id = student["id"])
			elif sub_grade[0] ==  "E":
				sj_e = sj_e + 1
				#increase no of E for student
				db.execute("UPDATE :grades SET :grade = :value WHERE id=:id", grades = tables["grade"], grade = grade_col, value = int(current_grades[0][grade_col])+1, id = student["id"])
		subject_row = db.execute("SELECT * FROM :subject WHERE id = :id", subject = tables["subjects"], id = subject["id"])
		no_of_students_present = sj_passes + sj_failures
		pass_percent = (sj_passes/no_of_students_present) * 100
		db.execute("UPDATE :subject SET ppass = :pass_percent1, no_of_A=:s_a, no_of_B=:s_b, no_of_C=:s_c, no_of_D=:s_d, no_of_E=:s_e, no_of_F=:s_f, no_passed= :n_pass, no_failed=:n_fail  WHERE id=:id ", subject=tables["subjects"], pass_percent1 = pass_percent, s_a = sj_a, s_b = sj_b, s_c = sj_c, s_d = sj_d, s_e = sj_e, s_f = sj_f, n_pass = sj_passes, n_fail = sj_failures, id = subject["id"])

#reeturns true if session_term exist and false if it does not exist
def session_term_check(session,term):
	tables = database(0)
	session_columns = db.execute("SELECT * FROM :ss", ss= tables["sessions"])
	session_columns = session_columns[0].keys()
	for s_t in session_columns:
		if s_t != "id":
			session_term = s_t.split("_")
			current_sesssion = session_term[0]
			current_term = session_term[1]
			if session == current_sesssion:
				if term ==current_term:
					return True
	return False
def new_term(school_session,term):
	tables = database(0)
	selected_term = term
	selected_session = school_session
	former_term_settings = db.execute("SELECT * FROM :class_settings",class_settings = tables["class_term_data"])
	new_session = selected_session+"_"+selected_term
	#alter table add column new_session
	db.execute("ALTER  TABLE :sessions ADD COLUMN :this_column", sessions=tables["sessions"],this_column=new_session)
	class_term_data = "class_term_data"+"_"+str(selected_term)+"_"+str(selected_session)+"_"+str(session["user_id"])
	session_data = "session_data"+"_"+str(selected_term)+"_"+str(selected_session)+"_"+str(session["user_id"])
	
	db.execute("CREATE TABLE :setting ('id' INTEGER PRIMARY KEY NOT NULL, 'classname' TEXT, 'grading_type' INTEGER, 'comment_lines' INTEGER,'student_position' INTEGER DEFAULT 1, 'surname' TEXT, 'firstname' TEXT,'othername' TEXT,'password' TEXT,'section' TEXT, 'ca' INTEGER, 'test' INTEGER,'exam' INTEGER)", setting = session_data)

	# create class term tables
	db.execute("CREATE TABLE :result ('id' INTEGER PRIMARY KEY  NOT NULL, 'noOfStudents' INTEGER DEFAULT 0,'noOfSubjects' INTEGER DEFAULT 0, 'no_of_passes' INTEGER DEFAULT 0, 'no_of_failures' INTEGER DEFAULT 0, 'grading_type' TEXT DEFAULT 'WAEC','background_color' TEXT DEFAULT 'white','text_color' TEXT DEFAULT 'black','line_color' TEXT DEFAULT 'black','background_font' TEXT DEFAULT 'Ariel','ld_position' TEXT DEFAULT 'center','l_font' TEXT DEFAULT 'Ariel Black','l_weight' TEXT DEFAULT '900','l_color' TEXT DEFAULT '#00ff40','l_fontsize' TEXT DEFAULT '30px','sd_font' TEXT DEFAULT 'Ariel','sd_color' TEXT DEFAULT '#808000','sd_fontsize' TEXT DEFAULT '20px','sd_position' TEXT DEFAULT 'center','sd_email' TEXT,'admin_email' TEXT DEFAULT 'off', 'address' TEXT,'po_box' TEXT,'phone' TEXT,'next_term' TEXT,'sd_other' TEXT,'std_color' TEXT DEFAULT 'black','std_font' TEXT DEFAULT 'Arial Narrow','std_fontsize' TEXT DEFAULT '18px','std_position' TEXT DEFAULT 'left','table_type' TEXT DEFAULT 'bordered','ca' TEXT DEFAULT 'on','test' TEXT DEFAULT 'on','exam' TEXT DEFAULT 'on','combined' TEXT DEFAULT 'on','subject_total' TEXT DEFAULT 'on','class_average' TEXT DEFAULT 'on','subject_position' TEXT DEFAULT 'on','grade' TEXT DEFAULT 'on','subject_comment' TEXT DEFAULT 'off','teachers_initials' TEXT DEFAULT 'on','total_score' TEXT DEFAULT 'on','average' TEXT DEFAULT 'on','position' TEXT DEFAULT 'on','teachers_line' INTEGER DEFAULT 0,'shadow' TEXT DEFAULT 'on','principal_line' INTEGER DEFAULT 0,'teachers_signature' TEXT DEFAULT 'off','principal_signature' TEXT DEFAULT 'off','pandf' TEXT DEFAULT 'on','grade_summary' TEXT DEFAULT 'on','watermark' TEXT DEFAULT 'off','email_notification' TEXT DEFAULT 'off')",result = class_term_data)
	for  clas in former_term_settings:
		former = database(clas["id"])
		class_settings = db.execute("SELECT * FROM :settings WHERE id=:id", settings = former["class_term_data"], id=clas["id"])
		class_details = db.execute("SELECT * FROM :details WHERE id=:id", details = former["session_data"], id=clas["id"])
		# format class tables names
		current_session = selected_session
		current_term = selected_term
		classIdentifier = str(clas["id"])+"_"+str(selected_term)+"_"+str(selected_session)+"_"+str(former["school_id"])
		classlist = "classlist"+"_"+classIdentifier
		ca  = "catable"+"_"+classIdentifier
		test = "testtable"+"_"+classIdentifier
		exam = "examtable"+"_"+classIdentifier
		subjects = "subjects"+"_"+classIdentifier
		mastersheet = "mastersheet"+"_"+classIdentifier
		subject_position = "subject_position"+"_"+classIdentifier
		grade = "grade"+"_"+classIdentifier
		#create tables
		db.execute("CREATE TABLE :classsubjects ('id' INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, 'name' TEXT, 'total_score' INTEGER DEFAULT 0,'ppass' INTEGER DEFAULT 0,'class_average' INTEGER DEFAULT 0,'no_of_A' INTEGER DEFAULT 0, no_of_B INTEGER DEFAULT 0, no_of_C INTEGER DEFAULT 0,no_of_D INTEGER DEFAULT 0,no_of_E INTEGER DEFAULT 0,no_of_F INTEGER DEFAULT 0,'no_failed' INTEGER DEFAULT 0,'no_passed' INTEGER DEFAULT 0,'teachers_name' TEXT ,'teachers_initial' TEXT )",classsubjects = subjects )

		# create  catable
		db.execute("CREATE TABLE :catable ('id' INTEGER PRIMARY KEY   NOT NULL)",catable = ca )

		# create  grade
		db.execute("CREATE TABLE :grade ('id' INTEGER PRIMARY KEY   NOT NULL, 'no_of_A' INTEGER DEFAULT 0,'no_of_B' INTEGER DEFAULT 0,'no_of_C' INTEGER DEFAULT 0,'no_of_D' INTEGER DEFAULT 0,'no_of_E' INTEGER DEFAULT 0,'no_of_F' INTEGER DEFAULT 0)",grade = grade )

		# create testtable
		db.execute("CREATE TABLE :testtable ('id' INTEGER PRIMARY KEY   NOT NULL)",testtable = test )

		# create examtable
		db.execute("CREATE TABLE :examtable ('id' INTEGER PRIMARY KEY  NOT NULL)",examtable = exam )

		# create mastersheet
		db.execute("CREATE TABLE :mastersheet ('id' INTEGER PRIMARY KEY  NOT NULL, 'total_score' INTEGER DEFAULT 0, 'average' INTEGER DEFAULT 0, 'subject_passed' INTEGER DEFAULT 0,'subject_failed' INTEGER DEFAULT 0, 'position' INTEGER )",mastersheet = mastersheet )

		# create subject_position
		db.execute("CREATE TABLE :subjectposition ('id' INTEGER PRIMARY KEY  NOT NULL)",subjectposition = subject_position )

		# create classlist
		db.execute("CREATE TABLE :classlist ('id' INTEGER PRIMARY KEY  NOT NULL, 'surname' TEXT,'firstname' TEXT,'othername' TEXT,'sex' TEXT, 'pin' TEXT)",classlist = classlist )
		#copy classlist
		tables = database(clas["id"])
		previous_classlist = db.execute("SELECT * FROM :classlist", classlist = tables["classlist"])
		pins = generate_pins(10, len(previous_classlist))
		#copy previous classlist
		i = 0
		for student in previous_classlist:
			db.execute("INSERT INTO :classlist (id, surname, firstname, othername, sex, pin)VALUES(:id, :surname, :firstname, :othername, :sex, :pin)",classlist=classlist, id = student["id"], surname= student["surname"], firstname = student["firstname"], othername=student["othername"], sex=student["sex"], pin = pins[i])
			db.execute("INSERT INTO :catable (id)VALUES(:id) ",catable = ca,id=student["id"])
			db.execute("INSERT INTO :testtable (id)VALUES(:id) ",testtable = test,id=student["id"])
			db.execute("INSERT INTO :examtable (id)VALUES(:id) ",examtable = exam,id=student["id"])
			db.execute("INSERT INTO :mastersheet (id)VALUES(:id) ",mastersheet = mastersheet,id=student["id"])
			db.execute("INSERT INTO :subject_position (id)VALUES(:id)",subject_position = subject_position,id=student["id"])
			db.execute("INSERT INTO :grades (id)VALUES(:id) ",grades = grade,id=student["id"])
			i = i + 1
		#insert into sessions
		db.execute("UPDATE :current_sessions SET :session_column = :value WHERE id=:id", current_sessions = tables["sessions"],session_column=new_session, value=new_session, id=clas["id"])
		#copy term tables
		db.execute("INSERT INTO :settings (id, noOfStudents ,noOfSubjects , no_of_passes , no_of_failures , grading_type ,background_color ,text_color ,line_color,background_font,ld_position,l_font ,l_weight ,l_color ,l_fontsize,sd_font,sd_color,sd_fontsize ,sd_position ,sd_email,admin_email , address ,po_box ,phone,next_term ,sd_other ,std_color,std_font,std_fontsize,std_position,table_type ,ca ,test,exam,combined ,subject_total,class_average,subject_position,grade,subject_comment ,teachers_initials,total_score,average,position,teachers_line ,shadow ,principal_line,teachers_signature,principal_signature,pandf ,grade_summary ,watermark, email_notification)VALUES(:id, :noOfStudents ,:noOfSubjects , :no_of_passes , :no_of_failures , :grading_type ,:background_color ,:text_color ,:line_color,:background_font,:ld_position,:l_font ,:l_weight ,:l_color ,:l_fontsize,:sd_font,:sd_color,:sd_fontsize ,:sd_position ,:sd_email,:admin_email , :address ,:po_box ,:phone,:next_term ,:sd_other ,:std_color,:std_font,:std_fontsize,:std_position,:table_type ,:ca ,:test,:exam,:combined ,:subject_total,:class_average,:subject_position,:grade,:subject_comment ,:teachers_initials,:total_score,:average,:position,:teachers_line ,:shadow ,:principal_line,:teachers_signature,:principal_signature,:pandf ,:grade_summary ,:watermark,:email_notification)",settings = class_term_data,id =clas["id"], noOfStudents = class_settings[0]["noOfStudents"] ,noOfSubjects = class_settings[0]["noOfSubjects"] , no_of_passes = class_settings[0]["no_of_passes"] , no_of_failures = class_settings[0]["no_of_failures"] , grading_type = class_settings[0]["grading_type"] ,background_color  = class_settings[0]["background_color"],text_color = class_settings[0]["text_color"] ,line_color = class_settings[0]["line_color"],background_font = class_settings[0]["background_font"],ld_position = class_settings[0]["ld_position"],l_font  = class_settings[0]["l_font"],l_weight = class_settings[0]["l_weight"] ,l_color  = class_settings[0]["l_color"],l_fontsize = class_settings[0]["l_fontsize"],sd_font = class_settings[0]["sd_font"],sd_color = class_settings[0]["sd_color"],sd_fontsize = class_settings[0]["sd_fontsize"] ,sd_position  = class_settings[0]["sd_position"],sd_email = class_settings[0]["sd_email"],admin_email  = class_settings[0]["admin_email"], address  = class_settings[0]["address"],po_box  = class_settings[0]["po_box"],phone= class_settings[0]["phone"],next_term  = class_settings[0]["phone"],sd_other  = class_settings[0]["phone"],std_color = class_settings[0]["std_color"],std_font = class_settings[0]["std_font"],std_fontsize = class_settings[0]["std_fontsize"],std_position = class_settings[0]["std_position"],table_type = class_settings[0]["table_type"] ,ca  = class_settings[0]["ca"],test = class_settings[0]["test"],exam = class_settings[0]["exam"],combined  = class_settings[0]["combined"],subject_total = class_settings[0]["subject_total"],class_average = class_settings[0]["noOfStudents"],subject_position = class_settings[0]["noOfStudents"],grade = class_settings[0]["grade"],subject_comment = class_settings[0]["subject_comment"] ,teachers_initials = class_settings[0]["teachers_initials"],total_score = class_settings[0]["total_score"],average = class_settings[0]["noOfStudents"],position = class_settings[0]["position"],teachers_line  = class_settings[0]["teachers_line"],shadow  = class_settings[0]["shadow"],principal_line = class_settings[0]["principal_line"],teachers_signature = class_settings[0]["teachers_signature"],principal_signature = class_settings[0]["principal_signature"],pandf  = class_settings[0]["pandf"],grade_summary  = class_settings[0]["grade_summary"],watermark = class_settings[0]["watermark"], email_notification = class_settings[0]["email_notification"])
		db.execute("INSERT INTO :class_detail (id, classname, grading_type, comment_lines, surname, firstname,password,section,ca,test,exam)VALUES(:id, :classname, :grading_type, :comment_lines, :surname, :firstname,:password,:section,:ca,:test,:exam)",class_detail =session_data,id=class_details[0]["id"], classname=class_details[0]["classname"], grading_type=class_details[0]["grading_type"], comment_lines=class_details[0]["comment_lines"], surname=class_details[0]["surname"], firstname=class_details[0]["firstname"],password=class_details[0]["password"],section=class_details[0]["section"],ca=class_details[0]["ca"],test=class_details[0]["test"],exam=class_details[0]["exam"])

	#update term om school
	db.execute("UPDATE school SET current_term=:value WHERE id=:id",value= selected_term, id=session["user_id"])


#todo 
def new_session(session,term):
	print("implement new_session")



def generate_pins(length, count, alphabet=string.digits):
  alphabet = ''.join(set(alphabet))
  if count > len(alphabet)**length:
    raise ValueError("Can't generate more than %s > %s pins of length %d out of %r" %
                      count, len(alphabet)**length, length, alphabet)
  def onepin(length):
    return ''.join(random.choice(alphabet) for x in range(length))
  result = set(onepin(length) for x in range(count))
  while len(result) < count:
    result.add(onepin(length))
  return list(result)
