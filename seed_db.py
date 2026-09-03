import os
from dotenv import load_dotenv
load_dotenv()

import shutil
import uuid
from app import app, db
from app.model.user import User
from app.model.gambar import Gambar
from app.model.glcm import GLCM
from app.model.hsv import HSV
from app.model.dataset import Dataset
import app.controller.ProcessingController as pre


def main():
    print("Mulai proses seeding database...")
    
    # 1. Pastikan folder upload/dataset ada
    upload_dataset_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'dataset')
    os.makedirs(upload_dataset_dir, exist_ok=True)
    
    with app.app_context():
        # 2. Hapus data lama agar bersih
        print("Membersihkan data lama di database...")
        db.session.query(Dataset).delete()
        db.session.query(Gambar).delete()
        db.session.query(GLCM).delete()
        db.session.query(HSV).delete()
        db.session.query(User).delete()
        db.session.commit()
        
        # 3. Buat user admin default
        print("Membuat user admin default...")
        admin = User(nama='Administrator', username='admin', plain_password='password123')
        admin.set_password('password123')
        db.session.add(admin)
        db.session.commit()
        print("User admin default berhasil dibuat! (admin / password123)")
        
        # 4. Tentukan folder asal dataset
        dataset_base_dir = os.path.join(os.getcwd(), 'kualitas garam.v1i.folder', 'train')
        categories = {
            'layak': 'layak',
            'sedang': 'sedang',
            'tidak': 'tidak_layak'
        }
        
        # 5. Iterasi dan proses setiap gambar
        total_seeded = 0
        for src_folder, db_label in categories.items():
            folder_path = os.path.join(dataset_base_dir, src_folder)
            if not os.path.exists(folder_path):
                print(f"Folder sumber tidak ditemukan: {folder_path}")
                continue
                
            files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            print(f"Memproses {len(files)} file dari folder '{src_folder}' dengan label '{db_label}'...")
            
            # Kita proses maksimal 180 file per kelas (atau semua yang ada)
            for i, filename in enumerate(files):
                src_file_path = os.path.join(folder_path, filename)
                
                # Buat nama file unik
                unique_filename = f"{uuid.uuid4().hex}_{filename}"
                dest_file_path = os.path.join(upload_dataset_dir, unique_filename)
                
                try:
                    # Copy file ke folder upload/dataset
                    shutil.copy(src_file_path, dest_file_path)
                    
                    # Jalankan ekstraksi fitur (Preprocessing, HSV, GLCM)
                    features = pre.runDataset(dest_file_path)
                    
                    # Simpan data Gambar
                    db_gambar = Gambar(gambar=unique_filename)
                    db.session.add(db_gambar)
                    db.session.commit()
                    
                    # Simpan data GLCM
                    nilai_glcm = features['nilai_glcm']
                    db_glcm = GLCM(
                        energi=nilai_glcm['energy'],
                        homogenitas=nilai_glcm['homogeneity'],
                        kontras=nilai_glcm['contrast'],
                        korelasi=nilai_glcm['correlation'],
                        dismilaritas=nilai_glcm['dissimilarity']
                    )
                    db.session.add(db_glcm)
                    db.session.commit()
                    
                    # Simpan data HSV
                    nilai_hsv = features['nilai_hsv']
                    db_hsv = HSV(
                        hue_std=nilai_hsv['hue_std'],
                        hue_mean=nilai_hsv['hue_mean'],
                        sat_std=nilai_hsv['sat_std'],
                        sat_mean=nilai_hsv['sat_mean'],
                        val_std=nilai_hsv['val_std'],
                        val_mean=nilai_hsv['val_mean']
                    )
                    db.session.add(db_hsv)
                    db.session.commit()
                    
                    # Simpan ke tabel Dataset
                    db_dataset = Dataset(
                        gambar=db_gambar.id,
                        kelas=db_label,
                        nilai_hsv=db_hsv.id,
                        nilai_glcm=db_glcm.id
                    )
                    db.session.add(db_dataset)
                    db.session.commit()
                    
                    total_seeded += 1
                    if (i + 1) % 10 == 0 or (i + 1) == len(files):
                        print(f"  -> Berhasil memproses {i + 1}/{len(files)} file...")
                        
                except Exception as e:
                    db.session.rollback()
                    # Hapus file jika gagal diproses agar tidak menumpuk sampah
                    if os.path.exists(dest_file_path):
                        try:
                            os.remove(dest_file_path)
                        except:
                            pass
                    print(f"  [ERROR] Gagal memproses file {filename}: {str(e)}")
                    
        print(f"Selesai! Berhasil mengunggah total {total_seeded} dataset ke database.")

if __name__ == '__main__':
    main()
