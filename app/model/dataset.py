from app import db


class Dataset(db.Model):
    __tablename__ = 'tb_dataset'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    gambar = db.Column(db.Integer, index=True, unique=True, nullable=False)
    kelas = db.Column(db.String(25), nullable=False)
    nilai_hsv = db.Column(db.Integer, index=True, unique=True, nullable=False)
    nilai_glcm = db.Column(db.Integer, index=True, unique=True, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    
    nilai_hsv = db.Column(db.Integer, db.ForeignKey('tb_hsv.id'))
    nilai_glcm = db.Column(db.Integer, db.ForeignKey('tb_glcm.id'))
    gambar = db.Column(db.Integer, db.ForeignKey('tb_gambar.id'))

    def __repr__(self):
        return '<Dataset {}>'.format(self.id)
