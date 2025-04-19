from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import create_engine
from mymodel import db_session, Patient, Op, Phone, OpSurgeon, OpAssistant
from funcs import create_surgeon_string
from datetime import datetime


def insert_patient(mydict):
    """Insert Patient and Phone into db using mydict
    mydict is a dictionay with following items
    patient_id (str),
    kanji_name (str),
    kana_name (str),
    birthdate (datetime.date),
    zipcode (str),
    address (str)
    phones (list of str)
    """

    my_patient = Patient(
        patient_id=mydict.get("patient_id"),
        kanji_name=mydict.get("kanji_name"),
        kana_name=mydict.get("kana_name"),
        birthdate=mydict.get("birthdate"),
        zipcode=mydict.get("zipcode"),
        address=mydict.get("address"),
    )

    # Patient record with the patient_id in the database
    possible_record = (
        db_session.query(Patient)
        .filter(Patient.patient_id == mydict.get("patient_id"))
        .first()
    )
    # If the patient_id is not in the database, insert the patient
    if not possible_record:
        db_session.add(my_patient)
        db_session.commit()

    temp_phones = (
        db_session.query(Phone)
        .filter(Phone.patient_id == mydict.get("patient_id"))
        .all()
    )
    cur_phones = [x.phone.strip() for x in temp_phones]

    for phone in mydict.get("phones"):
        if phone.strip() not in cur_phones:
            my_phone = Phone(patient_id=mydict.get("patient_id"), phone=phone)
            db_session.add(my_phone)
            db_session.commit()


def insert_op(myop):
    """Insert Op, OpSurgeon, OpAssistant into db using myop
    myop is a dictionary with following items
    patient_id (str)
    op_date (datetime.date)
    start_time (datetime.time)
    end_time (datetime.time)
    preop_dx (str)
    postop_dx (str)
    procedure (str)
    indication (str)
    op_note (str)
    surgeon_list (list of int)
    assistant_list (list of int)
    """

    my_op = Op(
        patient_id=myop["patient_id"],
        op_date=myop["op_date"],
        start_time=myop["start_time"],
        end_time=myop["end_time"],
        preop_dx=myop["preop_dx"],
        procedure=myop.get("procedure"),
        postop_dx=myop["postop_dx"],
        indication=myop["indication"],
        op_note=myop["op_note"],
    )
    my_op.surgeons = create_surgeon_string(myop["surgeon_list"])
    my_op.assistants = create_surgeon_string(myop["assistant_list"])

    possible_op = (
        db_session.query(Op)
        .filter(
            Op.patient_id == myop["patient_id"], Op.start_time == myop["start_time"]
        )
        .first()
    )

    # If the op is new, insert it
    # and then using the op_id of the just inserted record,
    # insert the phone numbers
    if not possible_op:
        db_session.add(my_op)
        db_session.commit()

        # Get the just inserted op record
        this_op = (
            db_session.query(Op)
            .filter(
                Op.patient_id == myop.patient_id,
                Op.op_date
                == (datetime.strptime(myop.op_date), "%H:%M").date(),
                Op.start_time
                == (datetime.strptime(myop.start_time, "%H:%M").time()),
            ) .first()
        )
        op_id = this_op.op_id

        for model, mylist in [
            (OpSurgeon, myop.surgeon_list),
            (OpAssistant, myop.assistant_list),
        ]:
            for i in mylist:
                my_object = model(op_id=op_id, surgeon_id=i)
                db_session.add(my_object)
                db_session.commit()
