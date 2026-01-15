from flask import Flask, render_template, jsonify, request, redirect, url_for, session
import json, os, requests, re, unicodedata
import mercadopago
from datetime import datetime, timedelta
from supabase import create_client, Client


app = Flask(
    __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/static'
)

app.secret_key = 'amakha_paris_secret_key_2024'


# ================= SUPABASE =================

SUPABASE_URL = "https://lgyghutifnhhtctnmqia.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxneWdodXRpZm5oaHRjdG5tcWlhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjcwMTY5NTcsImV4cCI6MjA4MjU5Mjk1N30.P9XNkCNExfuXAxLZyULIcP3AgZzpXLnbhaCx4qHFJzc"


supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ================= MERCADO PAGO =================

MP_ACCESS_TOKEN = os.getenv("MP_ACCESS_TOKEN")

if not MP_ACCESS_TOKEN:
    raise RuntimeError("MP_ACCESS_TOKEN não configurado")

sdk = mercadopago.SDK(MP_ACCESS_TOKEN)

# ================= CONFIG =================

CONFIG_FILE = "config.json"

# DEFAULT_CONFIG guarda também os kits (que continuam locais/JSON)
DEFAULT_CONFIG = {
    "whatsapp": "5519984242807",
    "cep_origem": "13088221",
    "admin_password": "amakha2024",

    "kits": {
        "2":  {"preco": 49.90, "ativo": True},
        "5":  {"preco": 89.90, "ativo": True},
        "10": {"preco": 179.90, "ativo": True},
        "15": {"preco": 279.90, "ativo": True},
        "20": {"preco": 369.90, "ativo": True},
        "30": {"preco": 565.90, "ativo": True},
        "50": {"preco": 819.90, "ativo": True},
        "100": {"preco": 1490.00, "ativo": True},
        "250": {"preco": 3890.00, "ativo": True}
    }
}


def load_config():
    """
    Carrega a configuração completa:
    - Começa do DEFAULT_CONFIG
    - Sobrepõe com o JSON (kits + overrides)
    - Sobrepõe com o Supabase (configuracoes_sistema, 1ª linha que encontrar)
      para whatsapp, cep_origem e admin_password.
    Banco é a fonte principal desses campos.
    """
    # base: cópia profunda simples
    config = json.loads(json.dumps(DEFAULT_CONFIG))

    # 1) JSON local (backup + kits)
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                local_cfg = json.load(f)
                for k, v in local_cfg.items():
                    if k == "kits" and isinstance(v, dict):
                        config["kits"].update(v)
                    else:
                        config[k] = v
        except Exception as e:
            print("Erro ao ler config.json:", e)

    # 2) Supabase (principal para campos principais)
    try:
        resp = (
            supabase
            .table("configuracoes_sistema")
            .select("*")
            .limit(1)
            .execute()
        )
        if resp.data:
            row = resp.data[0]
            if row.get("whatsapp") is not None:
                config["whatsapp"] = row["whatsapp"]
            if row.get("cep_origem") is not None:
                config["cep_origem"] = row["cep_origem"]
            if row.get("admin_password") is not None:
                config["admin_password"] = row["admin_password"]
    except Exception as e:
        print("Erro ao carregar config do Supabase, usando somente JSON/default:", e)

    return config


def save_config(config):
    """
    Salva:
    - JSON local (tudo, inclusive kits)
    - Supabase (apenas whatsapp, cep_origem, admin_password) na tabela configuracoes_sistema
      Usando: se já existir uma linha, faz UPDATE; se não, faz INSERT.
      Não envia 'id' no INSERT para não quebrar identity (GENERATED ALWAYS).
    """
    # carrega configuração atual e aplica overrides recebidos
    cfg = load_config()
    cfg.update(config)

    # 1) Salvar JSON (kits + demais campos)
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print("Erro ao salvar config.json:", e)

    # 2) Salvar no Supabase (fonte principal dos campos principais)
    try:
        dados_db = {
            "whatsapp": cfg.get("whatsapp"),
            "cep_origem": cfg.get("cep_origem"),
            "admin_password": cfg.get("admin_password")
        }

        # Verifica se já existe alguma linha
        existente = (
            supabase
            .table("configuracoes_sistema")
            .select("id")
            .limit(1)
            .execute()
        )

        if existente.data:
            row_id = existente.data[0]["id"]
            supabase.table("configuracoes_sistema")\
                .update(dados_db)\
                .eq("id", row_id)\
                .execute()
        else:
            # Inserção sem id -> identity do banco gera o valor
            supabase.table("configuracoes_sistema")\
                .insert(dados_db)\
                .execute()

    except Exception as e:
        print("Erro ao salvar config no Supabase:", e)


