from flask import render_template
from flask_wtf import FlaskForm
from wtforms import StringField, RadioField, DateField, DateTimeField, HiddenField
from wtforms import TextAreaField, SelectField, SelectMultipleField, IntegerField, SubmitField, PasswordField
from wtforms.validators import InputRequired, Length
import psycopg2
from funcs import get_surgeon_tuples


#患者登録画面用のform
class PtRegisterForm(FlaskForm):
    patient_id = StringField('ID', validators=[InputRequired(), Length(min=8, max=8)])
    kanji_name = StringField('名前')
    kana_name = StringField('なまえ')
    sex = RadioField('性別', choices=[('m', '男'), ('f', '女')])
    birth_date = DateField('生年月日')
    zip_code = StringField('郵便番号')
    address = StringField('住所')
    phone_1 = StringField('電話番号１')
    phone_2 = StringField('電話番号２')
    submit = SubmitField('Submit')

#手術登録画面用のform
class OpRegisterForm(FlaskForm):
    patient_id = StringField('ID', validators=[Length(min=8, max=8)])
    kanji_name = StringField('名前')
    op_date = DateField('手術日')
    preop_dx = StringField('術前診断')
    postop_dx = StringField('術後診断')
    procedure = StringField('術式')
    start_time = DateTimeField('開始時間', format='%H:%M')
    end_time = DateTimeField('終了時間', format='%H:%M')
    surgeons = SelectMultipleField('術者', choices = get_surgeon_tuples())
    assistants = SelectMultipleField('助手', choices = get_surgeon_tuples())
    indication = TextAreaField('Indication', render_kw={"style": "height: 400px"})
    op_note = TextAreaField('Procedure', render_kw={"style": "height: 400px"})
    submit = SubmitField('Submit')

class OpDisplayForm(FlaskForm):
    op_id = IntegerField('Op ID')
    patient_id = StringField('ID')
    kanji_name = StringField('名前')
    op_date = DateField('手術日')
    preop_dx = StringField('術前診断')
    postop_dx = StringField('術後診断')
    procedure = StringField('術式')
    start_time = DateTimeField('開始時間', format='%H:%M')
    end_time = DateTimeField('終了時間', format='%H:%M')
    surgeons = SelectMultipleField('術者', choices = get_surgeon_tuples())
    assistants = SelectMultipleField('助手', choices = get_surgeon_tuples())
    indication = TextAreaField('Indication', render_kw={"style": "height: 200px"})
    op_note = TextAreaField('Procedure', render_kw={"style": "height: 400px;"})

class OpEditForm(FlaskForm):
    op_id = IntegerField('Op ID')
    patient_id = StringField('ID')
    kanji_name = StringField('名前')
    op_date = DateField('手術日')
    preop_dx = StringField('術前診断')
    postop_dx = StringField('術後診断')
    procedure = StringField('術式')
    start_time = DateTimeField('開始時間', format='%H:%M')
    end_time = DateTimeField('終了時間', format='%H:%M')
    surgeons = SelectMultipleField('術者', choices=get_surgeon_tuples())
    assistants = SelectMultipleField('助手', choices=get_surgeon_tuples())
    indication = TextAreaField('Indication', render_kw={"style": "height: 400px"})
    op_note = TextAreaField('Procedure', render_kw={"style": "height: 400px;"})
    submit = SubmitField('Submit')

#手術検索画面用のform
class OpSearchForm(FlaskForm):
    date_from = StringField('From')
    date_to = StringField('To')
    operator = StringField('術者')
    procedure = StringField('術式')
    diagnosis = StringField('診断')
    indication = StringField('indication')
    opnote = StringField('Op Note')
    submit = SubmitField('Submit')

class PatientNameForm(FlaskForm):
    patient_name = StringField('patient_name')
    submit = SubmitField('Submit')

class PatientIdForm(FlaskForm):
    patient_id = StringField('patient_id', validators=[Length(min=8, max=8)])
    submit = SubmitField('Submit')

class OpIdForm(FlaskForm):
    op_id = IntegerField('op_id')
    submit = SubmitField('Submit')

class IdForm(FlaskForm):
    op_id = IntegerField('Op_id')
    submit = SubmitField('Submit')

class MajordivForm(FlaskForm):
    major_div = SelectField('Major_div', choices = [('1', 'Brain'), ('2',
    'Spine'), ('3', 'Peripheral'), ('4', 'Others')])
    submit = SubmitField('Submit')

class PathodivForm(FlaskForm):
    patho_div = SelectField('Patho_div', choices = [('1', 'Degenerative'), ('2', 'Tumor'), ('3', 'Vascular'), ('4', 'Trauma'), ('5', 'Functional'), ('6', 'Infection'), ('7', 'Others'), ('8', 'Congenital')])
    submit = SubmitField('Submit')

class DiseaseNameForm(FlaskForm):
    disease_name = SelectField('disease_name', choices = [])
    submit = SubmitField('Submit')

class DiseaseNameWithNewForm(FlaskForm):
    disease_name = SelectField('disease_name', choices = [])
    all_disease_name = SelectField('all_disease_name', choices = [])
    new_disease_name = StringField('new_disease_name')
    submit = SubmitField('Submit')

class LocationForm(FlaskForm):
    location = SelectField('location', choices = [])
    submit = SubmitField('Submit')

class LocationWithNewForm(FlaskForm):
    location = SelectField('location', choices = [])
    all_location = SelectField('all_location', choices = [])
    new_location = StringField('new_location')
    submit = SubmitField('Submit')

class SearchKeyForm(FlaskForm):
    search_key = StringField('search_key')
    submit = SubmitField('Subit')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=20)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=6, max=20)])
    submit = SubmitField('Login')
