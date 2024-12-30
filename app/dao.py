import hashlib
from sqlalchemy import func, extract
from models import User, UserRole, Unit, MedicineUnit, MedicalVisit_Medicine, Receipt, MedicalVisit, Medicine, Doctor, \
    Staff, Admin, Patient, Policy
from app import db, app
from flask_login import login_user
from sqlalchemy import or_

from flask import session


def check_login(username, password, role=UserRole.PATIENT):
    if username and password:
        password = hashlib.md5(password.strip().encode('utf-8')).hexdigest()
        return User.query.filter(User.username == username.strip(), User.password.__eq__(password),
                                 User.role.__eq__(role)).first()


def get_user_by_id(user_id):
    return User.query.get(user_id)


# Nguyễn Trung Quân

# Hàm lấy thông tin người dùng theo ID
def get_user_by_id(user_id):
    return User.query.get(user_id)


def get_user_by_username(username):
    return User.query.filter(User.username == username).first()


def load_user(user_id):
    user = User.query.filter_by(id=user_id).first()
    if user:
        user_data = {
            'user_id': user.id,
            'name': user.name,
            'dob': user.dob,
            'phone_number': user.phone_number,
            'avatar': user.avatar,
            'username': user.username,
            'role': user.role.name,
            'active': user.active
        }
        session.update(user_data)
    return None


# Hàm xác thực người dùng bằng tên đăng nhập và mật khẩu
def authenticate_user(username, password):
    user = get_user_by_username(username)
    password = str(hashlib.md5(password.encode('utf-8')).hexdigest())

    if not user:
        return False, None, "Tên đăng nhập không tồn tại"

    if user.password != password:
        return False, None, "Mật khẩu không đúng"

    return True, user, "Đăng nhập thành công"


# Hàm mã bí mật
def determine_user_role(secret_code):
    if secret_code == "codeadmin123":
        return UserRole.ADMIN
    elif secret_code == "codedoctor123":
        return UserRole.DOCTOR
    elif secret_code == "codestaff123":
        return UserRole.STAFF
    else:
        return UserRole.PATIENT  # Mặc định là vai trò bệnh nhân nếu không có mã


def add_user_to_role(user_id, role):
    if role == UserRole.STAFF:
        staff = Staff(user_id=user_id)
        db.session.add(staff)
    elif role == UserRole.ADMIN:
        admin = Admin(user_id=user_id)
        db.session.add(admin)
    elif role == UserRole.DOCTOR:
        doctor = Doctor(user_id=user_id)
        db.session.add(doctor)
    else:
        patient = Patient(user_id=user_id)
        db.session.add(patient)


# Hàm đăng ký người dùng mới
def register_user(username, password, name, dob, avatar, phone_number, secret_code=None):
    # Kiểm tra thông tin đầy đủ
    if not all([username, password, name, dob, phone_number, avatar]):
        return False, None, "Vui lòng điền đầy đủ thông tin đăng ký"

    # Kiểm tra tên đăng nhập đã tồn tại
    existing_user = User.query.filter(User.username == username).first()
    if existing_user:
        return False, None, "Tên đăng nhập đã tồn tại trong hệ thống"

    try:
        # Xác định role dựa trên secret code
        role = determine_user_role(secret_code)
        password = str(hashlib.md5(password.encode('utf-8')).hexdigest())

        # Tạo user mới
        new_user = User(
            username=username,
            password=password,
            name=name,
            dob=dob,
            avatar=avatar,
            phone_number=phone_number,
            role=role,
            active=True
        )

        # Thêm user vào database
        db.session.add(new_user)
        db.session.commit()

        return True, new_user, "Đăng ký tài khoản thành công"

    except Exception as e:
        db.session.rollback()
        return False, None, f"Lỗi trong quá trình đăng ký: {str(e)}"


def load_users_by_role(role):
    if not role:
        return []

    users = User.query.filter(
        User.role == role,
        User.active == True
    ).all()

    return users


def get_user_id_by_username(username):
    # Tìm kiếm user theo username
    user = User.query.filter_by(username=username).first()

    # Kiểm tra xem user có tồn tại không và trả về id nếu có, nếu không trả về None
    if user:
        return user.id
    return None


def get_max_patients_per_day():
    policy = Policy.query.first()

    if policy:
        return policy.max_patients_per_day
    else:
        return 40


def get_user_id_by_username(username):
    user = User.query.filter_by(username=username).first()
    if user:
        return user.id
    return None


def get_current_staff():
    staff_id = session.get('user_id')  # Giả sử user_id trong session là ID của nhân viên
    if not staff_id:
        return None

    return Staff.query.filter_by(id=staff_id).first()


# Quân end =====================================================

