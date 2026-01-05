from flask import Flask, render_template, jsonify, request, redirect, url_for, session
import json, os, requests
from supabase import create_client, Client
from datetime import datetime, timedelta

app = Flask(
    __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/static'
)

app.secret_key = 'amakha_paris_secret_key_2024'

# ================= SUPABASE CONFIG =================

SUPABASE_URL = "https://lgyghutifnhhtctnmqia.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxneWdodXRpZm5oaHRjdG5tcWlhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjcwMTY5NTcsImV4cCI6MjA4MjU5Mjk1N30.P9XNkCNExfuXAxLZyULIcP3AgZzpXLnbhaCx4qHFJzc"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ================= CONFIG =================

CONFIG_FILE = "config.json"
PERFUMES_FILE = "perfumes_fixos.json"

DEFAULT_CONFIG = {
    "whatsapp": "5519984242807",
    "cep_origem": "13088221",
    "admin_password": "amakha2024",
    "kits": {
        "2": {"preco": 49.90, "ativo": True},
        "5": {"preco": 89.90, "ativo": True},
        "10": {"preco": 179.90, "ativo": True},
        "15": {"preco": 279.90, "ativo": True},
        "20": {"preco": 369.90, "ativo": True},
        "30": {"preco": 565.90, "ativo": True},
        "50": {"preco": 819.90, "ativo": True},
        "100": {"preco": 1490.00, "ativo": True},
        "250": {"preco": 3890.00, "ativo": True}
    },
    "kits_logistica": {
        "2":  {"weight": 0.30, "width": 16, "height": 12, "length": 18},
        "5":  {"weight": 0.50, "width": 18, "height": 12, "length": 18},
        "10": {"weight": 0.80, "width": 18, "height": 12, "length": 18},
        "15": {"weight": 1.00, "width": 20, "height": 15, "length": 20},
        "20": {"weight": 1.20, "width": 22, "height": 16, "length": 22},
        "30": {"weight": 1.80, "width": 24, "height": 18, "length": 24},
        "50": {"weight": 3.00, "width": 26, "height": 20, "length": 28},
        "100": {"weight": 5.50, "width": 30, "height": 22, "length": 32},
        "250": {"weight": 12.00, "width": 40, "height": 35, "length": 40}
    }
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return DEFAULT_CONFIG.copy()

def save_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def load_perfumes():
    if os.path.exists(PERFUMES_FILE):
        with open(PERFUMES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_perfumes(perfumes):
    with open(PERFUMES_FILE, 'w', encoding='utf-8') as f:
        json.dump(perfumes, f, indent=2, ensure_ascii=False)

if not os.path.exists(CONFIG_FILE):
    save_config(DEFAULT_CONFIG)

CONFIG = load_config()
PERFUMES = load_perfumes()

API_URL = "https://melhorenvio.com.br/api/v2/me/shipment/calculate"

ME_HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiIxIiwianRpIjoiYWM2M2QwZGQ3MzIyMWViNmI5ODAyZDc5NzQxNjRkNWVmYzI5MTZmMzI4MGQyYWEzY2JhODQyYmNkMWMzMWFkZTE5MWE2MmNjZDM0NzM1YmYiLCJpYXQiOjE3NjcwOTQzMDYuNzk3NDQ5LCJuYmYiOjE3NjcwOTQzMDYuNzk3NDUsImV4cCI6MTc5ODYzMDMwNi43ODUzNjcsInN1YiI6ImEwOWM1ZGVlLTRmMjQtNDRlYS05Yzk0LWViNTViYWI3YjQzOCIsInNjb3BlcyI6WyJvcmRlcnMtcmVhZCIsInNoaXBwaW5nLWNhbGN1bGF0ZSIsInNoaXBwaW5nLWdlbmVyYXRlIiwic2hpcHBpbmctcHJldmlldyIsInNoaXBwaW5nLXByaW50Iiwic2hpcHBpbmctdHJhY2tpbmciXX0.TtPdSh4qU9MfLpLwHOQNMSqCK8_XbvlLgMIE3fNbcBt0UfX4xK04O8npRwFykRJE3gHnHyaHkkQye4vZuFdQqc_AUyPbi9j-cMv1NFSBlmRCKLei2q5srI2s142FeG2KlkfG7RAGlIL933CnYPLm1czbQz0nrZNBEEoXRCIMmTChIoN7Majp1uqAIO_dRXppAedofvnBaDkXGw_6GuV57F38uJseRnbC9686NY1kN9ZeEjJCetcMQ1MMLLTp1sfMNv7iNEVoqvQVNOn1hf_MRnI7HvUSmFCzlhMu0ZpEQVAYZ_aBUbKjPyQUwVirYNFn2Cj14cyS2LyJyQmm7OChcIrqPS_65V9AP7vWwgglKf5FFUAmqP10ACoBcj4tkxj8knHVdDV6MXggaT26I_XzWrorYFkMFTvB_T5a8wwBO89YwnTFy6Mj0OWqOvsJbTX7UKH7y-FEgkx4c-aiqGR84HUvH1pRKfR4KFAuuI56rNALSBPrO30JlMfJn3LksTYPVdVxR9uNoOvMm1THsV0sLQ5r4Z60dmGIJxqZv3OZUrbnnbcyUvoo9WYiRPfZtqq3jEUEd0MqoEET7prOKupNR--eIMvN9W63i6wRyIUr8o1p2hdirUP9ARMPQxnOESZ7imReWJpNY2n8jD_rtsR1_XckoGWwSjGwJZuO5rQGufY"
}

SERVICOS_CORREIOS = "1,2"
SERVICOS_JADLOG = "3,4,17,18"

IMG_DIR = "static/img_frascos_site"

# ================= NORMALIZAÇÃO =================

def normalizar_dimensoes(pkg):
    pkg = pkg.copy()
    pkg["length"] = max(pkg["length"], 18)
    pkg["width"]  = max(pkg["width"], 12)
    pkg["height"] = max(pkg["height"], 2)
    pkg["weight"] = max(pkg["weight"], 0.3)
    return pkg

# ================= PAGES =================

@app.route("/")
def landing():
    imagens = []
    if os.path.exists(IMG_DIR):
        imagens = [
            f"img_frascos_site/{f}"
            for f in os.listdir(IMG_DIR)
            if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))
        ]
    return render_template("landing.html", imagens=imagens)

