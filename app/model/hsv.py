from app import db


class HSV(db.Model):
    __tablename__ = 'tb_hsv'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    hue_mean = db.Column(db.Float, nullable=False)
    hue_std = db.Column(db.Float, nullable=False)
    sat_mean = db.Column(db.Float, nullable=False)
    sat_std = db.Column(db.Float, nullable=False)
    val_mean = db.Column(db.Float, nullable=False)
    val_std = db.Column(db.Float, nullable=False)

    def __init__(self, hue_mean, hue_std, sat_mean, sat_std, val_mean, val_std):
        self.hue_mean = hue_mean
        self.hue_std = hue_std
        self.sat_mean = sat_mean
        self.sat_std = sat_std
        self.val_mean = val_mean
        self.val_std = val_std

    def __repr__(self):
        return '<HSV %r>' % self.id

    def serialize(self):
        return {
            'id': self.id,
            'hue_mean': self.hue_mean,
            'hue_std': self.hue_std,
            'sat_mean': self.sat_mean,
            'sat_std': self.sat_std,
            'val_mean': self.val_mean,
            'val_std': self.val_std
        }