# Nguyễn Thanh Hoàng
def stats_monthly_revenue(month, year):
    subquery_patient_count = db.session.query(
        func.date(MedicalVisit.date).label('date'),
        func.count(func.distinct(MedicalVisit.patient_id)).label('patient_count')
    ).filter(
        func.extract('month', MedicalVisit.date) == month,
        func.extract('year', MedicalVisit.date) == year
    ).group_by(
        func.date(MedicalVisit.date)
    ).subquery()

    daily_stats = db.session.query(
        func.date(MedicalVisit.date).label('date'),
        func.sum(
            (MedicalVisit_Medicine.quantity * MedicineUnit.price) + Receipt.medical_examination_money
        ).label('daily_revenue'),
        subquery_patient_count.c.patient_count  # Kết hợp số lượng bệnh nhân từ subquery
    ).join(
        MedicalVisit_Medicine, MedicalVisit.id == MedicalVisit_Medicine.medical_visit_id
    ).join(
        MedicineUnit, MedicalVisit_Medicine.medicine_id == MedicineUnit.medicine_id
    ).join(
        Receipt, MedicalVisit.id == Receipt.medical_visit_id
    ).outerjoin(  # Join subquery để lấy patient_count
        subquery_patient_count, subquery_patient_count.c.date == func.date(MedicalVisit.date)
    ).filter(
        func.extract('month', MedicalVisit.date) == month,
        func.extract('year', MedicalVisit.date) == year
    ).group_by(
        func.date(MedicalVisit.date),
        subquery_patient_count.c.patient_count
    ).all()

    total_revenue = sum([stat.daily_revenue for stat in daily_stats])

    stats_with_percentage = []
    for stat in daily_stats:
        percentage = (stat.daily_revenue / total_revenue * 100) if total_revenue > 0 else 0
        stats_with_percentage.append({
            "date": stat.date,
            "patient_count": stat.patient_count or 0,  # Tránh giá trị None nếu không có bệnh nhân
            "daily_revenue": stat.daily_revenue,
            "percentage": percentage
        })

    return {
        "month": month,
        "year": year,
        "total_revenue": total_revenue,
        "daily_stats": stats_with_percentage
    }


def get_medicine_usage_report(month=None, year=None):
    # Truy vấn thông tin sử dụng thuốc
    query = db.session.query(
        Medicine.name.label('medicine'),
        Unit.name.label('unit'),
        func.sum(MedicalVisit_Medicine.quantity).label('quantity'),
        func.count(MedicalVisit_Medicine.medical_visit_id).label('count_use')
    ).join(
        MedicalVisit_Medicine, MedicalVisit_Medicine.medicine_id == Medicine.id
    ).join(
        MedicineUnit, MedicineUnit.medicine_id == Medicine.id
    ).join(
        Unit, Unit.id == MedicineUnit.unit_id
    ).join(
        MedicalVisit, MedicalVisit.id == MedicalVisit_Medicine.medical_visit_id
    )

    # Lọc theo tháng và năm (nếu có)
    if year:
        query = query.filter(extract('year', MedicalVisit.date) == year)
    if month:
        query = query.filter(extract('month', MedicalVisit.date) == month)

    # Gom nhóm theo thuốc và đơn vị tính
    query = query.group_by(Medicine.id, Medicine.name, Unit.name)

    # Lấy dữ liệu
    report_data = query.all()

    # Chuyển dữ liệu thành danh sách dictionary
    report_list = [
        {
            "Thuốc": row.medicine,
            "Đơn vị tính": row.unit,
            "Số lượng": row.quantity,
            "Số lần dùng": row.count_use
        }
        for row in report_data
    ]

    return report_list


def get_clinic_revenue():
    # Tính tổng tiền thuốc
    total_medicine_revenue = db.session.query(
        func.sum(MedicalVisit_Medicine.quantity * MedicineUnit.price).label('total_medicine_revenue')
    ).join(
        MedicineUnit, MedicalVisit_Medicine.medicine_id == MedicineUnit.medicine_id
    ).first()  # Trả về 0 nếu không có dữ liệu thuốc

    # Tính tổng tiền khám
    total_examination_revenue = db.session.query(
        func.sum(Receipt.medical_examination_money).label('total_examination_revenue')
    ).first()  # Trả về 0 nếu không có hóa đơn

    # Tổng doanh thu phòng khám
    total_revenue = total_medicine_revenue + total_examination_revenue

    return total_revenue
# =================================================
def add_MedicalVisit(name, date, symptoms, diagnosis, medicine, unit, quantity, usage):
    new_visit = MedicalVisit(
        name=name,
        date=date,
        symptoms=symptoms,
        diagnosis=diagnosis,
        medicine=medicine,
        unit=unit,
        quantity=int(quantity),
        usage=usage
    )
    db.session.add(new_visit)
    db.session.commit()