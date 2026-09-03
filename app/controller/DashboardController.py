from app.model.gambar import Gambar
from app.model.dataset import Dataset
from app.model.glcm import GLCM
from app.model.hsv import HSV
from app.model.klasifikasi import Klasifikasi
from app.model.user import User
from flask import request, session, render_template, flash, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
from sqlalchemy import func
from app import db

import app.controller.ProcessingController as pre

import os
import uuid


def dashboard():
    """
    Render halaman dashboard utama
    """
    return render_template(
        'backend/dashboard/index.html',
        title='Dashboard',
        active='dashboard'
    )


def getStats():
    """
    Endpoint API untuk mengambil statistik dashboard (JSON)
    """
    try:
        # Total data
        total_pengguna = db.session.query(func.count(User.id)).scalar()
        total_dataset = db.session.query(func.count(Dataset.id)).scalar()
        total_klasifikasi = db.session.query(func.count(Klasifikasi.id)).scalar()

        # Distribusi kualitas dataset
        total_layak = db.session.query(func.count(Dataset.id)).filter(Dataset.kelas == "layak").scalar()
        total_sedang = db.session.query(func.count(Dataset.id)).filter(Dataset.kelas == "sedang").scalar()
        total_tidak = db.session.query(func.count(Dataset.id)).filter(Dataset.kelas == "tidak_layak").scalar()

        return jsonify({
            "success": True,
            "totals": {
                "pengguna": total_pengguna,
                "dataset": total_dataset,
                "klasifikasi": total_klasifikasi
            },
            "distribusi": {
                "Layak": total_layak,
                "Sedang": total_sedang,
                "Tidak Layak": total_tidak
            }
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500