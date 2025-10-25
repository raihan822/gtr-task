# rag.py
from db import get_session
from models import Phone

class RAG:
    def __init__(self):
        pass

    def get_specs(self, model_name):
        session = get_session()
        try:
            q = session.query(Phone).filter(Phone.model_name.ilike(f"%{model_name}%"))
            result = q.all()
            # return list of dicts (could be >1 if multiple variants)
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
            q = session.query(Phone).filter(Phone.price_usd != None).filter(Phone.price_usd <= price_limit)
            q = q.order_by(Phone.battery.desc().nullslast())
            phone = q.first()
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