from app import db


class GLCM(db.Model):
    __tablename__ = 'tb_glcm'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    energi = db.Column(db.Float, nullable=False)
    homogenitas = db.Column(db.Float, nullable=False)
    kontras = db.Column(db.Float, nullable=False)
    korelasi = db.Column(db.Float, nullable=False)
    dismilaritas = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return '<GLCM %r>' % self.id
