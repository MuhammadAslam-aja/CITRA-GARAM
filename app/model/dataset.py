from app import db


class Dataset(db.Model):
    __tablename__ = 'tb_dataset'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    gambar = db.Column(db.Integer, db.ForeignKey('tb_gambar.id'), nullable=False)
    kelas = db.Column(db.String(25), nullable=False)
    nilai_hsv = db.Column(db.Integer, db.ForeignKey('tb_hsv.id'), nullable=False)
    nilai_glcm = db.Column(db.Integer, db.ForeignKey('tb_glcm.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())

    def __repr__(self):
        return '<Dataset {}>'.format(self.id)
