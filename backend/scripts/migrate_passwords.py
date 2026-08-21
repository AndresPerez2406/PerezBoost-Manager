import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.core.database import SessionLocal
from backend.core.security import hash_password
from backend.models.booster import Booster

def migrar_contrasenas():
    print("🔒 Iniciando migración criptográfica de contraseñas a Bcrypt...")
    db = SessionLocal()
    try:
        boosters = db.query(Booster).all()
        migrados = 0
        ya_hasheados = 0

        for b in boosters:
            pass_actual = b.password or "1234"
            if not pass_actual.startswith("$2b$") and not pass_actual.startswith("$2a$"):
                nuevo_hash = hash_password(pass_actual)
                b.password = nuevo_hash
                migrados += 1
                print(f"  • Contraseña de '{b.nombre}' migrada a hash Bcrypt.")
            else:
                ya_hasheados += 1

        db.commit()
        print(f"\n✅ Migración completada con éxito:")
        print(f"  • Contraseñas migradas a Bcrypt : {migrados}")
        print(f"  • Contraseñas previamente seguras: {ya_hasheados}")
        print(f"  • Total boosters en sistema      : {len(boosters)}")
    except Exception as e:
        db.rollback()
        print(f"❌ Error durante la migración: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    migrar_contrasenas()
