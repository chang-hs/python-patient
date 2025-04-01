import os, glob, psycopg2
from flask import render_template
import re

def get_surgeon_tuples():
    """Obtain data from the surgeons table
    returns a list of tuples (surgeon_id_string, surgeon_name_string)"""
    try:
        conn = psycopg2.connect("dbname=patient_2 user=chang password=stmmc364936 host=localhost")
        cur = conn.cursor()
    except:
        return []
    sql = "SELECT surgeon_id, surgeon_name FROM surgeons WHERE active = True"
    cur.execute(sql)
    return [(str(row[0]), row[1]) for row in cur]

def create_surgeon_string(surgeons):
    """From a list of surgeon_id_string, create a string of the names
    of the surgeons"""
    try:
        conn = psycopg2.connect("dbname=patient_2 user=chang password=stmmc364936 host=localhost")
        cur = conn.cursor()
    except:
        return render_template("message.html", message="Database Opening Error")
    surgeon_names = []
    sql = "SELECT surgeon_name FROM surgeons WHERE surgeon_id = %s"
    for i in surgeons:
        cur.execute(sql, (i,))
        for row in cur:
            surgeon_names.append(row[0].strip())
    return '、'.join(surgeon_names)

def file_exists(op_id, type):
	myPatientsPath = "/home/chang/Dropbox/myPatients/"
	try:
		conn = psycopg2.connect("dbname=patient_2 user=chang password=stmmc364936 host=localhost")
		cur = conn.cursor()
	except:
		return render_template("message.html", message="Database Opening Error")
	s = "SELECT patient_id, to_char(op_date, 'YYYY-MM-DD') FROM op WHERE op_id = %s"
	try:
		cur.execute(s, (op_id,))
	except:
		return render_template("message.html", message="Database Search Error")

	result = cur.fetchone()
	patient_id = result[0]
	op_date = result[1]
	pathname = ""
	if type == "edited":
		pathname = myPatientsPath + patient_id + "/" + "edited_video"
	elif type == "dicom":
		pathname = myPatientsPath + patient_id + "/" + "DICOM"
	else:
		pathname = myPatientsPath + patient_id + "/" + op_date + "-" + patient_id + "*"
		print(pathname)
	print(patient_id)
	if glob.glob(pathname):
		cur.close()
		conn.close()
		return True
	else:
		cur.close()
		conn.close()
		return False
	
def toWestDate(date):
    keys = (r'[sS]([0-9]+)[-\/]([0-9]+)[-\/]([0-9]+)',
            r'[hH]([0-9]+)[-\/]([0-9]+)[-\/]([0-9]+)',
            r'[tT]([0-9]+)[-\/]([0-9]+)[-\/]([0-9]+)',
            r'[mM]([0-9]+)[-\/]([0-9]+)[-\/]([0-9]+)')
    years = (1925, 1988, 1911, 1867)
    for i in (0,1,2,3):
        m=re.match(keys[i], date)
        if m:
            year = int(m.groups()[0]) + years[i]
            return str(year) + '-' + m.groups()[1] + '-' + m.groups()[2]
        
def convert_paragraph_text(text):
    pattern = r"\\paragraph\{(.*?)\}(.*?)((?=\\paragraph)|$)"
    paragraphs = re.findall(pattern, text, re.DOTALL)
    formatted = ""
    for i, (head, body, _) in enumerate(paragraphs):
          body = body.strip()
          formatted += f'<p class="mb-1"><span class="mx-2"><strong>{head}</strong></span>{body}</p>'
    return formatted

#print(file_exists(1860, "original"))