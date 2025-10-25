# _4_rag.py
from _2_db import get_session
from _1_models import Phone
from sqlalchemy import select
from sqlalchemy import func

class RAG:
    def __init__(self):
        pass

    def get_specs(self, model_name):
        session = get_session()
        try:
            stmt = select(Phone).where(
                func.replace(func.lower(Phone.model_name), ' ', '').like(
                    f"%{model_name.lower().replace(' ', '').replace('-', '')}%")
            )

            # stmt = select(Phone).where(Phone.model_name.ilike(f"%{model_name}%"))
            result = session.execute(stmt).scalars().all()

            out = []
            for p in result:
                out.append({
                    'model_name': p.model_name,
                    'release_date': p.release_date.isoformat() if p.release_date else None,
                    'display': p.display,
                    'battery': p.battery,
                    'camera': p.camera,
                    'ram': p.ram,
                    'storage': p.storage,
                    'price_usd': float(p.price_usd) if p.price_usd else None,
                    'source_url': p.source_url
                })
            return out
        finally:
            session.close()

    def find_best_battery_under(self, price_limit):
        session = get_session()
        try:
            stmt = (
                select(Phone)
                .where(Phone.price_usd != None)
                .where(Phone.price_usd <= price_limit)
                .order_by(Phone.battery.desc().nullslast())
            )
            phone = session.execute(stmt).scalars().first()
            if not phone:
                return None
            return {
                'model_name': phone.model_name,
                'battery': phone.battery,
                'price_usd': float(phone.price_usd) if phone.price_usd else None,
                'source_url': phone.source_url
            }
        finally:
            session.close()
