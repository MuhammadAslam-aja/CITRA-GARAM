from app.model.user import User
from app import response, app, db
from flask import request, render_template, flash, redirect, url_for, session, jsonify
from flask_login import current_user, login_user, logout_user

def login():
    # Jika user sudah terautentikasi, arahkan ke dashboard
    if current_user.is_authenticated:
        return redirect(url_for('dashboards'))

    # Proses login jika ada request POST
    if request.method == 'POST':
        try:
            # Ambil username dan password dari form
            username = request.form.get('inputUsername')
            password = request.form.get('inputPassword')

            # Query user berdasarkan username
            user = User.query.filter_by(username=username).first()

            # Jika user tidak ditemukan
            if user is None:
                return jsonify(success=False, message='Username tidak ditemukan.')
            # Jika password salah
            elif not user.checkPassword(password):
                return jsonify(success=False, message='Password yang anda masukkan salah.')
            else:
                # Masuk sebagai user
                login_user(user)
                session['user_id'] = user.id
                session['nama'] = user.nama
                session['user_username'] = user.username
                session['logged_in'] = True

                # Berhasil login, kembalikan response sukses
                return jsonify(success=True)

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Login Exception: {e}")
            return jsonify(success=False, message=f'Terjadi kesalahan: {str(e)}')


    # Render halaman login jika bukan POST
    return render_template('home/index.html', title="Beranda")

def logout():
    try:
        logout_user()
        # flash('Anda telah berhasil logout.', 'success')
        return jsonify({"success": True, "message": "Logout berhasil!"}), 200
    except Exception as e:
        print(e)  # Log the exception for debugging purposes
        # flash('Terjadi Kesalahan. Silakan Coba Lagi.', 'error')
        return jsonify({"success": False, "message": "Terjadi kesalahan, coba lagi."}), 500