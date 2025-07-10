from sqlmodel import text, create_engine
from app.config import DATABASE_URL

def upgrade():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'urls' AND column_name = 'password'
        """))
        
        if not result.fetchone():
            conn.execute(text("ALTER TABLE urls ADD COLUMN password VARCHAR"))
            conn.commit()

if __name__ == "__main__":
    upgrade()
