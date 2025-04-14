from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from typing import List
from typing import Optional
from sqlalchemy import Column, Integer, Boolean, CHAR, String, Date, Time, Text, ForeignKey, Table
from sqlalchemy import create_engine
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.orm import scoped_session, sessionmaker
import datetime
import sqlalchemy as sa
from flask_login import UserMixin


class Base(DeclarativeBase):
    pass

engine = create_engine('postgresql+psycopg2://chang:stmmc364936@localhost/patient_2')
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))

Base.query = db_session.query_property()

class Patient(Base):
    __tablename__ = 'patient'

    patient_id: Mapped[str] = mapped_column(CHAR(8), primary_key=True)
    kanji_name: Mapped[str] = mapped_column(String(30))
    kana_name: Mapped[str] = mapped_column(String(40), nullable=True)
    sex: Mapped[str] = mapped_column(CHAR(1), nullable=True)
    birthdate: Mapped[datetime.date] = mapped_column(Date, nullable=True)
    zipcode: Mapped[str] = mapped_column(CHAR(8), nullable=True)
    address: Mapped[str] = mapped_column(String(100), nullable=True)
    phones: Mapped[List["Phone"]] = relationship(back_populates="patient")
    ops: Mapped[List["Op"]] = relationship(back_populates="patient", order_by="Op.op_date")
    memo: Mapped[str] = mapped_column(Text, nullable=True)
    cold: Mapped[bool] = mapped_column(Boolean, nullable=True)
    listhesis: Mapped[bool] = mapped_column(Boolean, nullable=True)

    def __repr__(self) -> str:
        return f"Patient(id={self.patient_id!r}, name={self.kanji_name!r})"

class Op(Base):
    __tablename__ = 'op'

    op_id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[str] = Column(CHAR(8), ForeignKey("patient.patient_id"), nullable=False)
    op_date = Column(Date)
    start_time: Mapped[datetime.time] = mapped_column(Time, nullable=True)
    end_time: Mapped[datetime.time] = mapped_column(Time, nullable=True)
    preop_dx: Mapped[str] = mapped_column(String(100), nullable=True)
    postop_dx: Mapped[str] = mapped_column(String(100), nullable=True)
    procedure: Mapped[str] = mapped_column(Text, nullable=True)
    op_note: Mapped[str] = mapped_column(Text, nullable=True)
    emergency: Mapped[bool] = Column(Boolean, default=False)
    surgeons: Mapped[str] = mapped_column(String(40), nullable=True)
    assistants: Mapped[str] = mapped_column(String(40), nullable=True)
    indication: Mapped[str] = mapped_column(Text, nullable=True)
    coldp: Mapped[bool] = mapped_column(Boolean, nullable=True)
    category: Mapped[str] = mapped_column(String(40), nullable=True)
    decoy: Mapped[str] = mapped_column(Text, nullable=True)
    patient: Mapped["Patient"] = relationship(back_populates="ops")
    diags = relationship("Diagnosis", secondary='op_diag', overlaps='ops')
    surgeon_list = relationship("Surgeon", secondary='op_surgeon')
    assistant_list = relationship("Surgeon", secondary='op_assistant')

    def __repr__(self) -> str:
        return f"Op(id={self.op_id!r}, op_date={self.op_date!r}, procedure={self.procedure!r}"