@app.route("/kit")
def kit():
    config = load_config()
    kits_ativos = {k: v for k, v in config["kits"].items() if v.get("ativo", True)}
    kits_dict = {int(k): v["preco"] for k, v in kits_ativos.items()}
    return render_template("index.html", kits=kits_dict, whatsapp=config["whatsapp"])

@app.route("/api/perfumes")
def api_perfumes():
    perfumes = load_perfumes()
    perfumes_ativos = [p for p in perfumes if p.get("ativo", True)]
    return jsonify(perfumes_ativos)

@app.route("/api/kits")
def api_kits():
    config = load_config()
    kits_ativos = {k: v for k, v in config["kits"].items() if v.get("ativo", True)}
    return jsonify(kits_ativos)

# ================= REGISTRAR PEDIDO (SUPABASE) =================

@app.route("/api/registrar-pedido", methods=["POST"])
def registrar_pedido():
    try:
        data = request.json
        
        # Inserir pedido
        pedido_data = {
            "kit_quantidade": int(data.get("kit_quantidade", 0)),
            "kit_preco": float(data.get("kit_preco", 0)),
            "cliente_nome": data.get("cliente_nome", ""),
            "cliente_telefone": data.get("cliente_telefone", ""),
            "cliente_cep": data.get("cliente_cep", ""),
            "cliente_cidade": data.get("cliente_cidade", ""),
            "cliente_uf": data.get("cliente_uf", ""),
            "frete_valor": float(data.get("frete_valor", 0)),
            "frete_tipo": data.get("frete_tipo", ""),
            "valor_total": float(data.get("valor_total", 0)),
            "status": "pendente"
        }
        
        result = supabase.table("pedidos").insert(pedido_data).execute()
        pedido_id = result.data[0]["id"]
        
        # Inserir itens do pedido (perfumes)
        perfumes = data.get("perfumes", [])
        for perfume in perfumes:
            item_data = {
                "pedido_id": pedido_id,
                "perfume_nome": perfume.get("nome", ""),
                "perfume_categoria": perfume.get("categoria", ""),
                "quantidade": perfume.get("quantidade", 1)
            }
            supabase.table("pedido_itens").insert(item_data).execute()
        
        return jsonify({"sucesso": True, "pedido_id": pedido_id})
    
    except Exception as e:
        print("Erro ao registrar pedido:", e)
        return {"erro": str(e)}, 500

