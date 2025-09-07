import yaml
import re
import sys
import glob
import os
from datetime import datetime
from sqlalchemy import and_
from mymodel import Patient, Op, OpSurgeon, OpAssistant, Phone, db_session

sys.path.append("/home/chang/Dropbox/Projects/flasky")


def wrap_time_stamp(content):
    """
    Wrap the content of start time: or end time with double quotation marks
    """
    result = re.sub(r'(?i)(start time|end time):\s*([0-9]{1,2}:[0-9]{2})',
                    r'\1: "\2"', content)
    return result

def conv_paragraph_head(content):
    """
    Convert markdown headers ## into latex paragraph headers
    """
    result = re.sub(r'^##\s+(.*)', r'\\paragraph{\1}',
                    content, flags=re.MULTILINE)
    return result

def parse_opnote(filename):
    """
    Parse an opnote file and returns a dictionary with the yaml items

    Input: filename (string) opnote file name
    Output: dict with yaml item keys both for patient and op
    """
    yaml_lines = []
    indication_lines = []
    opnote_lines = []
    in_yaml = False
    in_indication = False
    in_opnote = False
    with open(filename) as f:
        for line in f:
            if line.strip() == '---':
                in_yaml = not in_yaml
                continue
            if line.strip() == '# Indication':
                in_indication = not in_indication
                continue
            if line.strip() == '# Procedure':
                in_indication = not in_indication
                in_opnote = not in_opnote
                continue
            if in_yaml:
                yaml_lines.append(line)
            elif in_indication:
                indication_lines.append(line)
            elif in_opnote:
                opnote_lines.append(line)
    yaml_content = wrap_time_stamp("".join(yaml_lines))
    data = yaml.safe_load(yaml_content)
    indication = "".join(indication_lines)
    opnote = "".join(opnote_lines)
    data["indication"] = conv_paragraph_head(indication)
    data["opnote"] = conv_paragraph_head(opnote)
    return data

def conv_data_to_patient_phone_op(data):
    """
    Convert a dictionary with patient and op data into Patient and Op
    
    Input:
        data: dictionary with both patient and op data

    Output:
        (Patient, Phone, Op)
    """
    patient = Patient(patient_id=str(data["id"]),
                      kanji_name=data["name"],
                      kana_name=data["kana"],
                      birthdate = data["birthdate"],
                      zipcode = data["zipcode"],
                      address = data["address"])
    phone = Phone(patient_id = data["id"],
                  phone = data["phone"])
    op = Op(patient_id = data["id"],
            op_date = data["opdate"],
            start_time = data["start time"],
            end_time = data["end time"],
            preop_dx = data["diag"],
            postop_dx = "do",
            procedure = data["procedure"],
            emergency = False,
            surgeons = data["surgeon"],
            assistants = data["assistant"],
            indication = data["indication"],
            op_note = data["opnote"])
    return patient, phone, op

def conv_namestring_to_numlist(surgeon_name_string):
    """
    Convert surgeon name string into a list of surgeon numbers

    Input
        surgeon_name_string: a string of assistant names separated with '、'

    Output
        a list of surgeon numbers
    """
    names = surgeon_name_string.split('、')
    result = []
    for name in names:
        if name == '張':
            result.append(3)
        elif name == '岡本':
            result.append(130)
        elif name == '井上':
            result.append(133)
        elif name == '佐野':
            result.append(112)
        elif name == '畑佐':
            result.append(131)
        elif name == '岩佐':
            result.append(134)
    return result
            

def get_opfile_names(date_1, date_2, directory):
    """
    Glob opnote filenames from date_1 to date_2 in the directory
    
    Input:
        date_1 (Date): from date
        date_2 (Date): to date
        directory: directory in which the search is performed
    """
    

    start_date = datetime.strptime(date_1, "%Y-%m-%d")
    end_date = datetime.strptime(date_2, "%Y-%m-%d")

    if not directory.endswith('/'):
        directory = directory + '/'

    files = glob.glob(os.path.join(directory + '*.md'))
    date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}")
    filtered_files = []
    for f in files:
        if date_pattern.match(os.path.basename(f)):
            file_date_str = os.path.basename(f)[:10]
            file_date = datetime.strptime(file_date_str, "%Y-%m-%d")
            if start_date <= file_date <= end_date:
                filtered_files.append(f)

    sorted_files = sorted(filtered_files)
    return sorted_files


def incorporate_opnote(start_date, end_date, my_dir):
    mylist = get_opfile_names(start_date, end_date, my_dir)
    for f in mylist:
        result = parse_opnote(f)

        patient, phone, op = conv_data_to_patient_phone_op(result)

        existing_patient = Patient.query.filter(Patient.patient_id == patient.patient_id).first()
        if not existing_patient: # if the patient does not exist in DB
            print(f"patient {patient.kanji_name} does not exist. Adding")
            db_session.add(patient)
            db_session.commit()

        existing_op = Op.query.filter(and_(Op.patient_id == patient.patient_id,
                                    Op.op_date == result["opdate"])).first()
        if not existing_op: # if the op does not exist in DB
            print(result["opdate"])
            print("op does not exist. Adding")
            try:
                db_session.add(op)
                db_session.commit()
            except:
                print("exception occurred")
            entered_op = Op.query.filter(and_(Op.patient_id == patient.patient_id,
                                    Op.op_date == result["opdate"])).first()
            entered_op_id = entered_op.op_id

        if existing_op:
            referred_op_id = existing_op.op_id
        else:
            referred_op_id = entered_op_id.op_id
            
        for role in ["surgeon", "assistant"]:
            id_list = conv_namestring_to_numlist(result[role])
            my_object = None
            for i in id_list:
                if role == "surgeon":
                    existing_opsurgeon = OpSurgeon.query.filter(OpSurgeon.op_id == referred_op_id,
                                                                OpSurgeon.surgeon_id == i).first()
                    if existing_opsurgeon:
                        break
                    else:
                        my_object = OpSurgeon(op_id=referred_op_id, surgeon_id=i)
                else:
                    existing_opassistant = OpAssistant.query.filter(OpAssistant.op_id == referred_op_id,
                                                                    OpAssistant.surgeon_id == i).first()
                    if existing_opassistant:
                        break
                    else:
                        my_object = OpAssistant(op_id=referred_op_id, surgeon_id=i)
                if my_object:
                    print(f"op-{role} does not exist. Adding")
                    try:
                        db_session.add(my_object)
                        db_session.commit()
                    except:
                        print("surgeon name insertion problem")

        
        existing_phone = Phone.query.filter(Phone.patient_id == patient.patient_id).first()
        if not existing_phone: # if the phone does not exist in DB
            print("The phone does not exist. Adding")
            db_session.add(phone)
            db_session.commit()
