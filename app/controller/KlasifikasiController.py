from app import response, app, db, uploadconfig
from flask import request, session, render_template, flash, redirect, url_for
from werkzeug.utils import secure_filename
from app.model.gambar import Gambar
from app.model.klasifikasi import Klasifikasi
from app.model.dataset import Dataset
from app.model.glcm import GLCM
from app.model.hsv import HSV
from datetime import date

import os
import uuid
import app.controller.ProcessingController as pre


def index():
    return render_template('backend/klasifikasi/index.html', title='Klasifikasi', active='klasifikasi')


def result():
    user_role = session.get('user_role')
    role = "Admin" if user_role == 0 else "User"
    dataKlasifikasi = session.get('dataKlasifikasi', None)
    if dataKlasifikasi is None:
        flash('Anda harus mengunggah gambar terlebih dahulu', 'error')
        return redirect(url_for('klasifikasis'))
    else:
        session.pop('dataKlasifikasi', None)
    print(dataKlasifikasi)
    return render_template('user/klasifikasi/result.html', dataKlasifikasi=dataKlasifikasi, title='Hasil Klasifikasi', role=role)
