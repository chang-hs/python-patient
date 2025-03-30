from flask import Flask, render_template, session, redirect, request, url_for, send_from_directory
from flask import flash
#from flask_script import Manager
from flask_bootstrap import Bootstrap5
from flask_wtf import FlaskForm
from flask_sqlalchemy import SQLAlchemy
from wtforms import StringField, RadioField, DateField, DateTimeField, HiddenField
from wtforms import TextAreaField, SelectField, SelectMultipleField, IntegerField, SubmitField
from wtforms.validators import InputRequired, Length
from flask_sqlalchemy import SQLAlchemy
from typing import List
from typing import Optional
from sqlalchemy import Column, Integer, Boolean, String, Date, Time, Text, ForeignKey, Table
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.orm import DeclarativeBase
import psycopg2
import datetime
import subprocess
from myforms import PtRegisterForm, OpRegisterForm, IdForm, MajordivForm, PathodivForm, DiseaseNameForm
from myforms import DiseaseNameWithNewForm, LocationForm, PatientIdForm, PatientNameForm, SearchKeyForm
from myforms import LocationWithNewForm, OpSearchForm, OpIdForm, LoginForm
from funcs import create_surgeon_string
from mymodel import Patient, Op, Diagnosis, OpDiag, DiseaseName, MajorDiv, PathoDiv, Location, Phone, Surgeon
from mymodel import OpSurgeon, User
from mymodel import db_session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash


#import sys
#sys.path.append('/home/chang/flasky/')
import funcs

