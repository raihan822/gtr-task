import pandas as pd
from datetime import datetime
from _2_db import get_session
from _1_models import Phone

CSV_PATH = r"C:\Users\raiha\Downloads\Linux Downloads\Documents & Jobs\Jobs\gtr_phones.csv"

df = pd.read_csv(CSV_PATH)

session = get_session()

try:
    for _, row in df.iterrows():
        exists = session.query(Phone).filter_by(model_name=row["model_name"]).first()
        if exists:
            continue

        # handle created_at safely
        created_at_value = pd.to_datetime(row.get("created_at"), errors='coerce')
        if pd.isna(created_at_value):
            created_at_value = datetime.utcnow()

        phone = Phone(
            model_name=row["model_name"],
            brand=row["brand"],
            release_date=pd.to_datetime(row["release_date"], errors='coerce').date() if pd.notna(
                row.get("release_date")) else None,
            display=row["display"],
            battery=row["battery"],
            camera=row["camera"],
            ram=row["ram"],
            storage=row["storage"],
            price_usd=float(row["price_usd"]) if pd.notna(row["price_usd"]) else None,
            source_url=row["source_url"],
            created_at=created_at_value
        )
        session.add(phone)

    session.commit()
    print("✅ CSV imported successfully!")
except Exception as e:
    session.rollback()
    print("❌ Error:", e)
finally:
    session.close()
