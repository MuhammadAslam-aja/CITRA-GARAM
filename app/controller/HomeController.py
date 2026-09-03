from datetime import date
import os
import uuid
from app import response, app, db
from flask import request, render_template, flash, redirect, url_for, session, jsonify
from flask_jwt_extended import *
from werkzeug.utils import secure_filename


from app.model.dataset import Dataset
from app.model.gambar import Gambar
from app.model.glcm import GLCM
from app.model.hsv import HSV
from app.model.klasifikasi import Klasifikasi
from app.uploadconfig import allowed_file

import app.controller.ProcessingController as pre


def index():
    """
    Home page route that handles both displaying the classification interface
    and processing classification requests
    """
    try:
        if request.method == 'POST':
            # Handle AJAX classification request
            if request.is_json or 'image' in request.files:
                return handle_classification_request()
            
        # GET request - display home page
        return render_template('home/index.html', title='GaramCitra - Klasifikasi Kualitas Garam')
    
    except Exception as e:
        print(f"Error in index route: {e}")
        if request.method == 'POST':
            return jsonify({
                'success': False,
                'message': 'Terjadi kesalahan sistem. Silakan coba lagi.'
            }), 500
        else:
            flash('Terjadi kesalahan sistem. Silakan coba lagi.', 'error')
            return render_template('home/index.html', title='GaramCitra - Klasifikasi Kualitas Garam')
        
def homeKlasifikasi():
    if request.method == 'POST':
        return handle_classification_request()
        
def handle_classification_request():
    """
    Handle the actual classification process
    """
    try:
        # Validate file upload
        if 'image' not in request.files:
            return jsonify({
                'success': False,
                'message': 'Tidak ada gambar yang diupload'
            }), 400

        file = request.files['image']
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': 'Tidak ada gambar yang dipilih'
            }), 400

        # Validate file type and size
        if not file or not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'message': 'Format file tidak didukung. Gunakan JPG, PNG, atau JPEG.'
            }), 400

        # Check file size (5MB limit)
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > 5 * 1024 * 1024:  # 5MB in bytes
            return jsonify({
                'success': False,
                'message': 'Ukuran file terlalu besar. Maksimal 5MB.'
            }), 400

        # Generate unique filename and save
        filename = secure_filename(file.filename)
        filename = str(uuid.uuid4()) + '_' + filename
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], 'klasifikasi', filename)
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(upload_path), exist_ok=True)
        file.save(upload_path)

        # Get training data from database
        training_data = get_training_data()
        
        if not training_data:
            return jsonify({
                'success': False,
                'message': 'Data training tidak tersedia. Hubungi administrator.'
            }), 500

        # Process classification
        classification_result = process_salt_classification(upload_path, training_data)
        
        if not classification_result:
            return jsonify({
                'success': False,
                'message': 'Gagal memproses klasifikasi gambar.'
            }), 500

        # Save results to database
        save_classification_to_db(filename, classification_result)

        # Prepare response data
        response_data = prepare_classification_response(filename, classification_result)
        
        # Check if the image is actually salt
        if classification_result['kelas'] == 'bukan objek':
            return jsonify({
                'success': False,
                'message': 'Gambar yang diupload bukan objek garam. Silakan upload gambar garam yang valid.'
            }), 400

        return jsonify({
            'success': True,
            'message': f'Klasifikasi berhasil! Kualitas garam: {classification_result["kelas"]}',
            'data': response_data
        })

    except Exception as e:
        print(f"Error in classification: {e}")
        return jsonify({
            'success': False,
            'message': 'Terjadi kesalahan dalam proses klasifikasi. Silakan coba lagi.'
        }), 500


def get_training_data():
    """
    Retrieve training data from database
    """
    try:
        # Query to get all training data with JOIN operations
        query = db.session.query(Dataset, Gambar, HSV, GLCM).join(HSV).join(Gambar).join(GLCM).all()
        
        training_data = []
        for row in query:
            training_data.append({
                'id': row.Dataset.id,
                'gambar': row.Gambar.gambar,
                'kelas': row.Dataset.kelas,
                'hue_mean': row.HSV.hue_mean,
                'hue_std': row.HSV.hue_std,
                'sat_mean': row.HSV.sat_mean,
                'sat_std': row.HSV.sat_std,
                'val_mean': row.HSV.val_mean,
                'val_std': row.HSV.val_std,
                'energy': row.GLCM.energi,
                'homogeneity': row.GLCM.homogenitas,
                'contrast': row.GLCM.kontras,
                'correlation': row.GLCM.korelasi,
                'dissimilarity': row.GLCM.dismilaritas
            })
        
        return training_data
    
    except Exception as e:
        print(f"Error getting training data: {e}")
        return None


