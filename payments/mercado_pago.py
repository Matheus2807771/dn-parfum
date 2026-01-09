import os
import mercadopago
from datetime import datetime, timedelta

sdk = mercadopago.SDK(os.getenv("MP_ACCESS_TOKEN"))

def criar_pagamento_pix(valor: float, descricao: str, email: str, referencia: str):
    body = {
        "transaction_amount": float(valor),
        "description": descricao,
        "payment_method_id": "pix",
        "payer": {"email": email},
        "external_reference": referencia,
        "date_of_expiration": (datetime.utcnow() + timedelta(minutes=30)).isoformat()
    }
    result = sdk.payment().create(body)
    return result["response"]
