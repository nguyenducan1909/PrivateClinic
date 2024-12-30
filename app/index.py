import re
import threading

from flask import render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from flask_sqlalchemy.model import Model
from werkzeug import Client

from app import app, login_manager, db, dao
from models import UserRole, Appointment, Doctor, User, Staff, Patient, MedicalVisit, MedicalVisit_Medicine
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash


# Nguyên Trung Quân
@app.context_processor
def inject_session():
    return dict(session=session)


@app.route('/')
def index():
    return render_template('index.html')


@login_manager.user_loader
def load_user(user_id):
    return dao.get_user_by_id(user_id)


@app.route('/admin-login', methods=['POST'])
def admin_signin():
    username = request.form.get('username')
    password = request.form.get('password')

    user = dao.check_login(username=username, password=password, role=UserRole.ADMIN)
    if user:
        login_user(user=user)

    return redirect('/admin')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        success, user, message = dao.authenticate_user(username, password)

        if success:
            login_user(user)

            session['user_id'] = user.id
            session['name'] = user.name
            session['avatar'] = user.avatar
            session['role'] = user.role.name
            session['phone_number'] = user.phone_number

            # Redirect based on role
            if user.role == UserRole.ADMIN:
                return redirect(url_for('admin.index'))
            elif user.role == UserRole.DOCTOR:
                return redirect(url_for('doctor'))
            elif user.role == UserRole.STAFF:
                return redirect(url_for('staff'))
            else:  # PATIENT
                return redirect(url_for('patient'))

        flash(message, 'error')
        return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    # Hàm kiểm tra số điện thoại
    def is_valid_phone(phone_number):
        # Kiểm tra số điện thoại hợp lệ (có thể chỉnh sửa biểu thức chính quy theo yêu cầu)
        return bool(re.match(r"^\d{10}$", phone_number))

    # Hàm kiểm tra mật khẩu
    def is_valid_password(password):
        # Kiểm tra mật khẩu: ít nhất 8 ký tự, có cả chữ và số
        return bool(re.match(r"^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$", password))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        name = request.form.get('name')
        dob = request.form.get('dob')
        avatar = request.form.get('avatar')
        phone_number = request.form.get('phone_number')
        secret_code = request.form.get('secret_code')

        # password = str(hashlib.md5(password.encode('utf-8')).hexdigest())

        # Kiểm tra các trường bắt buộc
        if not username or not password or not name or not dob or not phone_number:
            flash('Tất cả các trường là bắt buộc!', 'danger')
            return redirect(url_for('register'))

        # Kiểm tra số điện thoại
        if not is_valid_phone(phone_number):
            flash('Số điện thoại không hợp lệ. Vui lòng nhập số điện thoại gồm 10 chữ số.', 'danger')
            return redirect(url_for('register'))

        # Kiểm tra mật khẩu
        if not is_valid_password(password):
            flash('Mật khẩu phải có ít nhất 8 ký tự và chứa cả chữ cái và số.', 'danger')
            return redirect(url_for('register'))

        # Kiểm tra định dạng ngày sinh
        try:
            dob = datetime.strptime(dob, '%Y-%m-%d')
        except ValueError:
            flash('Định dạng ngày sinh không hợp lệ. Vui lòng sử dụng định dạng YYYY-MM-DD.', 'danger')
            return redirect(url_for('register'))

        # Đăng ký người dùng
        success, user, message = dao.register_user(
            username, password, name, dob, avatar, phone_number, secret_code
        )

        if success:

            flash(message, 'success')

        flash(message, 'error')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    session.clear()
    logout_user()

    flash('Bạn đã đăng xuất thành công.', 'success')
    return redirect(url_for('index'))  # Chuyển hướng về trang chính


@app.route('/doctor')
@login_required
def doctor():
    if current_user.role != UserRole.DOCTOR:
        flash('Unauthorized access', 'error')
        return redirect(url_for('index'))
    return render_template('layout/user/doctor.html')