# ================= RELATÓRIOS (SUPABASE) =================

@app.route("/api/admin/relatorios/resumo")
def api_relatorios_resumo():
    if not session.get("admin_logged"):
        return {"erro": "Não autorizado"}, 401
    
    try:
        # Total de pedidos
        pedidos = supabase.table("pedidos").select("*").execute()
        total_pedidos = len(pedidos.data)
        
        # Valor total vendido
        valor_total = sum([p.get("valor_total", 0) for p in pedidos.data])
        
        # Pedidos hoje
        hoje = datetime.now().strftime("%Y-%m-%d")
        pedidos_hoje = supabase.table("pedidos").select("*").gte("created_at", hoje).execute()
        total_hoje = len(pedidos_hoje.data)
        valor_hoje = sum([p.get("valor_total", 0) for p in pedidos_hoje.data])
        
        # Pedidos este mês
        primeiro_dia_mes = datetime.now().replace(day=1).strftime("%Y-%m-%d")
        pedidos_mes = supabase.table("pedidos").select("*").gte("created_at", primeiro_dia_mes).execute()
        total_mes = len(pedidos_mes.data)
        valor_mes = sum([p.get("valor_total", 0) for p in pedidos_mes.data])
        
        return jsonify({
            "total_pedidos": total_pedidos,
            "valor_total": valor_total,
            "pedidos_hoje": total_hoje,
            "valor_hoje": valor_hoje,
            "pedidos_mes": total_mes,
            "valor_mes": valor_mes
        })
    
    except Exception as e:
        print("Erro ao buscar resumo:", e)
        return {"erro": str(e)}, 500

@app.route("/api/admin/relatorios/kits-mais-vendidos")
def api_kits_mais_vendidos():
    if not session.get("admin_logged"):
        return {"erro": "Não autorizado"}, 401
    
    try:
        pedidos = supabase.table("pedidos").select("kit_quantidade").execute()
        
        # Contar kits
        contagem = {}
        for p in pedidos.data:
            kit = str(p.get("kit_quantidade", 0))
            contagem[kit] = contagem.get(kit, 0) + 1
        
        # Ordenar por quantidade
        resultado = [{"kit": k, "quantidade": v} for k, v in contagem.items()]
        resultado.sort(key=lambda x: x["quantidade"], reverse=True)
        
        return jsonify(resultado[:10])
    
    except Exception as e:
        print("Erro ao buscar kits mais vendidos:", e)
        return {"erro": str(e)}, 500

@app.route("/api/admin/relatorios/perfumes-mais-vendidos")
def api_perfumes_mais_vendidos():
    if not session.get("admin_logged"):
        return {"erro": "Não autorizado"}, 401
    
    try:
        itens = supabase.table("pedido_itens").select("perfume_nome, quantidade").execute()
        
        # Contar perfumes
        contagem = {}
        for item in itens.data:
            nome = item.get("perfume_nome", "")
            qtd = item.get("quantidade", 1)
            contagem[nome] = contagem.get(nome, 0) + qtd
        
        # Ordenar por quantidade
        resultado = [{"perfume": k, "quantidade": v} for k, v in contagem.items()]
        resultado.sort(key=lambda x: x["quantidade"], reverse=True)
        
        return jsonify(resultado[:20])
    
    except Exception as e:
        print("Erro ao buscar perfumes mais vendidos:", e)
        return {"erro": str(e)}, 500