def process_salt_classification(image_path, training_data):
    """
    Process the salt classification using KNN algorithm
    """
    try:
        classification_result = pre.runKlasifikasi(image_path, training_data)
        return classification_result
    
    except Exception as e:
        print(f"Error in salt classification processing: {e}")
        return None


def save_classification_to_db(filename, classification_result):
    """
    Save classification results to database
    """
    try:
        # Save image record
        gambar = Gambar(gambar=filename)
        db.session.add(gambar)
        db.session.commit()

        # Save GLCM data
        data_glcm = GLCM(
            energi=classification_result['energy'],
            homogenitas=classification_result['homogeneity'],
            kontras=classification_result['contrast'],
            korelasi=classification_result['correlation'],
            dismilaritas=classification_result['dissimilarity']
        )
        db.session.add(data_glcm)
        db.session.commit()

        # Save HSV data
        data_hsv = HSV(
            hue_mean=classification_result['hue_mean'],
            hue_std=classification_result['hue_std'],
            sat_mean=classification_result['sat_mean'],
            sat_std=classification_result['sat_std'],
            val_mean=classification_result['val_mean'],
            val_std=classification_result['val_std']
        )
        db.session.add(data_hsv)
        db.session.commit()

        # Save classification record
        klasifikasi = Klasifikasi(
            gambar=gambar.id,
            jarak=classification_result['jarak'],
            kelas=classification_result['kelas'],
            nilai_hsv=data_hsv.id,
            nilai_glcm=data_glcm.id,
            nilai_akurasi=classification_result['akurasi'],
            tanggal_klasifikasi=date.today()
        )
        db.session.add(klasifikasi)
        db.session.commit()

        return True

    except Exception as e:
        db.session.rollback()
        print(f"Error saving to database: {e}")
        return False


def prepare_classification_response(filename, classification_result):
    """
    Prepare the response data for the frontend
    """
    try:
        # Mapping dari database ke label tampilan
        label_mapping = {
            'layak': 'Layak',
            'sedang': 'Sedang',
            'tidak_layak': 'Tidak Layak'
        }

        # Ambil label hasil klasifikasi (default = raw value dari DB)
        kelas_db = classification_result['kelas']
        kelas_display = label_mapping.get(kelas_db, kelas_db)

        # Deskripsi kualitas (pakai label display)
        quality_descriptions = {
            'Layak': 'Garam dengan kualitas premium. Kristal sempurna, warna optimal, dan tekstur halus yang memenuhi standar kualitas tinggi.',
            'Sedang': 'Garam dengan kualitas standar. Kristal baik, warna normal, dan tekstur sedang yang masih dapat diterima untuk konsumsi.',
            'Tidak Layak': 'Garam dengan kualitas rendah. Perlu dilakukan perbaikan dan analisis lebih lanjut sebelum dapat dikonsumsi.'
        }

        response_data = {
            'gambar': filename,
            'hasil_klasifikasi': {
                'hue_mean': round(classification_result['hue_mean'], 4),
                'hue_std': round(classification_result['hue_std'], 4),
                'sat_mean': round(classification_result['sat_mean'], 4),
                'sat_std': round(classification_result['sat_std'], 4),
                'val_mean': round(classification_result['val_mean'], 4),
                'val_std': round(classification_result['val_std'], 4),
                'energi': round(classification_result['energy'], 4),
                'homogenitas': round(classification_result['homogeneity'], 4),
                'kontras': round(classification_result['contrast'], 4),
                'korelasi': round(classification_result['correlation'], 4),
                'dismilaritas': round(classification_result['dissimilarity'], 4)
            },
            'kelas': kelas_display,  # ✅ tampilkan label hasil mapping
            'jarak': round(classification_result['jarak'], 4),
            'akurasi': round(classification_result['akurasi'], 2),
            'keterangan_klasifikasi': quality_descriptions.get(
                kelas_display,
                'Klasifikasi tidak dikenali.'
            ),
            'tanggal_klasifikasi': date.today().strftime('%Y-%m-%d')
        }

        return response_data

    except Exception as e:
        print(f"Error preparing response: {e}")
        return None
