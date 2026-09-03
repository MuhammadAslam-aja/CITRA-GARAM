from app import db
from sqlalchemy import Date


class Klasifikasi(db.Model):
    __tablename__ = 'tb_klasifikasi'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    gambar = db.Column(db.Integer, db.ForeignKey('tb_gambar.id'))
    jarak = db.Column(db.Float)
    kelas = db.Column(db.String(25), nullable=False)
    nilai_hsv = db.Column(db.Integer, db.ForeignKey('tb_hsv.id'))
    nilai_glcm = db.Column(db.Integer, db.ForeignKey('tb_glcm.id'))
    nilai_akurasi = db.Column(db.Float)
    tanggal_klasifikasi = db.Column(Date)

    def __init__(self, gambar, nilai_hsv, nilai_glcm, jarak, kelas, nilai_akurasi, tanggal_klasifikasi):
        self.gambar = gambar
        self.jarak = jarak
        self.kelas = kelas
        self.nilai_hsv = nilai_hsv
        self.nilai_glcm = nilai_glcm
        self.nilai_akurasi = nilai_akurasi
        self.tanggal_klasifikasi = tanggal_klasifikasi