@app.route("/api/admin/relatorios/vendas-por-periodo")
def api_vendas_por_periodo():
    if not session.get("admin_logged"):
        return {"erro": "Não autorizado"}, 401
    
    try:
        # Últimos 30 dias
        data_inicio = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        pedidos = supabase.table("pedidos").select("created_at, valor_total").gte("created_at", data_inicio).execute()
        
        # Agrupar por dia
        vendas_por_dia = {}
        for p in pedidos.data:
            data = p.get("created_at", "")[:10]
            valor = p.get("valor_total", 0)
            if data not in vendas_por_dia:
                vendas_por_dia[data] = {"pedidos": 0, "valor": 0}
            vendas_por_dia[data]["pedidos"] += 1
            vendas_por_dia[data]["valor"] += valor
        
        # Converter para lista ordenada
        resultado = [{"data": k, "pedidos": v["pedidos"], "valor": v["valor"]} for k, v in vendas_por_dia.items()]
        resultado.sort(key=lambda x: x["data"])
        
        return jsonify(resultado)
    
    except Exception as e:
        print("Erro ao buscar vendas por período:", e)
        return {"erro": str(e)}, 500

@app.route("/api/admin/relatorios/pedidos-recentes")
def api_pedidos_recentes():
    if not session.get("admin_logged"):
        return {"erro": "Não autorizado"}, 401
    
    try:
        pedidos = supabase.table("pedidos").select("*").order("created_at", desc=True).limit(50).execute()
        return jsonify(pedidos.data)
    
    except Exception as e:
        print("Erro ao buscar pedidos recentes:", e)
        return {"erro": str(e)}, 500




@app.route("/api/admin/pedidos/<int:pedido_id>/status", methods=["PUT"])
def api_admin_atualizar_status(pedido_id):
    if not session.get("admin_logged"):
        return {"erro": "Não autorizado"}, 401

    data = request.json
    novo_status = data.get("status")

    if novo_status not in ["pendente","confirmado","cancelado"]:
        return {"erro": "Status inválido"}, 400

    try:
        supabase.table("pedidos")\
            .update({"status": novo_status})\
            .eq("id", pedido_id)\
            .execute()

        return {"sucesso": True}

    except Exception as e:
        print("Erro ao atualizar status:", e)
        return {"erro": str(e)}, 500




# ================= ADMIN ROUTES =================

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        password = request.form.get("password", "")
        config = load_config()
        if password == config.get("admin_password", "amakha2024"):
            session["admin_logged"] = True
            return redirect(url_for("admin_dashboard"))
        return render_template("admin_login.html", erro="Senha incorreta")
    return render_template("admin_login.html")

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged", None)
    return redirect(url_for("landing"))

@app.route("/admin")
def admin_dashboard():
    if not session.get("admin_logged"):
        return redirect(url_for("admin_login"))
    config = load_config()
    perfumes = load_perfumes()
    return render_template("admin_dashboard.html", config=config, perfumes=perfumes)

# ================= ADMIN API - KITS =================

@app.route("/api/admin/kits", methods=["GET"])
def api_admin_kits_get():
    if not session.get("admin_logged"):
        return {"erro": "Não autorizado"}, 401
    config = load_config()
    return jsonify(config["kits"])

