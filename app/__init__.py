import os
from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.login_view = 'logins'
login_manager.init_app(app)

from app.model import user, gambar, dataset, glcm, klasifikasi
from app import routes


def auto_init_database():
    try:
        from sqlalchemy import inspect, text
        with app.app_context():
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            if 'tb_user' not in tables or 'tb_dataset' not in tables:
                print("Database empty or missing tables! Auto-importing db_citra_garam.sql...")
                sql_file = os.path.join(app.root_path, '..', 'db_citra_garam.sql')
                if os.path.exists(sql_file):
                    with open(sql_file, 'r', encoding='utf-8') as f:
                        sql_text = f.read()

                    with db.engine.connect() as conn:
                        trans = conn.begin()
                        try:
                            conn.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
                            statement = ""
                            for line in sql_text.splitlines():
                                line_str = line.strip()
                                if line_str.startswith('--') or line_str.startswith('/*') or not line_str:
                                    continue
                                statement += "\n" + line
                                if line_str.endswith(';'):
                                    conn.execute(text(statement))
                                    statement = ""
                            conn.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
                            trans.commit()
                            print("Successfully auto-imported db_citra_garam.sql into Railway MySQL database!")
                        except Exception as e:
                            trans.rollback()
                            print(f"Error executing auto-import SQL: {e}")
    except Exception as ex:
        print(f"Auto-init check notice: {ex}")

auto_init_database()