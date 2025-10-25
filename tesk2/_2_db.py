# db.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from _1_models import Base, Phone

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/samsung_advisor')

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_session():
    return SessionLocal()

# convenience helper
def get_phone_by_model(session, model_name):
    return session.query(Phone).filter(Phone.model_name.ilike(f"%{model_name}%")).first()


if __name__ == '__main__':
    init_db()
    print('DB initialized')