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

from functions import apology, login_required, database, random_string_generator, render_portfolio, term_tables, drop_tables, grade, assign_student_position, assign_subject_position

db = SQL("postgres://suhvkspwdkqgsc:8e320b4f9f7a79bb0b8865bd86c078a500b62dbfc1a6cf6bcbb04704ad49214a@ec2-54-235-100-99.compute-1.amazonaws.com:5432/d7vb1s2vel25o3")

def create_table():
	db.execute("CREATE TABLE 'school' ('id'  SERIAL PRIMARY KEY NOT NULL, 'username' text, 'email' text, 'school_name' text, 'address' text, 'city' text, 'state' text, 'current_term' text, 'current_session' text, 'password' text, 'admin_password' text, 'token_id' text, 'token' text,'confirmed' text DEFAULT 'false', 'registered_on' timestamp, 'confirmed_on' timestamp)")
	db.execute("INSERT INTO school (school_name, email,username, password,admin_password,confirmed, current_session, current_term) VALUES ('classresult admin', 'classresult@yahoo.com', 'admin', :hash,  :adminPassword,'true','2011/2012','1')", hash = generate_password_hash('Admin123'),adminPassword = generate_password_hash('Admin123'))
	print("table created")


create_table()