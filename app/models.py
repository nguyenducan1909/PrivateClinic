from datetime import datetime
from enum import Enum as UserEnum

from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship

from app import db, app


class BaseModel(db.Model):
    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True)


class UserRole(UserEnum):
    DOCTOR = 'doctor'
    PATIENT = 'patient'
    STAFF = 'staff'
    ADMIN = 'admin'


class User(BaseModel, UserMixin):
    __tablename__ = 'user'


    name = Column(String(45), nullable=True)
    dob = Column(DateTime, nullable=False)
    phone_number = Column(String(15), nullable=False)
    avatar = Column(String(255), nullable=True)
    username = Column(String(45), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    active = Column(Boolean, default=True)

    staff = relationship('Staff', backref='user', uselist=False)
    doctor = relationship('Doctor', backref='user', uselist=False)
    patient = relationship('Patient', backref='user', uselist=False)
    admin = relationship('Admin', backref='user', uselist=False)


class Staff(User):
    __tablename__ = 'staff'

    user_id = Column(Integer, ForeignKey('user.id'), primary_key=True)

    # Quan hệ 1-n với các lớp
    appointments = relationship('Appointment', backref='staff', lazy=True)
    receipts = relationship('Receipt', backref='staff', lazy=True)


class Doctor(User):
    __tablename__ = 'doctor'

    user_id = Column(Integer, ForeignKey('user.id'), primary_key=True)

    # Quan hệ 1-n với các lớp
    appointments = relationship('Appointment', backref='doctor', lazy=True)
    medical_visits = relationship('MedicalVisit', backref='doctor', lazy=True)


class Patient(User):
    __tablename__ = 'patient'

    user_id = Column(Integer, ForeignKey('user.id'), primary_key=True)

    # Quan hệ 1-n với các lớp
    appointments = relationship('Appointment', backref='patient', lazy=True)
    medical_visits = relationship('MedicalVisit', backref='patient', lazy=True)
    receipts = relationship('Receipt', backref='patient', lazy=True)


class Admin(User):
    __tablename__ = 'admin'

    user_id = Column(Integer, ForeignKey('user.id'), primary_key=True)

    # Quan hệ 1-n với các lớp
    reports = relationship('Report', backref='admin', lazy=True)
    units = relationship('Unit', backref='admin', lazy=True)

    # Quan hệ n-n với các lớp
    medicines = relationship('Medicine', secondary='admin_medicine', backref='admins',
                             lazy=True)

    def __str__(self):
        return super().name

class AdminMedicine(BaseModel):
    __tablename__ = 'admin_medicine'

    admin_id = Column(Integer, ForeignKey('admin.user_id'), primary_key=True)
    medicine_id = Column(Integer, ForeignKey('medicine.id'), primary_key=True)


class Appointment(BaseModel):
    __tablename__ = 'appointment'

    date = Column(DateTime, nullable=False, default=datetime.now())
    status = Column(Boolean, default=False)

    # Các khóa ngoại
    doctor_id = Column(Integer, ForeignKey('doctor.user_id'), nullable=False)
    staff_id = Column(Integer, ForeignKey('staff.user_id'), nullable=False)
    patient_id = Column(Integer, ForeignKey('patient.user_id'), nullable=False)

    # Quan hệ 1-1 với các lớp
    medical_visit = relationship('MedicalVisit', backref='appointment', uselist=False)


class MedicalVisit(BaseModel):
    __tablename__ = 'medical_visit'

    date = Column(DateTime, nullable=False, default=datetime.now())
    diagnosis = Column(String(255), nullable=False)
    symptoms = Column(String(255), nullable=False)

    # Các khóa ngoại
    appointment_id = Column(Integer, ForeignKey('appointment.id'), nullable=False)

    doctor_id = Column(Integer, ForeignKey('doctor.user_id'), nullable=False)
    patient_id = Column(Integer, ForeignKey('patient.user_id'), nullable=False)

    # Quan hệ 1-1 với các lớp
    receipt = relationship('Receipt', backref='medical_visit', lazy=True, uselist=False)

    # Quan hệ n-n với các lớp
    medicine_mv = relationship('Medicine', secondary='medicalvisit_medicine', backref='medical_visit',
                               lazy=True)


# Lớp Medicine: Đại diện thuốc trong hệ thống
class Medicine(BaseModel):
    __tablename__ = 'medicine'

    # Các cột trong bảng Medicine
    name = Column(String(45), nullable=False)

    # Quan hệ n-n với các lớp
    # units = relationship('Unit', secondary='medicine_unit', backref='medicine',
    #                     lazy=True)
    units = relationship('MedicineUnit',backref='medicine',
                        lazy=True)

    medicalVisit_Medicines = relationship('MedicalVisit', secondary='medicalvisit_medicine', backref='medicine',
                                          lazy=True)


# Lớp MedicalVisit_Medicine: Bảng trung gian quản lý thuốc sử dụng trong lần khám bệnh
class MedicalVisit_Medicine(db.Model):
    __tablename__ = 'medicalvisit_medicine'

    medical_visit_id = Column(Integer, ForeignKey('medical_visit.id'), primary_key=True)
    medicine_id = Column(Integer, ForeignKey('medicine.id'), primary_key=True)

    # Các cột trong bảng MedicalVisit_Medicine
    quantity = Column(Integer, nullable=False)
    usage_instructions = Column(String(255), nullable=True)


class Unit(BaseModel):
    __tablename__ = 'unit'

    name = Column(String(45), nullable=False)
    admin_id = db.Column(Integer, ForeignKey('admin.user_id'))

    # medicines = relationship('Medicine', secondary='medicine_unit', backref='unit', lazy=True)
    medicines = relationship('MedicineUnit', backref='unit', lazy=True)

    def __str__(self):
        return self.name
    # def __repr__(self):
    #     return self.name

class MedicineUnit(db.Model):
    __tablename__ = 'medicine_unit'

    quantity = Column(Integer, nullable=False)
    price = Column(Integer, nullable=False)

    unit_id = Column(Integer, ForeignKey('unit.id'), primary_key=True)
    medicine_id = Column(Integer, ForeignKey('medicine.id'), primary_key=True)


class Receipt(BaseModel):
    __tablename__ = 'receipt'

    date = Column(DateTime, nullable=False, default=datetime.now())
    # total_money = Column(Integer, nullable=False)
    medical_examination_money = Column(Integer, nullable=False)
    # medicine_money = Column(Integer, nullable=False)

    # Các khóa ngoại
    medical_visit_id = Column(Integer, ForeignKey('medical_visit.id'), nullable=False)
    staff_id = Column(Integer, ForeignKey('staff.user_id'), nullable=False)
    patient_id = Column(Integer, ForeignKey('patient.user_id'), nullable=False)


class Policy(BaseModel):
    __tablename__ = 'policy'

    max_patients_per_day = Column(Integer, nullable=False)
    medical_examination_fee = Column(Integer, nullable=False)
    max_medicine_types = Column(Integer, nullable=False)

    admin_id = Column(Integer, ForeignKey('admin.user_id'), nullable=False)


class Report(BaseModel):
    __tablename__ = 'report'

    content = Column(String(255), nullable=False)
    type = Column(String(45), nullable=False)
    month = Column(Integer, nullable=False)

    # Các khóa ngoại
    admin_id = Column(Integer, ForeignKey('admin.user_id'), nullable=False)


if __name__ == '__main__':
    with app.app_context():
        # db.drop_all()

        db.create_all()
