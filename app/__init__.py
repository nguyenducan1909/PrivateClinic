from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from urllib.parse import quote

app = Flask(__name__)
app.secret_key = '@#$%^*&A^D&A(D*D*^A&%^D$^%&DAY*UAD*AD^&'
app.config[
    "SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:%s@localhost/clinicdb?charset=utf8mb4" % quote('An123456')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

login_manager = LoginManager(app)