@app.route('/staff')
@login_required
def staff():
    if current_user.role != UserRole.STAFF:
        flash('Unauthorized access', 'error')
        return redirect(url_for('index'))
    if 'staff' in session:
        return render_template('staff.html')

    current_date = datetime.now().date()
    start_date = current_date - timedelta(days=5)

    schedule_data = []
    for single_date in (start_date + timedelta(n) for n in range(10)):
        date_start = datetime.combine(single_date, datetime.min.time())
        date_end = datetime.combine(single_date, datetime.max.time())

        appointments = Appointment.query.filter(
            Appointment.date >= date_start,
            Appointment.date < date_end
        ).all()

        total_count = len(appointments)
        pending_count = len([a for a in appointments if not a.status])

        schedule_data.append({
            'date': single_date,
            'total_count': total_count,
            'max_count': dao.get_max_patients_per_day(),
            'pending_count': pending_count,
            'is_past': single_date < current_date
        })

    staff = Staff.query.get(current_user.id)
    doctors = dao.load_users_by_role(UserRole.STAFF)
    patients = dao.load_users_by_role(UserRole.PATIENT)

    return render_template('layout/user/staff.html',
                           staff=staff,
                           doctors=doctors,
                           patients=patients,
                           schedule_data=schedule_data)


@app.route('/patient')
@login_required
def patient():
    if current_user.role != UserRole.PATIENT:
        flash('Unauthorized access', 'error')
        return redirect(url_for('index'))

    doctors = dao.load_doctors()
    print("Doctors list:", [(d.id, d.name) for d in doctors])  # Debug print

    return render_template('layout/user/patient.html', doctors=doctors)


def get_appointment_counts(date):
    total_appointments = Appointment.query.filter_by(date=date).all()

    online_count = sum(1 for a in total_appointments if a.staff_id is None)
    offline_count = sum(1 for a in total_appointments if a.staff_id is not None)
    return online_count, offline_count


@app.route('/register_appointment', methods=['GET', 'POST'])
@login_required
def register_appointment():
    if request.method == 'POST':
        date = request.form.get('appointment_date')
        doctor_id = request.form.get('doctor')
        patient_id = session.get('user_id')

        if not date or not doctor_id:
            flash('Vui lòng điền đầy đủ thông tin.', 'danger')
            return redirect(url_for('patient'))

        appointment_date = datetime.strptime(date, '%Y-%m-%d').date()
        current_date = datetime.now().date()

        if appointment_date <= current_date:
            flash('Không thể đăng ký vào ngày hiện tại hoặc ngày trong quá khứ.', 'danger')
            return redirect(url_for('patient'))
        if (appointment_date - current_date).days < 2:
            flash('Bạn phải đăng ký trước ít nhất 2 ngày.', 'danger')
            return redirect(url_for('patient'))

        # Check online registration quota
        online_count, _ = get_appointment_counts(appointment_date)
        if online_count >= 10:
            flash('Đã đạt giới hạn đăng ký trực tuyến cho ngày này.', 'danger')
            return redirect(url_for('patient'))

        existing_appointment = Appointment.query.filter_by(
            date=appointment_date,
            patient_id=patient_id
        ).first()
        if existing_appointment:
            flash('Bạn đã đăng ký khám vào ngày này rồi.', 'danger')
            return redirect(url_for('patient'))

        new_appointment = Appointment(
            date=appointment_date,
            doctor_id=int(doctor_id),
            status=0,
            staff_id=None,
            patient_id=patient_id
        )

        db.session.add(new_appointment)
        db.session.commit()

        flash('Đăng ký khám bệnh thành công!', 'success')
        return redirect(url_for('patient'))

    doctors = Doctor.query.filter_by(role='DOCTOR').all()
    return render_template('layout/user/patient.html', doctors=doctors)


@app.route('/some_route')
def some_view():
    # Lấy user từ database
    user_id = session.get('user_id')
    if user_id:
        user = User.query.filter_by(id=user_id).first()
        if user:
            # Lưu thông tin người dùng vào session
            session['staff'] = {
                'name': user.name,
                'avatar': user.avatar or '/static/default-avatar.png',
                'dob': user.dob.strftime('%d/%m/%Y') if user.dob else 'N/A',
                'phone_number': user.phone_number,
                'role': {'name': user.role.name}  # Enum -> string
            }

    return render_template('header.html')


