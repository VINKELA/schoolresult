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
            db.execute("UPDATE :master SET subject_passed = :value,:subject = :score,total_score=:n_total,average = :n_average  WHERE id=:id", master = tables["mastersheet"], value = int(student_row[0]["subject_passed"])+1, id = student[0]subject = subject_id,score =total_score), n_total = new_total,n_average =new_average)
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


