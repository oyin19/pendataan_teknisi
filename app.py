import os
import pymysql
import pandas as pd
import xlsxwriter
from flask import Flask, render_template, request, redirect, url_for, send_file, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename
from io import BytesIO
from datetime import datetime

# ==========================================
# 1. KONFIGURASI PATH ABSOLUT (SINKRONISASI)
# ==========================================
# Mencari alamat folder tempat file app.py berada
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Path Absolut untuk folder Upload
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')

app = Flask(__name__)
app.secret_key = 'kunci_rahasia_123'

# --- PILIHAN DATABASE ---
# Jika di PythonAnywhere, disarankan pakai SQLite agar tidak repot setting MySQL
# Jika ingin tetap MySQL di lokal, biarkan seperti ini:
DB_USER, DB_PASSWORD, DB_NAME, DB_HOST = 'root', '', 'db_pendataan_teknisi', 'localhost'

# CONTOH PATH ABSOLUT UNTUK SQLITE (Opsional untuk Hosting):
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'database.db')

app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ==========================================

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- MODELS (Tetap sama) ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)

class Pekerjaan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    tanggal = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(50), nullable=False)
    foto_sebelum = db.Column(db.String(255))
    foto_proses = db.Column(db.String(255))
    foto_sesudah = db.Column(db.String(255))

class Aset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama_aset = db.Column(db.String(100), nullable=False)
    kode_aset = db.Column(db.String(50), unique=True, nullable=False)
    kategori = db.Column(db.String(50), nullable=False)
    kondisi = db.Column(db.String(50), nullable=False)
    lokasi = db.Column(db.String(100))
    foto_aset = db.Column(db.String(255))
    tanggal_input = db.Column(db.Date, default=datetime.now)

@login_manager.user_loader
def load_user(id): return User.query.get(int(id))

# --- FUNGSI SAVE IMG (Menggunakan Path Absolut) ---
def save_img(file, prefix):
    if file and file.filename != '':
        fname = secure_filename(f"{prefix}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
        # Menggunakan os.path.join dengan config UPLOAD_FOLDER yang sudah absolut
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))
        return fname
    return None

# --- ROUTES (Singkatnya sama, pastikan rute export menggunakan UPLOAD_FOLDER absolut) ---

@app.route('/aset/export')
@login_required
def aset_export_excel():
    data = Aset.query.all()
    output = BytesIO()
    wb = xlsxwriter.Workbook(output)
    ws = wb.add_worksheet('Aset')
    head_f = wb.add_format({'bold': True, 'bg_color': '#2e75b6', 'font_color': 'white', 'border': 1})
    
    headers = ['Foto', 'Kode', 'Nama', 'Kategori', 'Kondisi', 'Lokasi']
    for c, h in enumerate(headers): ws.write(0, c, h, head_f)
    ws.set_column('A:A', 12)
    
    for r, a in enumerate(data, 1):
        ws.set_row(r, 65)
        # PENGECEKAN FOTO DENGAN PATH ABSOLUT
        if a.foto_aset:
            img_path = os.path.join(app.config['UPLOAD_FOLDER'], a.foto_aset)
            if os.path.exists(img_path):
                ws.insert_image(r, 0, img_path, {'x_scale': 0.08, 'y_scale': 0.08})
        
        ws.write(r, 1, a.kode_aset); ws.write(r, 2, a.nama_aset); ws.write(r, 3, a.kategori)
        ws.write(r, 4, a.kondisi); ws.write(r, 5, a.lokasi)
    wb.close(); output.seek(0)
    return send_file(output, as_attachment=True, download_name="Data_Aset.xlsx")

# (Sisanya tetap sama dengan kode Anda...)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = User.query.filter_by(username=request.form['username'], password=request.form['password']).first()
        if u: login_user(u); return redirect(url_for('index'))
    return render_template('login.html')

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER): os.makedirs(UPLOAD_FOLDER)
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='admin').first():
            db.session.add(User(username='admin', password='123')); db.session.commit()
    app.run(debug=True)