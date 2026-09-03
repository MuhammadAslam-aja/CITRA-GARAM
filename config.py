import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    HOST = os.environ.get("DB_HOST") or os.environ.get("MYSQLHOST") or "127.0.0.1"
    PORT = os.environ.get("DB_PORT") or os.environ.get("MYSQLPORT") or "3306"
    DB = os.environ.get("DB_DATABASE") or os.environ.get("MYSQLDATABASE") or "db_citra_garam"
    USER = os.environ.get("DB_USERNAME") or os.environ.get("MYSQLUSER") or "root"
    PASSWORD = os.environ.get("DB_PASSWORD") or os.environ.get("MYSQLPASSWORD") or ""

    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY") or "rzylord"
    SECRET_KEY = os.environ.get("SECRET_KEY") or JWT_SECRET_KEY

    # Build URI for SQLAlchemy
    mysql_url = os.environ.get("MYSQL_URL") or os.environ.get("MYSQL_PRIVATE_URL")
    if mysql_url:
        SQLALCHEMY_DATABASE_URI = mysql_url.replace("mysql://", "mysql+pymysql://")
    else:
        if ":" in HOST:
            SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{USER}:{PASSWORD}@{HOST}/{DB}"
        else:
            SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True

    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER") or "upload"