@app.route("/api/admin/kits", methods=["POST"])
def api_admin_kits_post():
    if not session.get("admin_logged"):
        return {"erro": "Não autorizado"}, 401
    
    data = request.json
    quantidade = str(data.get("quantidade"))
    preco = float(data.get("preco", 0))
    
    config = load_config()
    config["kits"][quantidade] = {"preco": preco, "ativo": True}
    
    if quantidade not in config["kits_logistica"]:
        qtd = int(quantidade)
        config["kits_logistica"][quantidade] = {
            "weight": round(0.15 * qtd, 2),
            "width": min(16 + qtd, 40),
            "height": min(12 + (qtd // 5), 35),
            "length": min(18 + qtd, 40)
        }
    
    save_config(config)
    return {"sucesso": True}

@app.route("/api/admin/kits/<kit_id>", methods=["PUT"])
def api_admin_kits_put(kit_id):
    if not session.get("admin_logged"):
        return {"erro": "Não autorizado"}, 401
    
    data = request.json
    config = load_config()
    
    if kit_id in config["kits"]:
        if "preco" in data:
            config["kits"][kit_id]["preco"] = float(data["preco"])
        if "ativo" in data:
            config["kits"][kit_id]["ativo"] = data["ativo"]
        save_config(config)
        return {"sucesso": True}
    
    return {"erro": "Kit não encontrado"}, 404

@app.route("/api/admin/kits/<kit_id>", methods=["DELETE"])
def api_admin_kits_delete(kit_id):
    if not session.get("admin_logged"):
        return {"erro": "Não autorizado"}, 401
    
    config = load_config()
    if kit_id in config["kits"]:
        del config["kits"][kit_id]
        if kit_id in config["kits_logistica"]:
            del config["kits_logistica"][kit_id]
        save_config(config)
        return {"sucesso": True}
    
    return {"erro": "Kit não encontrado"}, 404

# ================= ADMIN API - PERFUMES =================

@app.route("/api/admin/perfumes", methods=["GET"])
def api_admin_perfumes_get():
    if not session.get("admin_logged"):
        return {"erro": "Não autorizado"}, 401
    return jsonify(load_perfumes())

@app.route("/api/admin/perfumes", methods=["POST"])
def api_admin_perfumes_post():
    if not session.get("admin_logged"):
        return {"erro": "Não autorizado"}, 401
    
    data = request.json
    perfumes = load_perfumes()
    
    novo_perfume = {
        "id": max([p.get("id", 0) for p in perfumes], default=0) + 1,
        "nome": data.get("nome"),
        "categoria": data.get("categoria"),
        "ml": data.get("ml", "15ml"),
        "ativo": True
    }
    
    perfumes.append(novo_perfume)
    save_perfumes(perfumes)
    return {"sucesso": True, "perfume": novo_perfume}

@app.route("/api/admin/perfumes/<int:perfume_id>", methods=["PUT"])
def api_admin_perfumes_put(perfume_id):
    if not session.get("admin_logged"):
        return {"erro": "Não autorizado"}, 401
    
    data = request.json
    perfumes = load_perfumes()
    
    for p in perfumes:
        if p.get("id") == perfume_id:
            if "nome" in data:
                p["nome"] = data["nome"]
            if "categoria" in data:
                p["categoria"] = data["categoria"]
            if "ml" in data:
                p["ml"] = data["ml"]
            if "ativo" in data:
                p["ativo"] = data["ativo"]
            save_perfumes(perfumes)
            return {"sucesso": True}
    
    return {"erro": "Perfume não encontrado"}, 404

@app.route("/api/admin/perfumes/<int:perfume_id>", methods=["DELETE"])
def api_admin_perfumes_delete(perfume_id):
    if not session.get("admin_logged"):
        return {"erro": "Não autorizado"}, 401
    
    perfumes = load_perfumes()
    perfumes = [p for p in perfumes if p.get("id") != perfume_id]
    save_perfumes(perfumes)
    return {"sucesso": True}

# ================= ADMIN API - CONFIG =================

@app.route("/api/admin/config", methods=["GET"])
def api_admin_config_get():
    if not session.get("admin_logged"):
        return {"erro": "Não autorizado"}, 401
    config = load_config()
    return jsonify({
        "whatsapp": config.get("whatsapp"),
        "cep_origem": config.get("cep_origem")
    })

@app.route("/api/admin/config", methods=["PUT"])
def api_admin_config_put():
    if not session.get("admin_logged"):
        return {"erro": "Não autorizado"}, 401
    
    data = request.json
    config = load_config()
    
    if "whatsapp" in data:
        config["whatsapp"] = data["whatsapp"]
    if "cep_origem" in data:
        config["cep_origem"] = data["cep_origem"]
    if "nova_senha" in data and data["nova_senha"]:
        config["admin_password"] = data["nova_senha"]
    
    save_config(config)
    return {"sucesso": True}

# ================= PONTOS DE COLETA =================

@app.route("/api/pontos-coleta", methods=["POST"])
def api_pontos_coleta():
    data = request.json
    cep = (data.get("cep") or "").replace("-", "").strip()
    
    try:
        resp = requests.get(f"https://viacep.com.br/ws/{cep}/json/")
        endereco = resp.json()
        
        if endereco.get("erro"):
            return {"erro": "CEP não encontrado"}, 404
        
        pontos = [
            {
                "nome": f"Ponto de Coleta {endereco.get('bairro', 'Centro')}",
                "endereco": f"{endereco.get('logradouro', 'Rua Principal')}, {endereco.get('bairro', 'Centro')}",
                "cidade": f"{endereco.get('localidade')}/{endereco.get('uf')}",
                "horario": "Seg-Sex: 8h-18h | Sáb: 8h-12h",
                "distancia": "0.5 km"
            },
            {
                "nome": f"Agência Correios {endereco.get('localidade')}",
                "endereco": f"Centro, {endereco.get('localidade')}",
                "cidade": f"{endereco.get('localidade')}/{endereco.get('uf')}",
                "horario": "Seg-Sex: 9h-17h",
                "distancia": "1.2 km"
            },
            {
                "nome": f"Jadlog {endereco.get('localidade')}",
                "endereco": f"Av. Principal, {endereco.get('localidade')}",
                "cidade": f"{endereco.get('localidade')}/{endereco.get('uf')}",
                "horario": "Seg-Sex: 8h-18h",
                "distancia": "2.0 km"
            }
        ]
        
        return jsonify({
            "endereco": endereco,
            "pontos": pontos
        })
        
    except Exception as e:
        print("Erro ao buscar CEP:", e)
        return {"erro": "Erro ao buscar CEP"}, 500

# ================= FRETE =================

def processar_resposta(resp, cotacoes, origem):
    dados = resp.json()
    print(f"\n=== RESPOSTA {origem} ===")
    print(dados)

    if isinstance(dados, dict):
        if dados.get("errors"):
            print("ERRO API:", dados["errors"])
            return
        if dados.get("message"):
            print("MENSAGEM API:", dados["message"])
            return
        return

    for op in dados:
        if op.get("error"):
            print("SERVIÇO RECUSADO:", op["name"], "-", op["error"])
            continue

        cotacoes.append({
            "transportadora": op["company"]["name"],
            "servico": op["name"],
            "valor": float(op["price"]),
            "prazo_min": op["delivery_range"]["min"],
            "prazo_max": op["delivery_range"]["max"]
        })

@app.route("/api/frete", methods=["POST"])
def calcular_frete():
    data = request.json
    config = load_config()

    cep_destino = (data.get("cep") or "").replace("-", "").strip()
    cep_destino = "".join(c for c in cep_destino if c.isdigit())

    if len(cep_destino) != 8:
        return {"erro": "CEP inválido"}, 400

    kit_escolhido = str(data.get("kit"))

    if kit_escolhido not in config["kits_logistica"]:
        return {"erro": "Kit não encontrado"}, 400

    kit_info = normalizar_dimensoes(config["kits_logistica"][kit_escolhido])
    kit_preco = config["kits"].get(kit_escolhido, {}).get("preco", 0)

    base_payload = {
        "from": {"postal_code": config.get("cep_origem", "13088221")},
        "to": {"postal_code": cep_destino},
        "packages": [{
            **kit_info,
            "insurance_value": kit_preco
        }],
        "options": {
            "receipt": False,
            "own_hand": False
        }
    }

    cotacoes = []

    try:
        payload = base_payload | {"services": SERVICOS_CORREIOS}
        resp = requests.post(API_URL, headers=ME_HEADERS, json=payload)
        processar_resposta(resp, cotacoes, "CORREIOS")

        payload = base_payload | {"services": SERVICOS_JADLOG}
        resp = requests.post(API_URL, headers=ME_HEADERS, json=payload)
        processar_resposta(resp, cotacoes, "JADLOG")

        cotacoes.sort(key=lambda x: (x["valor"], x["prazo_max"]))

        if not cotacoes:
            return {"erro": "Nenhum serviço disponível"}, 200

        return jsonify(cotacoes)

    except Exception as e:
        print("ERRO AO CONSULTAR FRETE:", e)
        return {"erro": "Falha ao consultar frete"}, 500

# ================= RUN =================

if __name__ == "__main__":
    app.run(debug=True)
