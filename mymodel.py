from flask_sqlalchemy import SQLAlchemy
from typing import List
from typing import Optional
from sqlalchemy import Column, Integer, Boolean, String, Date, Time, Text, ForeignKey, Table
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from patient.py import app

db = SQLAlchemy(app)
class Patient(db.Model):
    __tablename__ = 'patient'

    patient_id: Mapped[str] = mapped_column(String(8), primary_key=True)
    kanji_name: Mapped[str] = mapped_column(String(30))
    kana_name: Mapped[str] = mapped_column(String(40))
    sex: Mapped[str] = mapped_column(String(1))
    birthdate: Mapped[datetime.date] = mapped_column(Date)
    zipcode: Mapped[str] = mapped_column(String(8))
    address: Mapped[str] = mapped_column(String(100))
    phones: Mapped[List["Phone"]] = relationship(back_populates="patient")
    ops: Mapped[List["Op"]] = relationship(back_populates="patient")

    def __repr__(self) -> str:
        return f"Patient(id={self.patient_id!r}, name={self.kanji_name!r})"

class Op(db.Model):
    __tablename__ = 'op'

    op_id: Mapped[str] = mapped_column(primary_key=True)
    patient_id: Mapped[str] = Column(String(8), ForeignKey("patient.patient_id"))
    op_date = Column(Date)
    start_time: Mapped[datetime.time] = mapped_column(Time)
    end_time: Mapped[datetime.time] = mapped_column(Time)
    preop_dx: Mapped[str] = mapped_column(String(100))
    postop_dx: Mapped[str] = mapped_column(String(100))
    procedure: Mapped[str] = mapped_column(Text)
    op_note: Mapped[str] = mapped_column(Text)
    emergency: Mapped[bool] = Column(Boolean)
    surgeons: Mapped[str] = mapped_column(String(40))
    assistants: Mapped[str] = mapped_column(String(40))
    indication: Mapped[str] = mapped_column(Text)
    patient: Mapped["Patient"] = relationship(back_populates="ops")
    diags = relationship("Diagnosis", secondary='op_diag')
    surgeon_list = relationship("Surgeon", secondary='op_surgeon')

    def __repr__(self) -> str:
        return f"Op(id={self.op_id!r}, op_date={self.op_date!r}, procedure={self.procedure!r}"

class Diagnosis(db.Model):
    __tablename__ = 'diagnosis'

    disease_id: Mapped[int] = mapped_column(primary_key=True)
    disease_name: Mapped[str] = mapped_column(String(40))
    major_div_id: Mapped[int] = mapped_column(ForeignKey("majordiv.major_div_id"))
    patho_div_id: Mapped[int] = mapped_column(ForeignKey("pathodiv.patho_div_id"))
    location_id: Mapped[int] = mapped_column(ForeignKey("location.location_id"))
    disease_name_id: Mapped[int] = mapped_column(ForeignKey("disease_name.disease_name_id"))
    location: Mapped[str] = mapped_column(String(30))
    major_div: Mapped[str] = mapped_column(String(15))
    ops = relationship("Op", secondary='op_diag', order_by='Op.op_date, Op.op_id')

    def __repr__(self) -> str:
        return f"Diagnosis(id={self.disease_id!r}, disease_name={self.disease_name!r})"

class OpDiag(db.Model):
    __tablename__ = 'op_diag'
    op_diag_id: Mapped[int] = mapped_column(primary_key=True)
    op_id: Mapped[int] = mapped_column(ForeignKey("op.op_id"))
    disease_id: Mapped[int] = mapped_column(ForeignKey("diagnosis.disease_id"))

class DiseaseName(db.Model):
    __tablename__ = 'disease_name'
    disease_name_id: Mapped[int] = mapped_column(primary_key=True)
    disease_name: Mapped[str] = mapped_column(String(40))

class MajorDiv(db.Model):
    __tablename__ = 'majordiv'
    major_div_id: Mapped[int] = mapped_column(primary_key=True)
    major_div: Mapped[str] = mapped_column(String(15))

class PathoDiv(db.Model):
    __tablename__ = 'pathodiv'
    patho_div_id: Mapped[int] = mapped_column(primary_key=True)
    patho_div: Mapped[str] = mapped_column(String(15))

class Location(db.Model):
    __tablename__ = 'location'
    location_id: Mapped[int] = mapped_column(primary_key=True)
    location: Mapped[str] = mapped_column(String(30))

class Phone(db.Model):
    __tablename__ = 'phone'
    id: Mapped[int] = mapped_column(primary_key=True)
    phone: Mapped[str] = mapped_column(String(20))
    patient_id: Mapped[str] = mapped_column(ForeignKey("patient.patient_id"))
    patient = relationship("Patient", back_populates="phones")

class Surgeon(db.Model):
    __tablename__ = 'surgeons'
    surgeon_id: Mapped[int] = mapped_column(primary_key=True)
    surgeon_name: Mapped[str] = mapped_column(String(15))
    active: Mapped[bool] = mapped_column(Boolean)

class OpSurgeon(db.Model):
    __tablename__ = 'op_surgeon'
    op_surgeon_id: Mapped[int] = mapped_column(primary_key=True)
    op_id: Mapped[int] = mapped_column(ForeignKey("op.op_id"))
    surgeon_id: Mapped[int] = mapped_column(ForeignKey("surgeons.surgeon_id"))


with app.app_context():
    db.create_all()