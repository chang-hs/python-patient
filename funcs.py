import os, glob, psycopg2
from flask import render_template

def file_exists(op_id, type):
	myPatientsPath = "/home/chang/Dropbox/myPatients/"
	try:
		conn = psycopg2.connect("dbname=patient host=localhost")
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

#print(file_exists(1860, "original"))