# Inicializa JSON/Supabase com DEFAULT_CONFIG se ainda não houver nada local
if not os.path.exists(CONFIG_FILE):
    save_config(DEFAULT_CONFIG)

CONFIG = load_config()


# ================= NORMALIZAÇÃO =================

def sanitizar_nome(nome: str) -> str:
    if not nome:
        return ""
    nome = re.sub(r"[\'’´`]", "", nome)
    nome = unicodedata.normalize("NFKD", nome)
    nome = "".join(c for c in nome if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", nome).strip()


# ================= PÁGINAS SITE =================

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/kit")
def kit():
    config = load_config()
    kits_ativos = {k: v for k, v in config["kits"].items() if v.get("ativo", True)}
    kits_dict = {int(k): v["preco"] for k, v in kits_ativos.items()}
    return render_template("index.html", kits=kits_dict, whatsapp=config["whatsapp"])


# ================= API SITE =================

@app.route("/api/perfumes")
def api_perfumes():
    result = supabase.table("perfumes")\
        .select("*")\
        .eq("ativo", True)\
        .order("nome", desc=False)\
        .execute()

    return jsonify(result.data)


@app.route("/api/kits")
def api_kits():
    config = load_config()
    kits_ativos = {k: v for k, v in config["kits"].items() if v.get("ativo", True)}
    return jsonify(kits_ativos)


# ================= REGISTRAR PEDIDO =================

@app.route("/api/registrar-pedido", methods=["POST"])
def registrar_pedido():
    try:
        data = request.json

        pedido = {
            "kit_quantidade": int(data.get("kit_quantidade", 0)),
            "kit_preco": float(data.get("kit_preco", 0)),
            "cliente_nome": data.get("cliente_nome", ""),
            "cliente_telefone": data.get("cliente_telefone", ""),
            "cliente_cep": data.get("cliente_cep", ""),
            "cliente_cidade": data.get("cliente_cidade", ""),
            "cliente_uf": data.get("cliente_uf", ""),

            # Endereço completo (só funciona se você rodou o SQL no Supabase)
            "cliente_rua": data.get("cliente_rua", ""),
            "cliente_numero": data.get("cliente_numero", ""),
            "cliente_bairro": data.get("cliente_bairro", ""),
            "cliente_complemento": data.get("cliente_complemento", ""),

            "frete_valor": float(data.get("frete_valor", 0)),
            "frete_tipo": data.get("frete_tipo", ""),
            "valor_total": float(data.get("valor_total", 0)),
            "status": "pendente"
        }


        result = supabase.table("pedidos").insert(pedido).execute()
        pedido_id = result.data[0]["id"]

        for p in data.get("perfumes", []):
            supabase.table("pedido_itens").insert({
                "pedido_id": pedido_id,
                "perfume_nome": sanitizar_nome(p.get("nome", "")),
                "perfume_categoria": p.get("categoria", ""),
                "quantidade": p.get("quantidade", 1)
            }).execute()

        return {"sucesso": True, "pedido_id": pedido_id}

    except Exception as e:
        print("ERRO AO REGISTRAR PEDIDO:", e)
        return {"erro": str(e)}, 500


# ================= LOGIN ADMIN =================

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        password = request.form.get("password", "")
        if password == load_config().get("admin_password", ""):
            session["admin_logged"] = True
            return redirect("/admin")
        return render_template("admin_login.html", erro="Senha incorreta")

    return render_template("admin_login.html")


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged", None)
    return redirect("/")


@app.route("/admin")
def admin_dashboard():
    if not session.get("admin_logged"):
        return redirect("/admin/login")

    return render_template("admin_dashboard.html", config=load_config())


# ================= ADMIN — KITS =================

@app.route("/api/admin/kits", methods=["GET"])
def admin_kits_get():
    if not session.get("admin_logged"):
        return {"erro": "Não autorizado"}, 401

    return jsonify(load_config()["kits"])


@app.route("/api/admin/kits", methods=["POST"])
def admin_kits_post():
    if not session.get("admin_logged"):
        return {"erro": "Não autorizado"}, 401

    data = request.json
    config = load_config()

    qtd = str(data["quantidade"])
    config["kits"][qtd] = {"preco": float(data["preco"]), "ativo": True}

    save_config(config)
    return {"sucesso": True}


@app.route("/api/admin/kits/<qtd>", methods=["PUT"])
def admin_kits_put(qtd):
    if not session.get("admin_logged"):
        return {"erro": "Não autorizado"}, 401

    config = load_config()
    if qtd not in config["kits"]:
        return {"erro": "Kit não encontrado"}, 404

    config["kits"][qtd].update(request.json)
    save_config(config)

    return {"sucesso": True}


@app.route("/api/admin/kits/<qtd>", methods=["DELETE"])
def admin_kits_delete(qtd):
    if not session.get("admin_logged"):
        return {"erro": "Não autorizado"}, 401

    config = load_config()

    if qtd in config["kits"]:
        del config["kits"][qtd]
        save_config(config)

    return {"sucesso": True}


# ================= ADMIN — CONFIG GERAIS (CEP / WHATSAPP / SENHA) =================

@app.route("/api/admin/config", methods=["PUT"])
def admin_config_put():
    if not session.get("admin_logged"):
        return {"erro": "Não autorizado"}, 401

    data = request.json or {}

    config = load_config()

    cep = re.sub(r"\D", "", data.get("cep_origem", "") or "")
    whatsapp = re.sub(r"\D", "", data.get("whatsapp", "") or "")
    nova_senha = data.get("nova_senha", "")

    if cep:
        config["cep_origem"] = cep
    if whatsapp:
        config["whatsapp"] = whatsapp
    if nova_senha:
        config["admin_password"] = nova_senha

    save_config(config)

    return {"sucesso": True}


# ================= ADMIN — PERFUMES =================

@app.route("/api/admin/perfumes", methods=["GET"])
def admin_perfumes_get():
    if not session.get("admin_logged"):
        return {"erro": "Não autorizado"}, 401

    result = supabase.table("perfumes") \
        .select("*") \
        .order("nome", desc=False) \
        .execute()

    return jsonify(result.data)


@app.route("/api/admin/perfumes", methods=["POST"])
def admin_perfumes_post():
    if not session.get("admin_logged"):
        return {"erro": "Não autorizado"}, 401

    data = request.json

    novo = {
        "nome": sanitizar_nome(data.get("nome", "")),
        "categoria": data.get("categoria", ""),
        "ml": data.get("ml", "15ml"),
        "ativo": True
    }

    supabase.table("perfumes").insert(novo).execute()

    return {"sucesso": True}


@app.route("/api/admin/perfumes/<int:id>", methods=["PUT"])
def admin_perfumes_put(id):
    if not session.get("admin_logged"):
        return {"erro": "Não autorizado"}, 401

    data = request.json
    update = {}

    if "nome" in data:
        update["nome"] = sanitizar_nome(data["nome"])

    if "categoria" in data:
        update["categoria"] = data["categoria"]

    if "ml" in data:
        update["ml"] = data["ml"]

    if "ativo" in data:
        update["ativo"] = data["ativo"]

    supabase.table("perfumes") \
        .update(update) \
        .eq("id", id) \
        .execute()

    return {"sucesso": True}


@app.route("/api/admin/perfumes/<int:id>", methods=["DELETE"])
def admin_perfumes_delete(id):
    if not session.get("admin_logged"):
        return {"erro": "Não autorizado"}, 401

    supabase.table("perfumes") \
        .delete() \
        .eq("id", id) \
        .execute()

    return {"sucesso": True}


# ================= ADMIN — ATUALIZAR STATUS PEDIDO =================

@app.route("/api/admin/pedidos/<int:pedido_id>/status", methods=["PUT"])
def admin_atualizar_status(pedido_id):
    """
    Atualiza o campo 'status' do pedido na tabela 'pedidos'.
    Espera JSON: { "status": "pendente" | "confirmado" | "cancelado" }
    """
    if not session.get("admin_logged"):
        return {"erro": "Não autorizado"}, 401

    data = request.json or {}
    novo_status = (data.get("status") or "").lower()

    if novo_status not in ["pendente", "confirmado", "cancelado"]:
        return {"erro": "Status inválido"}, 400

    supabase.table("pedidos") \
        .update({"status": novo_status}) \
        .eq("id", pedido_id) \
        .execute()

    return {"sucesso": True, "status": novo_status}



# ================= RELATÓRIOS ADMIN =================

def to_float(v):
    try:
        return float(v)
    except Exception:
        return 0.0


@app.route("/api/admin/relatorios/resumo")
def admin_relatorio_resumo():
    if not session.get("admin_logged"):
        return {"erro": "Não autorizado"}, 401

    # Brasil = UTC-3
    hoje = (datetime.utcnow() - timedelta(hours=3)).date()
    mes_ini = hoje.replace(day=1)

    pedidos = supabase.table("pedidos").select("*").execute().data or []

    def data_pedido(p):
        return datetime.fromisoformat(p["created_at"].replace("Z", "")).date()

    valor_total = sum(
        to_float(p.get("valor_total")) for p in pedidos
    )

    pedidos_mes = [
        p for p in pedidos
        if data_pedido(p) >= mes_ini
    ]

    valor_mes = sum(
        to_float(p.get("valor_total")) for p in pedidos_mes
    )

    pedidos_hoje = [
        p for p in pedidos
        if data_pedido(p) == hoje
    ]

    valor_hoje = sum(
        to_float(p.get("valor_total")) for p in pedidos_hoje
    )

    return {
        "valor_total": valor_total,
        "total_pedidos": len(pedidos),
        "valor_mes": valor_mes,
        "pedidos_mes": len(pedidos_mes),
        "valor_hoje": valor_hoje,
        "pedidos_hoje": len(pedidos_hoje)
    }

@app.route("/api/admin/relatorios/kits-mais-vendidos")
def admin_relatorio_kits():
    if not session.get("admin_logged"):
        return {"erro": "Não autorizado"}, 401

    pedidos = (
        supabase
        .table("pedidos")
        .select("kit_quantidade, valor_total")
        .eq("status", "confirmado")
        .execute()
        .data
    )

    ranking = {}

    for p in pedidos:
        kit = int(p["kit_quantidade"])
        ranking.setdefault(kit, {"quantidade_vendida": 0})
        ranking[kit]["quantidade_vendida"] += 1

    resultado = [
        {
            "kit_quantidade": k,
            "quantidade_vendida": v["quantidade_vendida"]
        }
        for k, v in sorted(
            ranking.items(),
            key=lambda x: x[1]["quantidade_vendida"],
            reverse=True
        )
    ]

    return jsonify(resultado)




@app.route("/api/admin/relatorios/perfumes-mais-vendidos")
def admin_relatorio_perfumes():
    itens = supabase.table("pedido_itens").select("*").execute().data

    ranking = {}

    for i in itens:
        nome = i["perfume_nome"]
        ranking[nome] = ranking.get(nome, 0) + int(i.get("quantidade", 1))

    result = [
        {"perfume": k, "quantidade": v}
        for k, v in sorted(ranking.items(), key=lambda x: x[1], reverse=True)
    ]

    return jsonify(result)


@app.route("/api/admin/relatorios/vendas-por-periodo")
def admin_relatorio_periodo():
    if not session.get("admin_logged"):
        return {"erro": "Não autorizado"}, 401

    # Ajuste para horário do Brasil (UTC-3)
    hoje = (datetime.utcnow() - timedelta(hours=3)).date()
    inicio = hoje - timedelta(days=30)

    pedidos = supabase.table("pedidos").select("*").execute().data or []

    dias = {}

    for p in pedidos:
        try:
            data_pedido = datetime.fromisoformat(
                p["created_at"].replace("Z", "")
            ).date()
        except Exception:
            continue

        if data_pedido < inicio:
            continue

        chave = data_pedido.isoformat()
        dias[chave] = dias.get(chave, 0) + to_float(p.get("valor_total"))

    retorno = [
        {"data": data, "valor": valor}
        for data, valor in sorted(dias.items())
    ]

    return jsonify(retorno)


@app.route("/api/admin/relatorios/pedidos-recentes")
def admin_relatorio_pedidos():
    pedidos = supabase.table("pedidos")\
        .select("*")\
        .order("created_at", desc=True)\
        .limit(50)\
        .execute().data

    return jsonify(pedidos)

# ================= ADMIN — ENTREGA (FRETE DEFINIDO NO ADMIN) =================

@app.route("/api/admin/pedidos/<int:pedido_id>/entrega", methods=["PUT"])
def admin_atualizar_entrega(pedido_id):
    """
    Define entrega no admin:
    Espera JSON:
    {
      "frete_valor": 19.9,
      "frete_tipo": "Correios PAC",
      "observacao_entrega": "Postar amanhã",
      "status": "confirmado"  (opcional)
    }
    """
    if not session.get("admin_logged"):
        return {"erro": "Não autorizado"}, 401

    data = request.json or {}

    frete_valor = 0.0
    try:
        frete_valor = float(data.get("frete_valor", 0) or 0)
    except Exception:
        frete_valor = 0.0

    frete_tipo = (data.get("frete_tipo") or "").strip()
    observacao = (data.get("observacao_entrega") or "").strip()
    novo_status = (data.get("status") or "").strip().lower()  # opcional

    # Busca kit_preco para recalcular valor_total
    pedido_resp = (
        supabase
        .table("pedidos")
        .select("kit_preco")
        .eq("id", pedido_id)
        .limit(1)
        .execute()
    )

    if not pedido_resp.data:
        return {"erro": "Pedido não encontrado"}, 404

    kit_preco = 0.0
    try:
        kit_preco = float(pedido_resp.data[0].get("kit_preco") or 0)
    except Exception:
        kit_preco = 0.0

    valor_total = kit_preco + frete_valor

    payload_update = {
        "frete_valor": frete_valor,
        "frete_tipo": frete_tipo,
        "valor_total": valor_total,
    }

    # Só atualiza se o campo existir no banco (se não existir, Supabase pode falhar).
    # Se você rodou o SQL recomendado, pode salvar observacao_entrega.
    if observacao:
        payload_update["observacao_entrega"] = observacao

    # Status opcional (se vazio, não mexe)
    if novo_status in ["pendente", "confirmado", "cancelado"]:
        payload_update["status"] = novo_status

    supabase.table("pedidos") \
        .update(payload_update) \
        .eq("id", pedido_id) \
        .execute()

    return {"sucesso": True, "pedido_id": pedido_id, "valor_total": valor_total}

@app.route("/api/pagamentos/status/<payment_id>")
def status_pagamento(payment_id):
    pagamento = sdk.payment().get(payment_id)["response"]
    return {"status": pagamento["status"]}

# ================= PAGAMENTO PIX =================
@app.route("/api/pagamentos/pix", methods=["POST"])
def pagamento_pix():
    data = request.get_json(silent=True)

    if not data:
        return {"erro": "JSON inválido ou ausente"}, 400

    # 🔥 FORMATO EXATO EXIGIDO PELO MERCADO PAGO (PIX)
    expiration = (
        datetime.utcnow() - timedelta(hours=3) + timedelta(minutes=30)
    ).strftime("%Y-%m-%dT%H:%M:%S-03:00")

    body = {
        "transaction_amount": float(data["valor"]),
        "description": data.get("descricao", "Pedido DN Parfum"),
        "payment_method_id": "pix",
        "payer": {
            "email": data["email"]
        },
        "external_reference": str(data["pedido_id"]),
        "date_of_expiration": expiration
    }

    result = sdk.payment().create(body)

    if result["status"] not in (200, 201):
        return {
            "erro": "Erro ao criar pagamento",
            "detalhe": result
        }, 500

    pagamento = result["response"]
    pix = pagamento["point_of_interaction"]["transaction_data"]

    return jsonify({
        "payment_id": pagamento["id"],
        "status": pagamento["status"],
        "qr_code": pix["qr_code"],
        "qr_code_base64": pix["qr_code_base64"],
        "copiar_colar": pix["qr_code"]
    })
# ================= WEBHOOK MERCADO PAGO =================

@app.route("/webhook/mercadopago", methods=["POST"])
def webhook_mercadopago():
    payload = request.json or {}

    if payload.get("type") == "payment":
        payment_id = payload["data"]["id"]
        pagamento = sdk.payment().get(payment_id)["response"]

        status = pagamento["status"]
        referencia = pagamento.get("external_reference")

        if status == "approved" and referencia:
            supabase.table("pedidos") \
                .update({"status": "confirmado"}) \
                .eq("id", referencia) \
                .execute()

    return "OK", 200


# ================= RUN =================

if __name__ == "__main__":
    app.run(debug=True)
