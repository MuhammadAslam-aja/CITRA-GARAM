from sqlalchemy import desc
from app.model.dataset import Dataset
from app import response, app, db, uploadconfig
from flask import request, session, render_template, flash, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
from app.model.gambar import Gambar
from app.model.glcm import GLCM
from app.model.hsv import HSV

import os
import uuid

from app.model.klasifikasi import Klasifikasi

def index():
    return render_template(
        "backend/riwayat/index.html",
        title="Riwayat Klasifikasi",
        active="riwayat",
    )


def getKlasifikasiHistory():
    try:
        draw = request.args.get("draw", default=1, type=int) or 1
        start = request.args.get("start", default=0, type=int) or 0
        length = request.args.get("length", default=10, type=int) or 10
        search_value = request.args.get("search[value]", "", type=str)
        status_filter = request.args.get("status", "", type=str)

        query = Klasifikasi.query

        if status_filter:
            status_map = {
                "Layak": "layak",
                "Sedang": "sedang",
                "Tidak Layak": "tidak_layak"
            }
            if status_filter in status_map:
                query = query.filter(Klasifikasi.kelas == status_map[status_filter])

        if search_value:
            query = query.filter(Klasifikasi.kelas.ilike(f"%{search_value}%"))

        total_records = Klasifikasi.query.count()
        filtered_records = query.count()

        histories = query.offset(start).limit(length).all()

        data = []
        bulan_map = {
            "01": "Januari", "02": "Februari", "03": "Maret", "04": "April",
            "05": "Mei", "06": "Juni", "07": "Juli", "08": "Agustus",
            "09": "September", "10": "Oktober", "11": "November", "12": "Desember"
        }

        for i, h in enumerate(histories, start=start + 1):
            gambar = Gambar.query.get(h.gambar) if h.gambar else None
            img_url = f"/upload/klasifikasi/{gambar.gambar}" if (gambar and gambar.gambar) else None
            img_html = f'<img src="{img_url}" class="w-20 h-20 object-cover rounded-lg border">' if img_url else "-"

            label_map = {
                "layak": ("Layak", "bg-green-500"),
                "sedang": ("Sedang", "bg-yellow-500"),
                "tidak_layak": ("Tidak Layak", "bg-red-500"),
            }
            label_text, label_color = label_map.get(h.kelas, (h.kelas or "-", "bg-gray-500"))
            hasil_html = f"""
              <span class="px-3 py-1 rounded-full text-white text-xs sm:text-sm font-semibold {label_color}">
                {label_text}
              </span>
            """

            if h.tanggal_klasifikasi:
                try:
                    tanggal = h.tanggal_klasifikasi.strftime("%d %m %Y")
                    bulan = bulan_map.get(h.tanggal_klasifikasi.strftime("%m"), h.tanggal_klasifikasi.strftime("%m"))
                    tanggal = tanggal.replace(h.tanggal_klasifikasi.strftime("%m"), bulan)
                except Exception:
                    tanggal = "-"
            else:
                tanggal = "-"

            aksi_html = f"""
              <div class="flex flex-col sm:flex-row space-y-1 sm:space-y-0 sm:space-x-2">
                <button class="viewBtn text-blue-600 hover:text-blue-800 text-sm font-medium" data-id="{h.id}">
                  <i class="fas fa-eye"></i> Detail
                </button>
              </div>
            """

            data.append({
                "no": i,
                "tanggal": tanggal,
                "gambar": img_html,
                "hasil": hasil_html,
                "aksi": aksi_html
            })

        return jsonify({
            "draw": draw,
            "recordsTotal": total_records,
            "recordsFiltered": filtered_records,
            "data": data
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        draw = request.args.get("draw", default=1, type=int) or 1
        return jsonify({
            "draw": draw,
            "recordsTotal": 0,
            "recordsFiltered": 0,
            "data": [],
            "error": str(e)
        }), 200
    
def view(id):
    try:
        klasifikasi = Klasifikasi.query.get(id)
        if not klasifikasi:
            return jsonify(success=False, message="Data klasifikasi tidak ditemukan"), 404

        gambar = Gambar.query.get(klasifikasi.gambar)
        hsv = HSV.query.get(klasifikasi.nilai_hsv)
        glcm = GLCM.query.get(klasifikasi.nilai_glcm)

        # URL gambar
        image_url = os.path.join(app.config["UPLOAD_FOLDER"], "klasifikasi", gambar.gambar) if gambar else None

        # Mapping label agar konsisten
        label_map = {
            "layak": "Layak",
            "sedang": "Sedang",
            "tidak_layak": "Tidak Layak"
        }
        kelas_label = label_map.get(klasifikasi.kelas, klasifikasi.kelas)

        data = {
            "id": klasifikasi.id,
            "kelas": kelas_label,
            "akurasi": round(klasifikasi.nilai_akurasi, 2) if klasifikasi.nilai_akurasi else None,
            "jarak": round(klasifikasi.jarak, 4) if klasifikasi.jarak else None,
            "tanggal": klasifikasi.tanggal_klasifikasi.strftime("%d %B %Y"),
            "image_url": image_url,
            "hasil_klasifikasi": {
                "hue_mean": round(hsv.hue_mean, 4) if hsv else None,
                "sat_mean": round(hsv.sat_mean, 4) if hsv else None,
                "val_mean": round(hsv.val_mean, 4) if hsv else None,
                "energi": round(glcm.energi, 4) if glcm else None,
                "homogenitas": round(glcm.homogenitas, 4) if glcm else None,
                "kontras": round(glcm.kontras, 4) if glcm else None,
                "korelasi": round(glcm.korelasi, 4) if glcm else None,
                "dismilaritas": round(glcm.dismilaritas, 4) if glcm else None
            }
        }

        return jsonify(success=True, data=data)

    except Exception as e:
        return jsonify(success=False, message=str(e)), 500

def deleteAll():
    try:
        histories = Klasifikasi.query.all()

        for kl in histories:
            gambar = Gambar.query.get(kl.gambar)
            glcm = GLCM.query.get(kl.nilai_glcm)
            hsv = HSV.query.get(kl.nilai_hsv)

            db.session.delete(kl)
            db.session.flush() 

            if gambar and gambar.gambar:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'klasifikasi', gambar.gambar)
                if os.path.exists(file_path):
                    os.remove(file_path)
                db.session.delete(gambar)

            if hsv:
                db.session.delete(hsv)
            if glcm:
                db.session.delete(glcm)

        db.session.commit()
        return jsonify(success=True, message="Semua riwayat klasifikasi berhasil dihapus.")

    except Exception as e:
        db.session.rollback()
        return jsonify(success=False, message=str(e)), 500