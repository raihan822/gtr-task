# _2_db.py (SQLAlchemy 2.0+ style)
# connects the db:
import os
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from _1_models import Base, Phone

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:db123@localhost:5432/samsung_advisor')

engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_session():
    return SessionLocal()

def get_phone_by_model(session, model_name):
    stmt = select(Phone).where(Phone.model_name.ilike(f"%{model_name}%"))
    return session.scalars(stmt).first()

if __name__ == '__main__':
    init_db()
    print('DB initialized')
