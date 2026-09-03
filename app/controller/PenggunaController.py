from flask_login import current_user
from sqlalchemy import desc
from app import response, app, db, uploadconfig
from flask import request, session, render_template, flash, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
from app.model.user import User
from app.model.klasifikasi import Klasifikasi
from app.model.gambar import Gambar
from app.model.glcm import GLCM
from app.model.hsv import HSV

import os
import uuid


def index():
    return render_template('backend/pengguna/index.html', title='Manajemen Pengguna', active='pengguna')

def getPengguna():
    try:
        # Pagination
        start = request.args.get('start', default=0, type=int)
        length = request.args.get('length', default=10, type=int)

        # Search
        search_value = request.args.get('search[value]', '', type=str)

        # Order
        order_column_index = request.args.get('order[0][column]', default=0, type=int)
        order_direction = request.args.get('order[0][dir]', default='asc', type=str)

        # Kolom yang sesuai urutan di frontend
        columns = ['id', 'nama', 'username', 'created_at']
        order_column = columns[order_column_index]

        # Base query
        query = User.query

        # Filter jika ada pencarian
        if search_value:
            query = query.filter(
                (User.nama.ilike(f"%{search_value}%")) |
                (User.username.ilike(f"%{search_value}%"))
            )

        # Sorting
        if order_direction == 'desc':
            query = query.order_by(desc(getattr(User, order_column)))
        else:
            query = query.order_by(getattr(User, order_column))

        # Hitung total
        total_records = User.query.count()
        filtered_records = query.count()

        # Paginate
        users = query.offset(start).limit(length).all()

        # Format data untuk DataTable
        data = []
        bulan_map = {
            "01": "Januari", "02": "Februari", "03": "Maret", "04": "April",
            "05": "Mei", "06": "Juni", "07": "Juli", "08": "Agustus",
            "09": "September", "10": "Oktober", "11": "November", "12": "Desember"
        }

        for index, user in enumerate(users, start=start + 1):
            tanggal_indo = f"{user.created_at.day} {bulan_map.get(user.created_at.strftime('%m'))} {user.created_at.year}"

            # Jika user ini adalah yang sedang login sekarang
            if current_user.id == user.id:
                action_html = """
                  <span class="px-2 py-1 text-xs sm:text-sm font-semibold rounded-full bg-green-500 text-white">
                    Sedang Login
                  </span>
                """
            else:
                # User lain → tombol aksi
                action_html = f"""
                  <div class="flex flex-col sm:flex-row space-y-1 sm:space-y-0 sm:space-x-2">
                    <button class="text-blue-600 hover:text-blue-800 text-sm font-medium editBtn" data-user="{user.id}">
                      <i class="fas fa-edit"></i> Edit
                    </button>
                    <button class="text-red-600 hover:text-red-800 text-sm font-medium deleteBtn" data-user="{user.id}">
                      <i class="fas fa-trash-alt"></i> Hapus
                    </button>
                  </div>
                """

            data.append({
                "id": user.id,
                "name": user.nama,
                "username": user.username,
                "joined": tanggal_indo,
                "action": action_html
            })

        return jsonify({
            "draw": request.args.get('draw', type=int),
            "recordsTotal": total_records,
            "recordsFiltered": filtered_records,
            "data": data
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def add():
    if request.method == 'GET':
        form_html = render_template('backend/pengguna/_form.html')
        return jsonify(success=True, form=form_html)

    if request.method == 'POST':
       # Get the form data
        nama = request.form.get('userName')  # Match the input name in the form
        username = request.form.get('userUsername')  # Match the input name in the form
        password = request.form.get('userPassword')  # Match the input name in the form

        # Input validation
        if not nama or not username or not password:
            return jsonify(success=False, message="Semua field harus diisi"), 400

        # Check if the username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return jsonify(success=False, message="Username sudah digunakan"), 400

        # Create a new user and save to the database
        new_user = User(username=username, nama=nama, plain_password=password)  # Assuming you have a 'nama' field in your User model
        new_user.set_password(password)  # Hash the password

        db.session.add(new_user)  # Add the new user to the session
        db.session.commit()  # Commit the changes to the database

        return jsonify(success=True, message="Pengguna baru berhasil ditambahkan!")


def edit(id):
    user = User.query.get(id)

    if not user:
        return jsonify(success=False, message="Pengguna tidak ditemukan"), 404

    # Jika GET -> return form HTML (untuk modal)
    if request.method == "GET":
        form_html = render_template("backend/pengguna/_form.html", user=user)
        return jsonify(success=True, form=form_html)

    # Jika POST -> update data user
    if request.method == "POST":
        nama = request.form.get("userName")
        username = request.form.get("userUsername")
        password = request.form.get("userPassword")

        if not nama or not username:
            return jsonify(success=False, message="Nama dan Username wajib diisi"), 400

        # Cek duplikat username selain user ini
        existing_user = User.query.filter(User.username == username, User.id != id).first()
        if existing_user:
            return jsonify(success=False, message="Username sudah digunakan"), 400

        # Update data
        user.nama = nama
        user.username = username

        if password:  # Jika password diisi baru
            user.set_password(password)
            user.plain_password = password

        db.session.commit()
        return jsonify(success=True, message="Data pengguna berhasil diperbarui")


def delete(user_id):
    try:
        user = User.query.get(user_id)
        if user:
            db.session.delete(user)  # Delete the user from the session
            db.session.commit()  # Commit the changes to the database
            return jsonify(success=True), 200
        else:
            return jsonify(success=False, message="Pengguna tidak ditemukan"), 404
    except Exception as e:
        db.session.rollback()
        return jsonify(success=False, message=str(e)), 500


def riwayatKlasifikasi():
    user_role = session.get('user_role')
    role = "Admin" if user_role == 0 else "User"

    if user_role == 0:
        query = db.session.query(Klasifikasi, Gambar, GLCM, HSV, User).join(
            Gambar).join(GLCM).join(HSV).join(User).filter(Klasifikasi.kelas != 'bukan objek').all()
        data = []
        for row in query:
            data.append({
                'id': row.Klasifikasi.id,
                'gambar': row.Gambar.gambar,
                'kelas': row.Klasifikasi.kelas,
                'user': row.User.nama,
                'tanggal_klasifikasi': row.Klasifikasi.tanggal_klasifikasi
            })
        return render_template('admin/riwayat/index.html', title='Riwayat Klasifikasi', role=role, data=data)
    elif user_role == 1:
        query = db.session.query(Klasifikasi, Gambar, GLCM, HSV).join(
            Gambar).join(GLCM).join(HSV).filter(
                Klasifikasi.user == session.get('user_id'),
                Klasifikasi.kelas != 'bukan objek'
            ).all()         
        data = []
        for row in query:
            data.append({
                'id': row.Klasifikasi.id,
                'gambar': row.Gambar.gambar,
                'kelas': row.Klasifikasi.kelas,
                'tanggal_klasifikasi': row.Klasifikasi.tanggal_klasifikasi
            })
        return render_template('user/riwayat/index.html', title='Riwayat Klasifikasi', role=role, data=data)
    else:
        flash('Anda tidak memiliki izin untuk mengakses halaman ini.', 'error')
        return redirect(url_for('logins'))


def deleteKlasifikasi(id):
    try:
        klasifikasi = Klasifikasi.query.filter_by(id=id).first()

        if not klasifikasi:
            flash('Data Klasifikasi tidak ditemukan', 'error')
            return redirect(url_for('riwayatKlasifikasisUsers'))

        gambar = Gambar.query.filter_by(id=klasifikasi.gambar).first()
        hsv = HSV.query.filter_by(id=klasifikasi.nilai_hsv).first()
        glcm = GLCM.query.filter_by(id=klasifikasi.nilai_glcm).first()

        if gambar:
            base_dir = os.getcwd().replace('\\', '/') + '/upload/klasifikasi/'
            files_dir = os.path.join(base_dir, gambar.gambar)
            if os.path.exists(files_dir):
                os.remove(files_dir)

        if glcm:
            db.session.delete(glcm)
        if hsv:
            db.session.delete(hsv)

        db.session.delete(klasifikasi)
        db.session.commit()

        flash('Riwayat klasifikasi berhasil dihapus', 'success')
        return redirect(url_for('riwayatKlasifikasisUsers'))
    except Exception as e:
        print(e)
        flash('Terjadi kesalahan. Silakan coba lagi.', 'error')
        return redirect(url_for('riwayatKlasifikasisUsers'))
