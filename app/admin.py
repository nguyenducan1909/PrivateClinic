from app import app, db
from flask_admin import Admin, BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user, logout_user
from flask import redirect, request
from wtforms import IntegerField, HiddenField
from models import UserRole, Medicine, Policy, Unit, MedicineUnit
import dao
from wtforms_sqlalchemy.fields import QuerySelectField
from wtforms.fields import SelectField


class AuthenticatedModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == UserRole.ADMIN

class MedicineView(AuthenticatedModelView):
    column_list = ['name', 'display_units', 'display_prices', 'display_quantities']

    can_edit = True
    can_delete = True
    def _format_display_units(view, context, model, name):
        return ', '.join(unit.unit.name for unit in model.units)

    def _format_display_prices(view, context, model, name):
        return ', '.join(str(unit.price) for unit in model.units)

    def _format_display_quantities(view, context, model, name):
        return ', '.join(str(unit.quantity) for unit in model.units)

    column_formatters = {
        'display_units': _format_display_units,
        'display_prices': _format_display_prices,
        'display_quantities': _format_display_quantities,
    }

    column_labels = {
        'display_units': 'Units',
        'display_prices': 'Prices',
        'display_quantities': 'Quantities',
    }

    form_columns = ['name', 'units']


    inline_models = [
        (MedicineUnit, {
            'form_columns': ['unit_id', 'price', 'quantity', 'medicine_id'],
            'form_extra_fields': {
                'medicine_id': HiddenField(),
                'unit_id': SelectField(
                    'Unit',
                    choices=lambda: [(unit.id, unit.name) for unit in Unit.query.all()],
                    coerce=int
                )
            },
        })
    ]


class UnitView(AuthenticatedModelView):
    can_delete = False
    def on_model_change(self, form, model, is_created):
        if is_created:
            model.admin = current_user
        super().on_model_change(form, model, is_created)

class PolicyView(AuthenticatedModelView):
    can_create = False
    can_delete = False

class StatsView(BaseView):
    @expose('/')
    def index(self):
        rq_month = request.args.get('month')
        if rq_month:
            year, month = rq_month.split('-')  # Tách tháng và năm từ chuỗi
        else:
            year, month = 1, 1  # Gán giá trị mặc định khi không có `month`

        if not year or not month:
            stats = []  # Gán giá trị mặc định cho stats khi không có dữ liệu
            total_revenue = 0
        else:
            stats = dao.stats_monthly_revenue(month=month, year=year)  # Hàm DAO tính toán doanh thu

        print(stats)
        return self.render('admin/stats.html', stats=stats)

    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == UserRole.ADMIN

class StatsMedicineView(BaseView):
    @expose('/')
    def index(self):
        rq_month = request.args.get('month')
        if rq_month:
            year, month = rq_month.split('-')  # Tách tháng và năm từ chuỗi
        else:
            year, month = 0, 0  # Gán giá trị mặc định khi không có `month`

        if not year or not month:
            stats = []  # Gán giá trị mặc định cho stats khi không có dữ liệu
            total_revenue = 0
        else:
            stats = dao.get_medicine_usage_report(month=month, year=year)  # Hàm DAO tính toán doanh thu

        print(stats)
        return self.render('admin/stats_medicine.html', stats=stats)

    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == UserRole.ADMIN

class LogoutView(BaseView):
    @expose('/')
    def index(self):
        logout_user()
        return redirect('/admin')

    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == UserRole.ADMIN

admin = Admin(app=app, name="Private Clinic Management", template_mode='bootstrap4')

# Add views for different models
admin.add_view(MedicineView(Medicine, db.session))
admin.add_view(PolicyView(Policy, db.session))
admin.add_view(UnitView(Unit, db.session))
admin.add_view(StatsView(name='Stats'))
admin.add_view(StatsMedicineView(name='Stats Medicine'))
admin.add_view(LogoutView(name='Logout'))