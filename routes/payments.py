from flask import Blueprint, request, jsonify
from payments.mercado_pago import criar_pagamento_pix

bp = Blueprint("pagamentos", __name__)

@bp.route("/api/pagamentos/pix", methods=["POST"])
def pagamento_pix():
    data = request.get_json(force=True)

    pagamento = criar_pagamento_pix(
        valor=data["valor"],
        descricao=data["descricao"],
        email=data["email"],
        referencia=data["pedido_id"]
    )

    pix = pagamento["point_of_interaction"]["transaction_data"]

    return jsonify({
        "payment_id": pagamento["id"],
        "status": pagamento["status"],
        "qr_code": pix["qr_code"],
        "qr_code_base64": pix["qr_code_base64"],
        "copiar_colar": pix["qr_code"]
    })
