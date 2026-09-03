from app import db

class Gambar(db.Model):
    __tablename__ = 'tb_gambar'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    gambar = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return '<Gambar {}>'.format(self.id)