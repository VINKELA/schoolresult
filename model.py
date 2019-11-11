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

from functions import  login_required, database, random_string_generator, render_portfolio, term_tables, drop_tables, grade, assign_student_position, assign_subject_position
db = SQL("sqlite:///schools.db")
def create_table():
	db.execute("CREATE TABLE 'school' ('id' integer PRIMARY KEY AUTOINCREMENT NOT NULL, 'username' text, 'email' text, 'school_name' text, 'address' text, 'city' text, 'state' text, 'current_term' text, 'current_session' text, 'password' text, 'admin_password' text, 'token_id' text, 'token' text,'confirmed' text DEFAULT 'false', 'registered_on' datetime, 'confirmed_on' datetime)")
	db.execute("INSERT INTO school (school_name, email,username, password,admin_password,confirmed, current_session, current_term) VALUES ('Schoolresult admin', 'Schoolresult@yahoo.com', 'admin', :hash,  :adminPassword,'true','2011/2012','1')", hash = generate_password_hash('Admin123'),adminPassword = generate_password_hash('Admin123'))
	db.execute("INSERT INTO school (school_name, email,username, password,admin_password,current_session,current_term, registered_on, confirmed) VALUES (:schoolname, :email, :username, :hash,  :adminPassword,:current_session,:term, :registered_on,'true')", schoolname = "YOUR SCHOOLNAME WILL BE HERE", email= "youschoolemail@yahoo.com", username = "user", hash = generate_password_hash("password"), adminPassword = generate_password_hash("admin_password"),current_session = "2019/2020",term='1', registered_on = datetime.datetime.now())
	# Query database for username
	rows = db.execute("SELECT * FROM school WHERE username = :user",user="user")
	school_classes = "classes"+"_"+str(rows[0]["id"])
	school_sessions = "sessions"+"_"+str(rows[0]["id"])
	current_session_data   = "session_data"+"_"+str(rows[0]["current_term"])+"_"+str(rows[0]["current_session"])+"_"+str(rows[0]["id"])
	class_term_data = "class_term_data"+"_"+str(rows[0]["current_term"])+"_"+str(rows[0]["current_session"])+"_"+str(rows[0]["id"])

	column = str(rows[0]["current_session"])+"_"+str(rows[0]["current_term"])
	db.execute("CREATE TABLE :sessions ('id' INTEGER PRIMARY KEY NOT NULL, :column TEXT)", sessions = school_sessions, column=column)
	db.execute("CREATE TABLE :classes ('id' INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,'identifier' TEXT )", classes = school_classes)
	db.execute("CREATE TABLE :setting ('id' INTEGER PRIMARY KEY NOT NULL, 'classname' TEXT, 'grading_type' INTEGER, 'comment_lines' INTEGER,'student_position' INTEGER DEFAULT 1, 'surname' TEXT, 'firstname' TEXT,'password' TEXT,'section' TEXT, 'ca' INTEGER, 'test' INTEGER,'exam' INTEGER)", setting = current_session_data)
	db.execute("CREATE TABLE :result ('id' INTEGER PRIMARY KEY  NOT NULL, 'noOfStudents' INTEGER DEFAULT 0,'noOfSubjects' INTEGER DEFAULT 0, 'no_of_passes' INTEGER DEFAULT 0, 'no_of_failures' INTEGER DEFAULT 0, 'grading_type' TEXT DEFAULT 'WAEC','background_color' TEXT DEFAULT '#fff','text_color' TEXT DEFAULT 'black','line_color' TEXT DEFAULT 'black','background_font' TEXT DEFAULT 'Ariel','ld_position' TEXT DEFAULT 'center','l_font' TEXT DEFAULT 'Ariel Black','l_weight' TEXT DEFAULT '900','l_color' TEXT DEFAULT '#537fbe','l_fontsize' TEXT DEFAULT '30px','sd_font' TEXT DEFAULT 'Ariel','sd_color' TEXT DEFAULT '#808000','sd_fontsize' TEXT DEFAULT '20px','sd_position' TEXT DEFAULT 'center','sd_email' TEXT,'admin_email' TEXT DEFAULT 'off', 'address' TEXT,'po_box' TEXT,'phone' TEXT,'next_term' TEXT,'sd_other' TEXT,'std_color' TEXT DEFAULT 'black','std_font' TEXT DEFAULT 'Arial Narrow','std_fontsize' TEXT DEFAULT '18px','std_position' TEXT DEFAULT 'left','table_type' TEXT DEFAULT 'striped','ca' TEXT DEFAULT 'on','test' TEXT DEFAULT 'on','exam' TEXT DEFAULT 'on','combined' TEXT DEFAULT 'on','subject_total' TEXT DEFAULT 'on','class_average' TEXT DEFAULT 'on','subject_position' TEXT DEFAULT 'on','grade' TEXT DEFAULT 'on','subject_comment' TEXT DEFAULT 'off','teachers_initials' TEXT DEFAULT 'off','total_score' TEXT DEFAULT 'on','average' TEXT DEFAULT 'on','position' TEXT DEFAULT 'on','teachers_line' INTEGER DEFAULT 0,'shadow' TEXT DEFAULT 'on','principal_line' INTEGER DEFAULT 0,'teachers_signature' TEXT DEFAULT 'off','principal_signature' TEXT DEFAULT 'off','pandf' TEXT DEFAULT 'on','grade_summary' TEXT DEFAULT 'on','watermark' TEXT DEFAULT 'off','email_notification' TEXT DEFAULT 'on')",result = class_term_data)

	print("tables created")

create_table()