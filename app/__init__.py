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
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()

            # Check if tables are missing
            if 'tb_dataset' not in tables or 'tb_user' not in tables or 'tb_gambar' not in tables:
                print("Database tables missing! Initializing database from db_citra_garam.sql dump...")
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

                        # Organize CREATE and INSERT statements in strict dependency order
                        create_stmts = [s for s in statements if 'CREATE TABLE' in s or 'DROP TABLE' in s]
                        insert_gambar = [s for s in statements if '`tb_gambar`' in s and 'INSERT INTO' in s]
                        insert_hsv = [s for s in statements if '`tb_hsv`' in s and 'INSERT INTO' in s]
                        insert_glcm = [s for s in statements if '`tb_glcm`' in s and 'INSERT INTO' in s]
                        insert_user = [s for s in statements if '`tb_user`' in s and 'INSERT INTO' in s]
                        insert_dataset = [s for s in statements if '`tb_dataset`' in s and 'INSERT INTO' in s]
                        insert_klasifikasi = [s for s in statements if '`tb_klasifikasi`' in s and 'INSERT INTO' in s]
                        other_stmts = [s for s in statements if s not in create_stmts and s not in insert_gambar and s not in insert_hsv and s not in insert_glcm and s not in insert_user and s not in insert_dataset and s not in insert_klasifikasi]

                        ordered_stmts = (
                            create_stmts +
                            insert_gambar +
                            insert_hsv +
                            insert_glcm +
                            insert_user +
                            insert_dataset +
                            insert_klasifikasi +
                            other_stmts
                        )

                        for stmt in ordered_stmts:
                            try:
                                cursor.execute(stmt)
                            except Exception as stmt_e:
                                print(f"Stmt notice: {stmt_e}")

                        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
                        raw_conn.commit()
                        print("Successfully created tables and populated database from db_citra_garam.sql!")
                    except Exception as e:
                        raw_conn.rollback()
                        print(f"Error during raw dump import: {e}")
                    finally:
                        raw_conn.close()

            # Ensure all tables via SQLAlchemy ORM as backup
            db.create_all()

            # Ensure admin user exists
            from app.model.user import User
            admin_user = User.query.filter_by(username='admin').first()
            if not admin_user:
                new_admin = User(nama='Administrator', username='admin', plain_password='password123')
                new_admin.set_password('password123')
                db.session.add(new_admin)
                db.session.commit()

    except Exception as ex:
        import traceback
        print(f"Auto-init exception: {ex}")
        traceback.print_exc()

# Run database auto-init in a background daemon thread
threading.Thread(target=auto_init_database, daemon=True).start()