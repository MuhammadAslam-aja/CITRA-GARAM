import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    HOST = str(os.environ.get("DB_HOST"))
    DB = str(os.environ.get("DB_DATABASE"))
    USER = str(os.environ.get("DB_USERNAME"))
    PASSWORD = str(os.environ.get("DB_PASSWORD"))

    JWT_SECRET_KEY = str(os.environ.get("JWT_SECRET_KEY"))
    SECRET_KEY = str(os.environ.get("JWT_SECRET_KEY"))

    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{USER}:{PASSWORD}@{HOST}/{DB}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True

    # SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://db_am:12345678@localhost:3306/db_am"

    UPLOAD_FOLDER = str(os.environ.get("UPLOAD_FOLDER"))