class Diagnosis(Base):
    __tablename__ = 'diagnosis'

    disease_id: Mapped[int] = mapped_column(primary_key=True)
    disease_name: Mapped[str] = mapped_column(String(40), nullable=True)
    major_div_id: Mapped[int] = mapped_column(ForeignKey("majordiv.major_div_id"))
    patho_div_id: Mapped[int] = mapped_column(ForeignKey("pathodiv.patho_div_id"))
    location_id: Mapped[int] = mapped_column(ForeignKey("location.location_id"))
    disease_name_id: Mapped[int] = mapped_column(ForeignKey("disease_name.disease_name_id"), nullable=True)
    location: Mapped[str] = mapped_column(String(30), nullable=True)
    major_div: Mapped[str] = mapped_column(String(15), nullable=True)
    patho_div: Mapped[str] = mapped_column(CHAR(15), nullable=True)
    ops = relationship("Op", secondary='op_diag', order_by='Op.op_date, Op.op_id', overlaps='diags')

    __table_args__ = (
        sa.UniqueConstraint('major_div_id', 'patho_div_id', 'location_id', 'disease_name_id', name='diagnosis_multi_unique'),
    )

    def __repr__(self) -> str:
        return f"Diagnosis(id={self.disease_id!r}, disease_name={self.disease_name!r})"

class OpDiag(Base):
    __tablename__ = 'op_diag'
    op_diag_id: Mapped[int] = mapped_column(primary_key=True)
    op_id: Mapped[int] = mapped_column(ForeignKey("op.op_id"))
    disease_id: Mapped[int] = mapped_column(ForeignKey("diagnosis.disease_id"))

class DiseaseName(Base):
    __tablename__ = 'disease_name'
    disease_name_id: Mapped[int] = mapped_column(primary_key=True)
    disease_name: Mapped[str] = mapped_column(String(40))

class MajorDiv(Base):
    __tablename__ = 'majordiv'
    major_div_id: Mapped[int] = mapped_column(primary_key=True)
    major_div: Mapped[str] = mapped_column(CHAR(15), unique=True)

class PathoDiv(Base):
    __tablename__ = 'pathodiv'
    patho_div_id: Mapped[int] = mapped_column(primary_key=True)
    patho_div: Mapped[str] = mapped_column(CHAR(15), unique=True)

class Location(Base):
    __tablename__ = 'location'
    location_id: Mapped[int] = mapped_column(primary_key=True)
    location: Mapped[str] = mapped_column(String(30), unique=True)

class Phone(Base):
    __tablename__ = 'phone'
    id: Mapped[int] = mapped_column(primary_key=True)
    phone: Mapped[str] = mapped_column(CHAR(20), nullable=True)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patient.patient_id"))
    patient = relationship("Patient", back_populates="phones")

class Surgeon(Base):
    __tablename__ = 'surgeons'
    surgeon_id: Mapped[int] = mapped_column(primary_key=True)
    surgeon_name: Mapped[str] = mapped_column(CHAR(15), unique=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=True)

class OpSurgeon(Base):
    __tablename__ = 'op_surgeon'
    op_surgeon_id: Mapped[int] = mapped_column(primary_key=True)
    op_id: Mapped[int] = mapped_column(ForeignKey("op.op_id"))
    surgeon_id: Mapped[int] = mapped_column(ForeignKey("surgeons.surgeon_id"))

    __table_args__ = (
        sa.UniqueConstraint('op_id', 'surgeon_id', name='op_surgeon_op_id_surgeon_id_key'),
    )

    def __repr__(self):
        return (
            f'OpSurgeon(op_id: {self.op_id}, surgeon_id: {self.surgeon_id})'
        )
               


class OpAssistant(Base):
    __tablename__ = 'op_assistant'
    id: Mapped[int] = mapped_column(primary_key=True)
    op_id: Mapped[int] = mapped_column(ForeignKey("op.op_id"))
    surgeon_id: Mapped[int] = mapped_column(ForeignKey("surgeons.surgeon_id"))

    __table_args__ = (
        sa.UniqueConstraint('op_id', 'surgeon_id',
                            name='op_assistant_op_id_surgeon_id_key'),
    )

    def __repr__(self):
        return (
            f'OpAssistant(op_id: {self.op_id}, surgeon_id: {self.surgeon_id})'
        )

class User(Base, UserMixin):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String)
    password: Mapped[str] = mapped_column(String)

    def __repr__(self) -> str:
        return f"User {self.username}"
