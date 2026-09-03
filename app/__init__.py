import os
import threading
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
            # 1. Ensure all tables exist
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
                print("Dataset empty! Auto-importing db_citra_garam.sql dump via raw DBAPI connection...")
                sql_file = os.path.join(app.root_path, '..', 'db_citra_garam.sql')
                if os.path.exists(sql_file):
                    raw_conn = db.engine.raw_connection()
                    try:
                        cursor = raw_conn.cursor()
                        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
                        with open(sql_file, 'r', encoding='utf-8') as f:
                            full_sql = f.read()

                        # Collect clean SQL statements
                        statements = []
                        current_stmt = ""
                        for line in full_sql.splitlines():
                            line_str = line.strip()
                            if line_str.startswith('--') or line_str.startswith('/*') or not line_str or line_str.startswith('LOCK') or line_str.startswith('UNLOCK'):
                                continue
                            current_stmt += "\n" + line
                            if line_str.endswith(';'):
                                statements.append(current_stmt)
                                current_stmt = ""

                        # Execute statements
                        for stmt in statements:
                            try:
                                cursor.execute(stmt)
                            except Exception as stmt_e:
                                print(f"Stmt notice: {stmt_e}")

                        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
                        raw_conn.commit()
                        print("Dataset dump import completed via raw DBAPI!")
                    except Exception as e:
                        raw_conn.rollback()
                        print(f"Error during raw dump import: {e}")
                    finally:
                        raw_conn.close()

    except Exception as ex:
        import traceback
        print(f"Auto-init exception: {ex}")
        traceback.print_exc()

# Run database auto-init in a background daemon thread to prevent Gunicorn worker startup timeout
threading.Thread(target=auto_init_database, daemon=True).start()