@app.route('/register_appointment_off', methods=['GET', 'POST'])
@login_required
def register_appointment_off():
    if request.method == 'POST':
        date = request.form.get('appointment_date')
        staff_id = session.get('user_id')
        username_patient = request.form.get('username_patient')
        doctor_id = request.form.get('doctor')

        if not date or not doctor_id or not username_patient:
            flash('Vui lòng điền đầy đủ thông tin.', 'danger')
            return redirect(url_for('staff'))

        appointment_date = datetime.strptime(date, '%Y-%m-%d').date()
        current_date = datetime.now().date()

        if appointment_date <= current_date:
            flash('Không thể đăng ký vào ngày hiện tại hoặc ngày trong quá khứ.', 'danger')
            return redirect(url_for('staff'))
        if (appointment_date - current_date).days < 1:
            flash('Bạn phải đăng ký trước ít nhất 1 ngày.', 'danger')
            return redirect(url_for('staff'))

        # Check combined quotas
        online_count, offline_count = get_appointment_counts(appointment_date)
        max_total = dao.get_max_patients_per_day()
        remaining_slots = max_total - online_count

        if offline_count >= remaining_slots:
            flash('Đã đạt giới hạn đăng ký cho ngày này.', 'danger')
            return redirect(url_for('staff'))

        patient_id = dao.get_user_id_by_username(username_patient)
        if patient_id is None:
            flash('Tên đăng nhập của bệnh nhân không đúng hoặc không tồn tại.', 'danger')
            return redirect(url_for('staff'))

        existing_appointment = Appointment.query.filter_by(
            date=appointment_date,
            patient_id=patient_id
        ).first()
        if existing_appointment:
            flash('Bệnh nhân đã đăng ký khám vào ngày này rồi.', 'danger')
            return redirect(url_for('staff'))

        new_appointment = Appointment(
            date=appointment_date,
            doctor_id=int(doctor_id),
            status=0,
            staff_id=staff_id,
            patient_id=patient_id
        )

        db.session.add(new_appointment)
        db.session.commit()

        flash('Đăng ký khám bệnh thành công!', 'success')
        return redirect(url_for('staff'))

    doctors = Doctor.query.filter_by(role='DOCTOR').all()
    patients = Patient.query.filter_by(role='PATIENT').all()
    return render_template('layout/user/staff.html',
                           staff=staff,
                           doctors=doctors,
                           patients=patients,
                           active_function='register_appointment_off'
                           )


@app.route('/process_payment', methods=['GET', 'POST'])
@login_required
def process_payment():
    pass


@app.route('/create_schedule')
@login_required
def create_schedule():
    if current_user.role != UserRole.STAFF:
        flash('Unauthorized access', 'error')
        return redirect(url_for('index'))

    current_date = datetime.now().date()
    start_date = current_date - timedelta(days=5)
    end_date = current_date + timedelta(days=4)

    schedule_data = []
    for single_date in (start_date + timedelta(n) for n in range(10)):
        # Convert date to datetime for SQLAlchemy query
        date_start = datetime.combine(single_date, datetime.min.time())
        date_end = datetime.combine(single_date, datetime.max.time())

        appointments = Appointment.query.filter(
            Appointment.date >= date_start,
            Appointment.date < date_end
        ).all()

        total_count = len(appointments)
        pending_count = len([a for a in appointments if not a.status])

        schedule_data.append({
            'date': single_date,
            'total_count': total_count,
            'max_count': dao.get_max_patients_per_day(),
            'pending_count': pending_count,
            'is_past': single_date < current_date
        })

    return render_template('layout/user/staff.html',
                           staff=current_user.staff,
                           schedule_data=schedule_data,
                           active_function='create_schedule')


@app.route('/confirm_appointments/<date>', methods=['POST'])
@login_required
def confirm_appointments(date):
    try:
        appointment_date = datetime.strptime(date, '%Y-%m-%d').date()
        date_start = datetime.combine(appointment_date, datetime.min.time())
        date_end = datetime.combine(appointment_date, datetime.max.time())

        pending_appointments = Appointment.query.filter(
            Appointment.date >= date_start,
            Appointment.date < date_end,
            Appointment.status == False
        ).all()

        if not pending_appointments:
            flash('Không có lịch hẹn cần xác nhận cho ngày này.', 'info')
            return redirect(url_for('create_schedule'))

        client = Client(app.config['TWILIO_ACCOUNT_SID'],
                        app.config['TWILIO_AUTH_TOKEN'])

        for appointment in pending_appointments:
            appointment.status = True
            patient = User.query.get(appointment.patient_id)
            doctor = Doctor.query.get(appointment.doctor_id)

            try:
                message = client.messages.create(
                    body=f"Xác nhận lịch khám ngày {appointment_date.strftime('%d/%m/%Y')} với bác sĩ {doctor.name}",
                    from_=app.config['TWILIO_PHONE_NUMBER'],
                    to=patient.phone_number
                )
            except Exception as e:
                app.logger.error(f"Failed to send SMS to {patient.phone_number}: {str(e)}")

        db.session.commit()
        flash('Đã xác nhận tất cả các lịch hẹn và gửi thông báo', 'success')

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error confirming appointments: {str(e)}")
        flash('Có lỗi xảy ra khi xác nhận lịch hẹn', 'error')

    return redirect(url_for('create_schedule'))