app = Flask(__name__)
bootstrap = Bootstrap5(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://chang:stmmc364936@localhost/patient_2'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['SECRET_KEY'] = 'penfield'


@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def set_user_password(username, password):
    new_user = User(username=username, password=generate_password_hash(password))
    db_session.add(new_user)
    db_session.commit()

def update_user_password(username, password):
    user = User.query.filter_by(username=username).first()
    if user:
        user.password = generate_password_hash(password)
    db_session.commit()


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password', 'danger')
            return redirect(url_for('login'))
    return render_template('login.html', form=form)

@app.route('/')
@login_required
def home():
    return render_template('index.html', name="chang")


#患者登録画面用のview function
@app.route('/register/patient', methods=['GET', 'POST'])
@login_required
def pt_register():
    form = PtRegisterForm()
    if form.validate_on_submit():
        patient_id = form.patient_id.data
        kanji_name = form.kanji_name.data
        kana_name = form.kana_name.data
        sex = form.sex.data
        birth_date = form.birth_date.data
        zip_code = form.zip_code.data
        address = form.address.data
        phone_1 = form.phone_1.data
        phone_2 = form.phone_2.data

        new_patient = Patient(patient_id=patient_id, kanji_name=kanji_name,
                                kana_name=kana_name, birthdate=birth_date,
                                sex=sex, zipcode=zip_code, address=address)

        try:
            db_session.add(new_patient)
            db_session.commit()
        except:
            return render_template('message.html', message="Patient Input Error")
        #Insert phone numbers
        phones = [phone_1, phone_2]
        for phone_number in phones:
            if phone_number != '':
                new_phone = Phone(patient_id=patient_id, phone=phone_number)
                try:
                    db_session.add(new_phone)
                    db_session.commit()
                except:
                    return render_template('message.html', message="Phone Input Error")
        return render_template('message.html', message="Insertion successful")
   # Getで最初に呼ばれたときは、formを出す 
    return render_template('pt_register.html', form=form)

#手術登録画面用のview functioin
#まず、patient_idを取得する
@app.route('/register/op', methods = ['GET', 'POST'])
@login_required
def get_patient_id():
    patient_id_form = PatientIdForm()
    if patient_id_form.validate_on_submit():
        session['patient_id'] = patient_id_form.patient_id.data
        return redirect(url_for('op_register'))
    return render_template("patient_id.html", form=patient_id_form)

#手術データ入力画面
@app.route('/register/op/procedure', methods = ['GET', 'POST'])
@login_required
def op_register():
    patient_id = session['patient_id']
    sql = "SELECT kanji_name FROM patient WHERE patient_id = %s"
    try:
        conn = psycopg2.connect("dbname=patient_2 user=chang password=stmmc364936 host=localhost")
        cur = conn.cursor()
    except:
        return render_template("message.html", message="Database Opeening Error")
    try:
        cur.execute(sql, (patient_id,))
        kanji_name = cur.fetchone()[0]
    except:
        return render_template("message.html", message="Unable to obtain patient name from the id: " + patient_id)
    form = OpRegisterForm()
    form.patient_id.data = patient_id
    form.kanji_name.data = kanji_name
    #Form入力後の処理
    if form.validate_on_submit():
        patient_id = form.patient_id.data
        op_date = form.op_date.data
        preop_dx = form.preop_dx.data
        postop_dx = form.postop_dx.data
        procedure = form.procedure.data
        start_time = form.start_time.data.time().strftime('%H:%M')
        end_time = form.end_time.data.time().strftime('%H:%M')
        surgeons = form.surgeons.data
        surgeons_string = create_surgeon_string(surgeons)
        assistants = form.assistants.data
        assistants_string = create_surgeon_string(assistants)
        indication = form.indication.data
        op_note = form.op_note.data

        new_op = Op(patient_id=patient_id, op_date=op_date, preop_dx=preop_dx,
                    postop_dx=postop_dx, procedure=procedure,
                    start_time=start_time, end_time=end_time,
                    surgeons=surgeons, assistants=assistants,
                    indication=indication, op_note=op_note)
        #Database接続
        try:
            conn = psycopg2.connect("dbname=patient_2 user=chang password=stmmc364936 host=localhost")
            cur = conn.cursor()
        except:
            return render_template("message.html", message="Database Opening Error")

        #手術情報登録
        sql = "INSERT INTO op \
                (patient_id, op_date, preop_dx, postop_dx, procedure, \
                start_time, end_time, indication, op_note, surgeons, assistants) values \
                (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        try:
            cur.execute(sql, (patient_id, op_date, preop_dx, postop_dx,
                procedure, start_time, end_time, indication, op_note,
                surgeons_string, assistants_string))
            conn.commit()
        except:
            return render_template("message.html", message="Database Insertion Error")
 

        #Retrieve op_id from the data just inserted, using op_date and start_time as queues
        sql = "SELECT op_id FROM op WHERE op_date = %s and start_time = %s"
        try:
            cur.execute(sql, (op_date, start_time))
            for row in cur:
                op_id = row[0]   #Beware! op_id is integer
        except:
            return render_template("message.html", message="Op_id retrieval failed")

        #術者を、op_surgeon tableに登録
        sql = "INSERT INTO op_surgeon (op_id, surgeon_id) values (%s, %s)" 
        try:
            for surgeon_id in surgeons:
                cur.execute(sql, (op_id, surgeon_id))
                conn.commit()
        except:
            return render_template("message.html", message="Surgeon insertion failed")

        #助手を、op_assistant tableに登録
        sql = "INSERT INTO op_assistant (op_id, surgeon_id) values (%s, %s)" 
        try:
            for surgeon_id in assistants:
                cur.execute(sql, (op_id, surgeon_id))
                conn.commit()
        except:
            return render_template("message.html", message="Assistant insertion failed")
        #成功メッセージ
        cur.close()
        conn.close()
        session['op_id'] = op_id
        return render_template("message_with_url.html", message="Op_id: " +
                str(op_id) + "  Data Successfully Inserted",
                url=str(url_for("op_id_register")))

    #最初のform表示
    return render_template("op_register.html", form=form)

@app.route('/register/op_diag', methods = ['GET', 'POST'])
@login_required
def op_id_register():
    id_form  = IdForm()
    if id_form.validate_on_submit():
        session['op_id'] = id_form.op_id.data
        return redirect(url_for('major_div_register'))
    if 'op_id' in session:
        id_form.op_id = session['op_id']
    return render_template("id_form.html", form=id_form)

@app.route('/register/op_diag/majordiv', methods = ['GET', 'POST'])
@login_required
def major_div_register():
    major_div_form = MajordivForm()
    if major_div_form.validate_on_submit():
        session['major_div_id'] = major_div_form.major_div.data
        return redirect(url_for('patho_div_register'))
    return render_template("major_div.html", form=major_div_form)

@app.route('/register/op_diag/pathodiv', methods = ['GET', 'POST'])
@login_required
def patho_div_register():
    patho_div_form = PathodivForm()
    if patho_div_form.validate_on_submit():
        session['patho_div_id'] = patho_div_form.patho_div.data
        return redirect(url_for('disease_name_register'))
    return render_template("patho_div.html", form=patho_div_form)

@app.route('/register/op_diag/disease_name', methods = ['GET', 'POST'])
@login_required
def disease_name_register():
    sql = "SELECT DISTINCT dn.disease_name_id, dn.disease_name FROM disease_name dn \
            INNER JOIN diagnosis d ON d.disease_name_id = dn.disease_name_id \
            WHERE d.major_div_id = %s AND \
            d.patho_div_id = %s \
            ORDER BY dn.disease_name"
    try:
        conn = psycopg2.connect("dbname=patient_2 user=chang password=stmmc364936 host=localhost")
        cur = conn.cursor()
    except:
        return render_template("message.html", message="Databae Opening")
    try:
        cur.execute(sql, (session['major_div_id'], session['patho_div_id']))
    except:
        return render_template("message.html", message="Database Execution Error")
    disease_name_tuples = [(str(row[0]), row[1]) for row in cur]
    disease_name_form = DiseaseNameForm()
    disease_name_form.disease_name.choices = disease_name_tuples
    if disease_name_form.validate_on_submit():
        session['disease_name_id'] = disease_name_form.disease_name.data
        return redirect(url_for('location_register'))
    cur.close()
    conn.close()
    return render_template("disease_name.html", form=disease_name_form)

@app.route('/register/op_diag/location', methods = ['GET', 'POST'])
@login_required
def location_register():
    location_form = LocationForm()
    sql = "SELECT DISTINCT l.location_id, l.location FROM location l \
            INNER JOIN diagnosis d ON d.location_id = l.location_id \
            WHERE d.major_div_id = %s AND \
            d.patho_div_id = %s AND \
            d.disease_name_id = %s"
    try:
        conn = psycopg2.connect("dbname=patient_2 user=chang password=stmmc364936 host=localhost")
        cur = conn.cursor()
    except:
        return render_template("message.html", message="Database Opening Error")
    try:
        cur.execute(sql, (session['major_div_id'], session['patho_div_id'], session['disease_name_id']))
    except:
        return render_template("message.html", message="Database execution error")
    locations = [(str(row[0]), row[1]) for row in cur]
    location_form.location.choices = locations
    cur.close()
    conn.close()
    if location_form.validate_on_submit():
        session["location_id"] = location_form.location.data
        return redirect(url_for('database_insertion'))
    return render_template("location.html", form=location_form)

@app.route('/register/op_diag/database_insertion', methods = ['GET', 'POST'])
@login_required
def database_insertion():
    op_id = session['op_id']
    major_div_id = session['major_div_id']
    patho_div_id = session['patho_div_id']
    location_id = session['location_id']
    disease_name_id = session['disease_name_id']
    sql = "SELECT disease_id FROM diagnosis \
            WHERE major_div_id = %s AND \
            patho_div_id = %s AND \
            disease_name_id = %s AND \
            location_id = %s"
    try:
        conn = psycopg2.connect("dbname=patient_2 user=chang password=stmmc364936 host=localhost")
        cur = conn.cursor()
    except:
        return render_template("message.html", message="Database Opening Error")
    try:
        cur.execute(sql, (major_div_id, patho_div_id, disease_name_id, location_id))
        for row in cur:
            disease_id = row[0]
    except:
        return render_template("message.html", message="Database Execution Error")

    #Check whether the disease_id already exists in the database
    sql = "SELECT disease_id FROM op_diag WHERE op_id = %s"
    disease_id_list = []
    try:
        cur.execute(sql, (op_id,))
        for row in cur:
            disease_id_list.append(row[0])
    except:
        return render_template("message.html", message="Database execution \
                error when retrieving disease_id of the op_id")
    if disease_id_list and (disease_id in disease_id_list):
        return render_template("message.html", message="Disease_id already exists")

    #Final insertion of op_diag
    sql = "INSERT INTO op_diag (op_id, disease_id) values (%s, %s)"
    try:
        cur.execute(sql, (op_id, disease_id))
        conn.commit()
    except:
        return render_template("message.html", message="Error in the final insertion")
    cur.close()
    conn.close()
    return render_template("display_after_op_diag_insertion.html", op_id=op_id,
            disease_id=disease_id)


#@app.route('/diag_adm', methods = ['GET', 'POST'])
#def diag_adm_get_op_id():
#    op_id_form = OpIdForm()
#    if op_id_form.validate_on_submit():
#        session['op_id'] = op_id_form.op_id.data
#        return redirect(url_for('diag_adm_get_major'))
#    return render_template("op_id.html", form=op_id_form)

@app.route('/diag_adm', methods = ['GET', 'POST'])
@login_required
def diag_adm_get_major():
    major_div_form = MajordivForm()
    if major_div_form.validate_on_submit():
        session['major_div_id'] = major_div_form.major_div.data
        return redirect(url_for('diag_adm_get_patho'))
    return render_template("major_div.html", form=major_div_form)

@app.route('/diag_adm/pathodiv', methods = ['GET', 'POST'])
@login_required
def diag_adm_get_patho():
    patho_div_form = PathodivForm()
    if patho_div_form.validate_on_submit():
        session['patho_div_id'] = patho_div_form.patho_div.data
        return redirect(url_for('diag_adm_get_disease_name'))
    return render_template("patho_div.html", form=patho_div_form)

@app.route('/diag_adm/diseasename', methods = ['GET', 'POST'])
@login_required
def diag_adm_get_disease_name():
    major_div_id = session['major_div_id']
    patho_div_id = session['patho_div_id']
    try:
        conn = psycopg2.connect("dbname=patient_2 user=chang password=stmmc364936 host=localhost")
        cur = conn.cursor()
    except:
        return render_template("message.html", message="Database Opening Error")

    #Set pertinent disease names
    sql = "SELECT DISTINCT dn.disease_name_id, dn.disease_name FROM disease_name dn \
            INNER JOIN diagnosis d ON d.disease_name_id = dn.disease_name_id \
            WHERE d.major_div_id = %s AND d.patho_div_id = %s \
            ORDER BY dn.disease_name"
    try:
        cur.execute(sql, (major_div_id, patho_div_id))
        pertinent_list = [(str(row[0]), row[1]) for row in cur ]
    except:
        return render_template("message.html", message="Can't retrieve disease name")
    disease_name_with_new_form = DiseaseNameWithNewForm()
    pertinent_list[0:0] = [('0', '')]
    disease_name_with_new_form.disease_name.choices = pertinent_list

    #Set all disease names
    sql = "SELECT disease_name_id, disease_name FROM disease_name \
            ORDER BY disease_name"
    try:
        cur.execute(sql)
        all_list = [(str(row[0]), row[1]) for row in cur ]
    except:
        return render_template("message.html", message="Can't retrieve all disease names")
    all_list[0:0] = [('0', '')]
    disease_name_with_new_form.all_disease_name.choices = all_list

    #Procedure after validation
    if disease_name_with_new_form.validate_on_submit():
        disease_name_id = disease_name_with_new_form.disease_name.data
        disease_name_from_all_id = disease_name_with_new_form.all_disease_name.data
        new_disease_name = disease_name_with_new_form.new_disease_name.data
        if new_disease_name != '':
            sql = "INSERT INTO disease_name (disease_name) values \
                    (%s)"
            try:
                cur.execute(sql, (new_disease_name,))
                conn.commit()
            except:
                render_template("message.html", message="Database Execution Error")
            sql = "SELECT disease_name_id FROM disease_name WHERE \
                    disease_name = %s"
            try:
                cur.execute(sql, (new_disease_name,))
                new_disease_name_id = cur.fetchone()[0]
            except:
                render_template("message.html",
                        message="Failed to retrieve the new disease name")
            session['disease_name_id'] = new_disease_name_id
            return redirect(url_for('diag_adm_get_location'))
        elif disease_name_from_all_id != '0':
            session['disease_name_id'] = disease_name_from_all_id
            return redirect(url_for('diag_adm_get_location'))
        elif disease_name_id != '0':
            session['disease_name_id'] = disease_name_id
            return redirect(url_for('diag_adm_get_location'))
        else:
            return render_template("message.html", message="Can't decide a disease_name_id")
    #Initial display
    return render_template("disease_name_with_new.html", form=disease_name_with_new_form)

@app.route('/diag_adm/location', methods = ['GET', 'POST'])
@login_required
def diag_adm_get_location():
    major_div_id = session['major_div_id']
    patho_div_id = session['patho_div_id']
    disease_name_id = session['disease_name_id']
    try:
        conn = psycopg2.connect("dbname=patient_2 user=chang password=stmmc364936 host=localhost")
        cur = conn.cursor()
    except:
        return render_template("message.html", message="Database Opening Error")

    #Set pertinent location names
    sql = "SELECT DISTINCT l.location_id, l.location FROM location l \
            INNER JOIN diagnosis d ON d.location_id = l.location_id \
            WHERE d.major_div_id = %s AND d.patho_div_id = %s AND \
            d.disease_name_id = %s \
            ORDER BY l.location"
    try:
        cur.execute(sql, (major_div_id, patho_div_id, disease_name_id))
        pertinent_list = [(str(row[0]), row[1]) for row in cur ]
    except:
        return render_template("message.html", message="Can't retrieve location name")
    location_with_new_form = LocationWithNewForm()
    pertinent_list[0:0] = [('0', '')]
    location_with_new_form.location.choices = pertinent_list

    #Set all location names
    sql = "SELECT location_id, location FROM location \
            ORDER BY location"
    try:
        cur.execute(sql)
        all_list = [(str(row[0]), row[1]) for row in cur ]
    except:
        return render_template("message.html", message="Can't retrieve all location names")
    all_list[0:0] = [('0', '')]
    location_with_new_form.all_location.choices = all_list

    #Procedure after validation
    if location_with_new_form.validate_on_submit():
        location_id = location_with_new_form.location.data
        location_from_all_id = location_with_new_form.all_location.data
        new_location_name = location_with_new_form.new_location.data
        if new_location_name != '':
            sql = "INSERT INTO location (location) values \
                    (%s)"
            try:
                cur.execute(sql, (new_location_name,))
                conn.commit()
            except:
                render_template("message.html", message="Database Execution Error")
            sql = "SELECT location_id FROM location WHERE \
                    location = %s"
            try:
                cur.execute(sql, (new_location_name,))
                new_location_id = cur.fetchone()[0]
            except:
                render_template("message.html",
                        message="Failed to retrieve the new location")
            #他のidがstring型なのに合わせるため、str()が必要
            session['location_id'] = str(new_location_id)
            return redirect(url_for('diag_adm_set_diag'))
        elif location_from_all_id != '0':
            #既に登録されているlocationなら、その旨を通知して終了
            if location_from_all_id in pertinent_list:
                return render_template("message.html", message="Location already exists!")
            session['location_id'] = location_from_all_id
            return redirect(url_for('diag_adm_set_diag'))
        elif location_id != '0':
            return render_template("message.html", message="Diagnosis already exists!")
        else:
            return render_template("message.html", message="Can't decide a location_id")
    #Initial display
    return render_template("location_with_new.html", form=location_with_new_form)

@app.route('/diag_adm/set_diag', methods = ['GET', 'POST'])
@login_required
def diag_adm_set_diag():
    major_div_id = session['major_div_id']
    patho_div_id = session['patho_div_id']
    disease_name_id = session['disease_name_id']
    location_id = session['location_id']
    try:
        conn = psycopg2.connect('dbname=patient_2 user=chang password=stmmc364936 host=localhost')
        cur = conn.cursor()
    except:
        return render_template("message.html", message="Database Opening Error")
    #retrieve disease_name
    sql = "SELECT disease_name FROM disease_name WHERE disease_name_id = %s"
    try:
        cur.execute(sql, (disease_name_id,))
        disease_name = cur.fetchone()[0]
    except:
        return render_template("message.html", message="Can't retrieve disease name")
    #retrieve location
    sql = "SELECT location FROM location WHERE location_id = %s"
    try:
        cur.execute(sql, (location_id,))
        location = cur.fetchone()[0]
    except:
        return render_template("message.html", message="Can't retrieve location")
    #Insert data into diagnosis table
    sql = "INSERT INTO diagnosis (major_div_id, patho_div_id, location_id, \
            disease_name_id) values \
            (%s, %s, %s, %s)"
    try:
        cur.execute(sql, (major_div_id, patho_div_id, location_id,
            disease_name_id))
        conn.commit()
    except:
        return render_template("message.html", message="Can't insert into diagnosis")
    return render_template("diag_adm_success.html", major_div_id=major_div_id,
            patho_div_id=patho_div_id, location_id=location_id,
            disease_name_id=disease_name_id, disease_name=disease_name,
            location=location)

@app.route('/search/patient_name', methods = ['GET', 'POST'])
@login_required
def search_patient_name():
    patient_name_form = PatientNameForm()
    if patient_name_form.validate_on_submit():
        session['name_key'] = patient_name_form.patient_name.data
        return redirect(url_for('search_patients_from_name_key'))
    return render_template("patient_name.html", form=patient_name_form)


@app.route('/search/disease_id', methods = ['Get', 'POST'])
@login_required
def search_disease_id():
    search_key_form = SearchKeyForm()
    if search_key_form.validate_on_submit():
        session['search_key'] = search_key_form.search_key.data
        return redirect(url_for('search_disease_id_from_search_key'))
    return render_template("disease_name_key.html", form=search_key_form)

@app.route('/search_patient_id', methods = ['GET', 'POST'])
@login_required
def search_patient_id():
    patient_id_form = PatientIdForm()
    if patient_id_form.validate_on_submit():
        patient_id = patient_id_form.patient_id.data
        return redirect(url_for('show_patient', patient_id=patient_id))
    return render_template("patient_id.html", form=patient_id_form)

#Display Patient List from the input name on search_patient_name
@app.route('/search/patients_from_name_key', methods = ['GET', 'POST'])
@login_required
def search_patients_from_name_key():
    name_key = session['name_key']
    sql_result = Patient.query.filter(Patient.kanji_name.like('%'+name_key+'%')).all()

    patient_list = [(p.patient_id, p.kanji_name) for p in sql_result]

    return render_template("display_patient_list.html", patient_list = patient_list)

@app.route('/show_patient/<patient_id>', methods=['GET', 'POST'])
@login_required
def show_patient(patient_id):
    
    patient = Patient.query.filter(Patient.patient_id == patient_id).one()
        
    patient_dict = dict(zip(["ID", "名前", "かな", "性別", "生年月日", "郵便番号", "住所"], 
        [patient.patient_id, patient.kanji_name, patient.kana_name, patient.sex,
        patient.birthdate, patient.zipcode, patient.address]))

    phone_list = [p.phone for p in patient.phones]

    op_list = [(o.op_id, o.op_date, o.procedure,
                url_for("render_pdf_opnote", op_id = o.op_id),
                url_for("render_pdf_opnote_noid", op_id = o.op_id)) for o in patient.ops]

    return render_template("display_patient.html", patient_dic = patient_dict,
            phone_list = phone_list, op_list=op_list)

@app.route('/render_pdf_opnote/<op_id>', methods=['Get', 'Post'])
@login_required
def render_pdf_opnote(op_id):
    try:
        conn = psycopg2.connect('dbname=patient_2 user=chang password=stmmc364936 host=localhost')
        cur = conn.cursor()
    except:
        return render_template("message.html", message="Database Opening Error")
    sql = "SELECT p.patient_id, p.kanji_name, o.op_date, o.surgeons, o.assistants, o.start_time, \
            o.end_time, o.preop_dx, o.procedure, o.indication, o.op_note \
            FROM op o INNER JOIN patient p ON o.patient_id = p.patient_id \
            WHERE o.op_id = %s"
    cur.execute(sql, (op_id,))
    op = cur.fetchone()
    with open("/srv/http/opnote_template.tex", "rt") as template_file:
        opnote_template = template_file.read()
    pdf_text = opnote_template.format(
            op_id = op_id,
            patient_id = op[0],
            kanji_name = op[1],
            op_date = op[2],
            surgeons  = op[3],
            assistants = op[4],
            start_time = op[5],
            end_time = op[6],
            preop_diag = op[7],
            procedure = op[8],
            indication = op[9],
            op_note = op[10])
    with open("/home/chang/tmp/opnote.tex", "wt") as texfile:
        texfile.write(pdf_text)
    res = subprocess.call('/home/chang/texlive/2024/bin/x86_64-linux/platex -output-directory /home/chang/tmp /home/chang/tmp/opnote.tex', shell=True)
    res = subprocess.call('/home/chang/texlive/2024/bin/x86_64-linux/dvipdfmx -o /home/chang/tmp/opnote.pdf /home/chang/tmp/opnote', shell=True)
    cur.close()
    conn.close()
    # return send_from_directory('/home/chang/tmp', 'opnote.pdf', as_attachment=True, attachment_filename='opnote-' + op_id + '.pdf')
    return send_from_directory('/home/chang/tmp', 'opnote.pdf', as_attachment=True)


@app.route('/render_pdf_opnote_noid/<op_id>', methods=['GET', 'POST'])
@login_required
def render_pdf_opnote_noid(op_id):
    try:
        conn = psycopg2.connect('dbname=patient_2 user=chang password=stmmc364936 host=localhost')
        cur = conn.cursor()
    except:
        return render_template("message.html", message="Database Opening Error")
    sql = "SELECT p.patient_id, p.kanji_name, o.op_date, o.surgeons, o.assistants, o.start_time, \
            o.end_time, o.preop_dx, o.procedure, o.indication, o.op_note \
            FROM op o INNER JOIN patient p ON o.patient_id = p.patient_id \
            WHERE o.op_id = %s"
    cur.execute(sql, (op_id,))
    op = cur.fetchone()
    with open("/srv/http/opnote_template.tex", "rt") as template_file:
        opnote_template = template_file.read()
    pdf_text = opnote_template.format(
            op_id = op_id,
            patient_id = op[0],
            kanji_name = "anonymous",
            op_date = op[2],
            surgeons  = op[3],
            assistants = op[4],
            start_time = op[5],
            end_time = op[6],
            preop_diag = op[7],
            procedure = op[8],
            indication = op[9],
            op_note = op[10])
    with open("/home/chang/tmp/opnote.tex", "wt") as texfile:
        texfile.write(pdf_text)
    res = subprocess.call('/home/chang/texlive/2022/bin/x86_64-linux/platex -output-directory /home/chang/tmp /home/chang/tmp/opnote.tex', shell=True)
    res = subprocess.call('/home/chang/texlive/2022/bin/x86_64-linux/dvipdfmx -o /home/chang/tmp/opnote.pdf /home/chang/tmp/opnote', shell=True)
    cur.close()
    conn.close()
    return send_from_directory('/home/chang/tmp', 'opnote.pdf', as_attachment=True, 
            attachment_filename='opnote-' + op_id + '.pdf')

@app.route('/search/disease_id_from_search_key', methods=['GET', 'POST'])
@login_required
def search_disease_id_from_search_key():
    "Search disease id from a search key of the disease name"
    search_key = '%' + session['search_key'] + '%'
    try:
        conn = psycopg2.connect("dbname=patient_2 user=chang password=stmmc364936 host=localhost")
        cur = conn.cursor()
    except:
        return render_template("message.html", message="Can't connect to database")
    sql = "SELECT d.disease_id, dn.disease_name, m.major_div, p.patho_div, l.location "
    sql += "FROM diagnosis d "
    sql += "INNER JOIN disease_name dn ON d.disease_name_id = dn.disease_name_id "
    sql += "INNER JOIN majordiv m on d.major_div_id = m.major_div_id "
    sql += "INNER JOIN pathodiv p on d.patho_div_id = p.patho_div_id "
    sql += "INNER JOIN location l on d.location_id = l.location_id "
    sql += "WHERE dn.disease_name LIKE %s"
    cur.execute(sql, (search_key,)) 
    results = [
            {"disease_id": row[0], "disease_name": row[1],
            "major_div_id": row[2], "patho_div_id": row[3],
            "location": row[4] }
            for row in cur]
    cur.close()
    conn.close()
    return render_template("display_disease_ids.html", id_list=results,
            return_url=url_for("receive_disease_id"))

@app.route('/search/op', methods=['GET', 'POST'])
@login_required
def search_op():
    "Search operation from a table"
    search_key_form = OpSearchForm()
    if search_key_form.validate_on_submit():
        session['date_from'] = search_key_form.date_from.data
        session['date_to'] = search_key_form.date_to.data
        session['operator'] = search_key_form.operator.data
        session['procedure'] = search_key_form.procedure.data
        session['indication'] = search_key_form.indication.data
        session['opnote'] = search_key_form.opnote.data
        return redirect(url_for('op_search_from_key'))
    return render_template("op_search.html", form=search_key_form)

@app.route('/search/op_from_key', methods=['Get', 'Post'])
@login_required
def op_search_from_key():
    "Search op record from key"
    date_from = session['date_from']
    date_to = session['date_to']
    operator = session['operator']
    procedure = session['procedure']
    indication = session['indication']
    opnote = session['opnote']
    sql = "SELECT o.op_id, o.op_date, p.patient_id, p.kanji_name, o.procedure " \
          "FROM op o LEFT JOIN patient p on o.patient_id = p.patient_id " \
          "WHERE o.op_id > 1 "
    if date_from != "":
        sql = sql + "and o.op_date > '" + date_from + "' "
    if date_to != "":
        sql = sql + "and o.op_date < '" + date_to + "' "
    if procedure != "":
        sql = sql + "and o.procedure ~ '.*" + procedure + ".*' "
    if indication != "":
        sql = sql + "and o.indication ~ '.*" + indication + ".*' "
    if opnote != "":
        sql = sql + "and o.op_note ~ '.*" + opnote + ".*'"
    sql = sql + " ORDER BY o.op_date"
    try:
        conn = psycopg2.connect("dbname=patient_2 user=chang password=stmmc364936 host=localhost")
        cur = conn.cursor()
    except:
        return render_template("message.html", message="Database Opening Error")
    cur.execute(sql)
    results = cur.fetchall()
    result_list = [(item[0], item[1], item[2], item[3], item[4],
        url_for("render_pdf_opnote", op_id = item[0])) for item in results]
    return render_template("display_opsearch_result.html", sql=sql, result_list = result_list)

@app.route('/receive_disease_id', methods=['GET', 'POST'])
@login_required
def receive_disease_id():
    "Receive the submission from display_disease_ids.html, renders op_id_list "\
            "and redirect to op_id_list_from_disease_id_list"
    if request.method == "POST":
        disease_id_list = request.form.getlist("disease_id")
    session["disease_id_list"] = [int(item) for item in disease_id_list]
    return redirect(url_for("get_op_id_list_from_disease_id_list"))

@app.route('/search/op_id_list_from_disease_id_list', methods=['GET', 'POST'])
@login_required
def get_op_id_list_from_disease_id_list():
    "Obtain list of patients from a list of disease_id"
    disease_id_list = session["disease_id_list"]
    try:
        conn = psycopg2.connect(database="patient_2", host="localhost")
        cur = conn.cursor()
    except:
        return render_template("message.html", message="Can't connect to database")
    sql = "SELECT o.op_id FROM op o "\
          "INNER JOIN op_diag od ON od.op_id = o.op_id "\
          "WHERE od.disease_id = ANY(%s) "\
          "ORDER BY o.op_date"
    cur.execute(sql, (disease_id_list,))
    results = cur.fetchall()
    op_id_list = [ row[0] for row in results ]
    session['op_id_list'] = op_id_list
    cur.close()
    conn.close()
    return redirect(url_for("display_op_id_list"))
        
@app.route('/display_op_id_list', methods=['GET', 'POST'])
@login_required
def display_op_id_list():
    op_id_list = session['op_id_list']
    try:
        conn = psycopg2.connect(database="patient_2", host="localhost")
        cur = conn.cursor()
    except:
        return render_template("message.html", message="Can't connect to database")

    sql = "SELECT p.patient_id, p.kanji_name, o.op_id, o.op_date, "\
          "o.preop_dx, o.procedure "\
          "FROM op o "\
          "INNER JOIN patient p ON p.patient_id = o.patient_id "\
          "WHERE o.op_id = ANY(%s)" \
          "ORDER BY o.op_date"
    cur.execute(sql, (op_id_list,))
    results = cur.fetchall()
    op_rows = []

    for row in results:
        op_id = row[2]
        edited_exists = funcs.file_exists(op_id, "edited")
        dicom_exists = funcs.file_exists(op_id, "dicom")
        original_exists = funcs.file_exists(op_id, "original")
        op_rows.append({"patient_id": row[0], "kanji_name": row[1], 
            "op_id": row[2], "op_date": row[3], "preop_dx": row[4], 
            "procedure": row[5], "url": url_for('render_pdf_opnote', op_id = row[2]),
            "edited" : edited_exists, "dicom": dicom_exists,
            "original": original_exists})
    return render_template("display_op_list.html", op_list = op_rows)

@app.route('/presentation')
@login_required
def display_presentation():
    sql = "SELECT title, authors, meeting, date, location \
            FROM presentation ORDER BY date"
    try:
        conn = psycopg2.connect("dbname=presentation host=localhost")
        cur = conn.cursor()
    except:
        return render_template("message.html", message="Database Opening Error")
    try:
        cur.execute(sql)
        result = [row for row in cur]
    except:
        return render_template("message.html", message="Database Execution Error")
    return render_template("display_presentation.html", result=result)

class OpNoteForm(FlaskForm):
    indication = TextAreaField('indication', render_kw = {'rows':15,'cols':80})
    opnote = TextAreaField('opnote', render_kw= {'rows':25, 'cols':80})
    submit = SubmitField('Submit')

@app.route('/modify_opnote', methods = ['GET', 'POST'])
@login_required
def get_op_id():
    op_id_form = OpIdForm()
    if op_id_form.validate_on_submit():
        session['op_id'] = op_id_form.op_id.data
        return redirect(url_for('modify_opnote'))
    return render_template('op_id.html', form=op_id_form)

@app.route('/modify_opnote_process', methods = ['GET', 'POST'])
@login_required
def modify_opnote():
    op_id = session['op_id']
    sql = "SELECT indication, op_note FROM op WHERE op_id = %s"
    try:
        conn = psycopg2.connect("dbname=patient_2 user=chang password=stmmc364936 host=localhost")
        cur = conn.cursor()
    except:
        return render_template("message.html", message="Database Opening Error")
    cur.execute(sql, (op_id,))
    (indication, opnote) = cur.fetchone()
    modify_op_form = OpNoteForm()
    if modify_op_form.validate_on_submit():
        new_indication = modify_op_form.indication.data
        new_op_note = modify_op_form.opnote.data
        sql = 'UPDATE op SET indication = %s WHERE op_id = %s'
        cur.execute(sql, (new_indication, op_id))
        conn.commit()
        sql = "UPDATE op SET op_note = %s WHERE op_id = %s"
        cur.execute(sql, (new_op_note, op_id))
        conn.commit()
        cur.close()
        conn.close()
        return render_template("message.html", message="Op_note successfully modified!")
    modify_op_form.indication.data = indication
    modify_op_form.opnote.data = opnote
    return render_template('opnote.html', form=modify_op_form)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
#if __name__ == '__main__':
#    manager.run
