from sqlalchemy import desc
from app.model.dataset import Dataset
from app import response, app, db, uploadconfig
from flask import request, session, render_template, flash, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
from app.model.gambar import Gambar
from app.model.dataset import Dataset
from app.model.glcm import GLCM
from app.model.hsv import HSV

import os
import uuid
import app.controller.ProcessingController as pre


def index():
    try:
        # Hitung jumlah dataset berdasarkan kelas
        kualitas_layak = db.session.query(Dataset).filter_by(kelas="layak").count()
        kualitas_sedang = db.session.query(Dataset).filter_by(kelas="sedang").count()
        kualitas_rendah = db.session.query(Dataset).filter_by(kelas="tidak_layak").count()

        return render_template(
            "backend/dataset/index.html",
            title="Manajemen Dataset",
            active="dataset",
            kualitas_layak=kualitas_layak,
            kualitas_sedang=kualitas_sedang,
            kualitas_rendah=kualitas_rendah
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error in dataset index: {e}")
        return render_template(
            "backend/dataset/index.html",
            title="Manajemen Dataset",
            active="dataset",
            kualitas_layak=0,
            kualitas_sedang=0,
            kualitas_rendah=0
        )


def getDataset():
    try:
        draw = request.args.get("draw", default=1, type=int) or 1
        start = request.args.get("start", default=0, type=int) or 0
        length = request.args.get("length", default=10, type=int) or 10

        search_value = request.args.get("search[value]", "", type=str)
        order_column_index = request.args.get("order[0][column]", default=0, type=int) or 0
        order_direction = request.args.get("order[0][dir]", default="asc", type=str)

        columns = ["id", "gambar", "kelas", "created_at"]
        order_column = columns[order_column_index] if order_column_index < len(columns) else "id"

        query = Dataset.query

        if search_value:
            query = query.filter(Dataset.kelas.ilike(f"%{search_value}%"))

        if order_direction == "desc":
            query = query.order_by(desc(getattr(Dataset, order_column, Dataset.id)))
        else:
            query = query.order_by(getattr(Dataset, order_column, Dataset.id))

        total_records = Dataset.query.count()
        filtered_records = query.count()

        datasets = query.offset(start).limit(length).all()

        data = []
        bulan_map = {
            "01": "Januari", "02": "Februari", "03": "Maret", "04": "April",
            "05": "Mei", "06": "Juni", "07": "Juli", "08": "Agustus",
            "09": "September", "10": "Oktober", "11": "November", "12": "Desember"
        }

        for index, ds in enumerate(datasets, start=start + 1):
            gambar = Gambar.query.get(ds.gambar) if ds.gambar else None
            image_url = f"/upload/dataset/{gambar.gambar}" if (gambar and gambar.gambar) else None

            image_html = f'<img src="{image_url}" class="w-20 h-20 object-cover rounded-lg border" alt="preview">' if image_url else "-"

            label_map = {
                "layak": ("Layak", "bg-green-500"),
                "sedang": ("Sedang", "bg-yellow-500"),
                "tidak_layak": ("Tidak Layak", "bg-red-500"),
            }
            label_text, label_color = label_map.get(ds.kelas, (ds.kelas or "-", "bg-gray-500"))
            label_html = f"""
                <span class="px-2 sm:px-3 py-1 rounded-full text-white text-xs sm:text-sm font-semibold {label_color}">
                    {label_text}
                </span>
            """

            if ds.created_at:
                try:
                    tanggal_upload = ds.created_at.strftime("%d %m %Y")
                    bulan = bulan_map.get(ds.created_at.strftime("%m"), ds.created_at.strftime("%m"))
                    tanggal_upload = tanggal_upload.replace(ds.created_at.strftime("%m"), bulan)
                except Exception:
                    tanggal_upload = "-"
            else:
                tanggal_upload = "-"

            action_html = f"""
              <div class="flex flex-col sm:flex-row space-y-1 sm:space-y-0 sm:space-x-2">
                <button class="viewBtn text-blue-600 hover:text-blue-800 text-sm font-medium viewBtn" data-id="{ds.id}">
                  <i class="fas fa-eye"></i> Lihat
                </button>
                <button class="deleteBtn text-red-600 hover:text-red-800 text-sm font-medium deleteBtn" data-id="{ds.id}">
                  <i class="fas fa-trash-alt"></i> Hapus
                </button>
              </div>
            """

            data.append({
                "no": index,
                "preview": image_html,
                "label": label_html,
                "upload": tanggal_upload,
                "aksi": action_html,
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
    

def viewDataset(id):
    try:
        dataset = Dataset.query.get(id)
        if not dataset:
            return jsonify(success=False, message="Dataset tidak ditemukan"), 404

        gambar = Gambar.query.get(dataset.gambar)
        image_url = None
        file_size_kb = None

        if gambar and gambar.gambar:
            image_url = f"/upload/dataset/{gambar.gambar}"
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], "dataset", gambar.gambar)
            if os.path.exists(file_path):
                file_size_kb = round(os.path.getsize(file_path) / 1024, 2)

        label_map = {
            "layak": "Layak",
            "sedang": "Sedang",
            "tidak_layak": "Tidak Layak",
        }
        label_text = label_map.get(dataset.kelas, dataset.kelas)

        return jsonify(success=True, data={
            "id": dataset.id,
            "label": label_text,
            "upload": dataset.created_at.strftime("%d %B %Y") if dataset.created_at else "-",
            "image_url": image_url,
            "size": f"{file_size_kb}" if file_size_kb else None,
            "filename": gambar.gambar if gambar else None
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify(success=False, message=str(e)), 500

    
def refreshCount():
    try:
        kualitas_layak = db.session.query(Dataset).filter_by(kelas="layak").count()
        kualitas_sedang = db.session.query(Dataset).filter_by(kelas="sedang").count()
        kualitas_rendah = db.session.query(Dataset).filter_by(kelas="tidak_layak").count()

        return jsonify({
            "success": True,
            "kualitas_layak": kualitas_layak,
            "kualitas_sedang": kualitas_sedang,
            "kualitas_rendah": kualitas_rendah
        })
    except Exception as e:
        return jsonify(success=False, message=str(e)), 500

def upload():
    if request.method == 'GET':
        form_html = render_template('backend/dataset/_form.html')
        return jsonify(success=True, form=form_html)
    
    if request.method == 'POST':
        try:
            # Ambil label kualitas
            kualitas = request.form.get('label')
            if kualitas not in ['layak', 'sedang', 'tidak_layak']:
                return jsonify(success=False, message="Label kualitas tidak valid"), 400

            # Ambil semua file yang diupload
            files = request.files.getlist('files[]')
            if not files or files[0].filename == '':
                return jsonify(success=False, message="Tidak ada file yang dipilih"), 400

            uploaded_count = 0
            for file in files:
                if file and uploadconfig.allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    filename = f"{uuid.uuid4().hex}_{filename}"
                    save_path = os.path.join(app.config['UPLOAD_FOLDER'], 'dataset', filename)
                    os.makedirs(os.path.dirname(save_path), exist_ok=True)
                    file.save(save_path)

                    # Jalankan preprocessing
                    proses_gambar = pre.runDataset(save_path)

                    # Simpan data gambar
                    data_gambar = Gambar(gambar=filename)
                    db.session.add(data_gambar)
                    db.session.commit()

                    # Simpan nilai GLCM
                    nilai_glcm = proses_gambar['nilai_glcm']
                    data_glcm = GLCM(
                        energi=nilai_glcm['energy'],
                        homogenitas=nilai_glcm['homogeneity'],
                        kontras=nilai_glcm['contrast'],
                        korelasi=nilai_glcm['correlation'],
                        dismilaritas=nilai_glcm['dissimilarity']
                    )
                    db.session.add(data_glcm)
                    db.session.commit()

                    # Simpan nilai HSV
                    nilai_hsv = proses_gambar['nilai_hsv']
                    data_hsv = HSV(
                        hue_std=nilai_hsv['hue_std'],
                        hue_mean=nilai_hsv['hue_mean'],
                        sat_std=nilai_hsv['sat_std'],
                        sat_mean=nilai_hsv['sat_mean'],
                        val_std=nilai_hsv['val_std'],
                        val_mean=nilai_hsv['val_mean']
                    )
                    db.session.add(data_hsv)
                    db.session.commit()

                    # Simpan ke dataset
                    data_dataset = Dataset(
                        gambar=data_gambar.id,
                        kelas=kualitas,
                        nilai_hsv=data_hsv.id,
                        nilai_glcm=data_glcm.id,
                    )
                    db.session.add(data_dataset)
                    db.session.commit()

                    uploaded_count += 1

            print(uploaded_count)
            print(kualitas)
            print(files)

            return jsonify(success=True, message=f"{uploaded_count} file dataset berhasil diupload")

        except Exception as e:
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return jsonify(success=False, message=str(e)), 500


def delete(id):
    try:
        dataset = Dataset.query.filter_by(id=id).first()

        if not dataset:
            return jsonify(success=False, message="Dataset tidak ditemukan"), 404

        # Ambil relasi
        gambar = Gambar.query.filter_by(id=dataset.gambar).first()
        hsv = HSV.query.filter_by(id=dataset.nilai_hsv).first()
        glcm = GLCM.query.filter_by(id=dataset.nilai_glcm).first()

        # Hapus file gambar dari folder
        if gambar:
            base_dir = os.path.join(os.getcwd(), "upload", "dataset")
            files_dir = os.path.join(base_dir, gambar.gambar)
            if os.path.exists(files_dir):
                os.remove(files_dir)

        # Hapus record database
        db.session.delete(dataset)
        if gambar:
            db.session.delete(gambar)
        if hsv:
            db.session.delete(hsv)
        if glcm:
            db.session.delete(glcm)

        db.session.commit()

        return jsonify(success=True, message="Dataset berhasil dihapus")

    except Exception as e:
        db.session.rollback()
        return jsonify(success=False, message=str(e)), 500


def deleteAll():
    try:
        # Ambil semua dataset
        datasets = Dataset.query.all()

        for ds in datasets:
            # Cari relasi gambar, glcm, hsv berdasarkan ID foreign key
            gambar = Gambar.query.get(ds.gambar)
            glcm = GLCM.query.get(ds.nilai_glcm)
            hsv = HSV.query.get(ds.nilai_hsv)

            # Hapus file gambar jika ada
            if gambar and gambar.gambar:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'dataset', gambar.gambar)
                if os.path.exists(file_path):
                    os.remove(file_path)
                db.session.delete(gambar)

            # Hapus data glcm jika ada
            if glcm:
                db.session.delete(glcm)

            # Hapus data hsv jika ada
            if hsv:
                db.session.delete(hsv)

            # Terakhir hapus dataset
            db.session.delete(ds)

        db.session.commit()

        return jsonify(success=True, message="Semua dataset berhasil dihapus.")
    except Exception as e:
        db.session.rollback()
        return jsonify(success=False, message=str(e)), 500