def auto_confirm_appointments(date):
    """Helper function to confirm appointments for a specific date"""
    date_start = datetime.combine(date, datetime.min.time())
    date_end = datetime.combine(date, datetime.max.time())

    pending_appointments = Appointment.query.filter(
        Appointment.date >= date_start,
        Appointment.date < date_end,
        Appointment.status == False
    ).all()

    if pending_appointments:
        client = Client(app.config['TWILIO_ACCOUNT_SID'],
                        app.config['TWILIO_AUTH_TOKEN'])

        for appointment in pending_appointments:
            appointment.status = True
            patient = User.query.get(appointment.patient_id)
            doctor = Doctor.query.get(appointment.doctor_id)

            try:
                message = client.messages.create(
                    body=f"Xác nhận lịch khám ngày {date.strftime('%d/%m/%Y')} với bác sĩ {doctor.name}",
                    from_=app.config['TWILIO_PHONE_NUMBER'],
                    to=patient.phone_number
                )
            except Exception as e:
                app.logger.error(f"Failed to send SMS to {patient.phone_number}: {str(e)}")

        db.session.commit()


def schedule_auto_confirm():
    """Background task to handle automatic appointment confirmation"""
    with app.app_context():
        while True:
            try:
                current_time = datetime.now()
                current_date = current_time.date()

                # Auto confirm at 00:01
                if current_time.hour == 0 and current_time.minute == 1:
                    auto_confirm_appointments(current_date)

                # Check for full days
                for i in range(5):
                    check_date = current_date + timedelta(days=i)
                    date_start = datetime.combine(check_date, datetime.min.time())
                    date_end = datetime.combine(check_date, datetime.max.time())

                    appointments = Appointment.query.filter(
                        Appointment.date >= date_start,
                        Appointment.date < date_end
                    ).all()

                    if len(appointments) >= dao.get_max_patients_per_day():
                        auto_confirm_appointments(check_date)

            except Exception as e:
                app.logger.error(f"Error in auto confirmation thread: {str(e)}")
            import time
            time.sleep(60)


# Start background thread for auto confirmation
confirmation_thread = threading.Thread(target=schedule_auto_confirm, daemon=True)
confirmation_thread.start()
@app.route('/create_medical_visit', methods=['GET', 'POST'])
def create_medical_visit():
    if request.method == 'POST':
        appointment_id = request.form.get('appointment_id')
        patient_id = request.form.get('patient_id')
        date = request.form.get('date')
        symptoms = request.form.get('symptoms')
        diagnosis = request.form.get('diagnosis')
        doctor_id = 1  # Lấy ID của bác sĩ hiện tại từ phiên đăng nhập

        # Lưu thông tin phiếu khám
        medical_visit = MedicalVisit(appointment_id = appointment_id,patient_id=patient_id, date=date, symptoms=symptoms, diagnosis=diagnosis, doctor_id=doctor_id)
        db.session.add(medical_visit)
        db.session.commit()

        # Lấy ID của phiếu khám vừa lưu
        medical_visit_id = medical_visit.id

        # Lưu thông tin thuốc
        medicines = request.form.getlist('medicines[]')
        quantities = request.form.getlist('quantities[]')
        usages = request.form.getlist('usages[]')

        for i in range(len(medicines)):
            medicine_id = medicines[i]
            quantity = quantities[i]
            usage = usages[i]
            medical_visit_medicine = MedicalVisit_Medicine(medical_visit_id=medical_visit_id, medicine_id=medicine_id, quantity=quantity, usage_instructions=usage)
            db.session.add(medical_visit_medicine)

        db.session.commit()

        flash("Lưu phiếu khám thành công", "success")
        return redirect('layout/user/doctor.html')

    return render_template('doctor/create_MedicalVisit.html')


@app.route('/search_medicine', methods=['GET', 'POST'])
def search_medicine():
    medicines = []
    search_query = ""
    message = ""

    if request.method == 'POST':
        search_query = request.form.get('search_query')
        if search_query:
            # Tìm kiếm thuốc dựa trên từ khóa
            medicines = Medicine.query.filter(Medicine.name.like(f"%{search_query}%")).all()

            # Xử lý khi không có kết quả tìm kiếm
            if not medicines:
                message = "Không tìm thấy kết quả nào!"

    return render_template('doctor/search_medicine.html', medicines=medicines, search_query=search_query, message=message)

if __name__ == '__main__':
    from app.admin import *

    app.run(debug=True)
