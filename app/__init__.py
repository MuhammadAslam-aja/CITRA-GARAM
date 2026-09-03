import os
from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = app.config['SECRET_KEY']

db = SQLAlchemy(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.login_view = 'logins'
login_manager.init_app(app)

from app.model import user, gambar, dataset, glcm, klasifikasi
from app import routes


def auto_init_database():
    try:
        with app.app_context():
            # 1. Ensure tables exist
            db.create_all()

            # 2. Ensure admin user exists
            from app.model.user import User
            admin_user = User.query.filter_by(username='admin').first()
            if not admin_user:
                print("Admin user missing! Creating default admin user...")
                new_admin = User(nama='Administrator', username='admin', plain_password='password123')
                new_admin.set_password('password123')
                db.session.add(new_admin)
                db.session.commit()
                print("Admin user created successfully!")

            # 3. Import dataset if dataset table is empty
            from app.model.dataset import Dataset
            if Dataset.query.count() == 0:
                print("Dataset empty! Importing db_citra_garam.sql dump...")
                sql_file = os.path.join(app.root_path, '..', 'db_citra_garam.sql')
                if os.path.exists(sql_file):
                    from sqlalchemy import text
                    with open(sql_file, 'r', encoding='utf-8') as f:
                        sql_text = f.read()

                    with db.engine.connect() as conn:
                        trans = conn.begin()
                        try:
                            conn.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
                            statement = ""
                            for line in sql_text.splitlines():
                                line_str = line.strip()
                                if line_str.startswith('--') or line_str.startswith('/*') or not line_str or line_str.startswith('LOCK') or line_str.startswith('UNLOCK'):
                                    continue
                                statement += "\n" + line
                                if line_str.endswith(';'):
                                    try:
                                        conn.execute(text(statement))
                                    except Exception as stmt_e:
                                        pass
                                    statement = ""
                            conn.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
                            trans.commit()
                            print("Dataset dump import completed!")
                        except Exception as e:
                            trans.rollback()
                            print(f"Error during dump import: {e}")

    except Exception as ex:
        import traceback
        print(f"Auto-init exception: {ex}")
        traceback.print_exc()

auto_init_database()