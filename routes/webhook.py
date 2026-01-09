from flask import Blueprint, request
import os
import mercadopago

bp = Blueprint("webhook", __name__)
sdk = mercadopago.SDK(os.getenv("MP_ACCESS_TOKEN"))

@bp.route("/webhook/mercadopago", methods=["POST"])
def webhook_mp():
    payload = request.json or {}
    if payload.get("type") == "payment":
        payment_id = payload["data"]["id"]
        pagamento = sdk.payment().get(payment_id)["response"]

        status = pagamento["status"]  # approved | pending | rejected
        referencia = pagamento.get("external_reference")

        # TODO: atualizar status no Supabase usando 'referencia'
        # approved -> liberar pedido

    return "OK", 200
