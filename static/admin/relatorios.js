/* ================= RELATÓRIOS (FINAL 100%) ================= */

let chartVendas = null;
window.__pedidosMap = {};
window.__pedidoEntregaAtualId = null;

/* ================= HELPERS ================= */

function brMoney(v) {
  return 'R$ ' + Number(v || 0).toFixed(2).replace('.', ',');
}

function safeSetText(id, v) {
  const el = document.getElementById(id);
  if (el) el.innerText = v;
}

function formatDate(dt) {
  return dt ? String(dt).replace('T', ' ').slice(0, 16) : '-';
}

function enderecoLinha(p) {
  const linhas = [];

  const l1 = [p.cliente_rua, p.cliente_numero].filter(Boolean).join(', ');
  const l2 = [p.cliente_bairro, `${p.cliente_cidade || ''}/${p.cliente_uf || ''}`.replace('/','')].filter(Boolean).join(' — ');

  if (l1) linhas.push(l1);
  if (l2) linhas.push(l2);
  if (p.cliente_cep) linhas.push(`CEP: ${p.cliente_cep}`);
  if (p.cliente_complemento) linhas.push(`Compl.: ${p.cliente_complemento}`);

  return linhas.length ? linhas.join('<br>') : '-';
}

/* ================= RANKINGS ================= */

window.carregarPerfumesMaisVendidos = async function () {
  const container = document.getElementById('ranking-perfumes');
  if (!container) return;

  try {
    const r = await fetch('/api/admin/relatorios/perfumes-mais-vendidos');
    const d = await r.json();

    if (!Array.isArray(d) || !d.length) {
      container.innerHTML = '<div class="small-muted">Nenhum dado disponível</div>';
      return;
    }

    container.innerHTML = d.map((p, i) => `
      <div class="ranking-card">
        <div class="ranking-pos">#${i + 1}</div>
        <div class="ranking-nome">${p.perfume}</div>
        <div class="ranking-qtd">${p.quantidade} vendidos</div>
      </div>
    `).join('');
  } catch (e) {
    console.error(e);
    container.innerHTML = '<div class="small-muted">Erro ao carregar</div>';
  }
};

window.carregarKitsMaisVendidos = async function () {
  const container = document.getElementById('ranking-kits');
  if (!container) return;

  try {
    const r = await fetch('/api/admin/relatorios/kits-mais-vendidos');
    const d = await r.json();

    if (!Array.isArray(d) || !d.length) {
      container.innerHTML = '<div class="small-muted">Nenhum dado disponível</div>';
      return;
    }

    container.innerHTML = d.map((k, i) => `
      <div class="ranking-card">
        <div class="ranking-pos">#${i + 1}</div>
        <div class="ranking-nome">Kit ${k.kit_quantidade}</div>
        <div class="ranking-qtd">${k.quantidade_vendida} vendidos</div>
      </div>
    `).join('');
  } catch (e) {
    console.error(e);
    container.innerHTML = '<div class="small-muted">Erro ao carregar</div>';
  }
};

/* ================= RELATÓRIOS ================= */

window.carregarRelatorios = async function () {
  const r = await fetch('/api/admin/relatorios/resumo');
  const d = await r.json();

  safeSetText('stat-valor-total', brMoney(d.valor_total));
  safeSetText('stat-total-pedidos', d.total_pedidos);
  safeSetText('stat-valor-hoje', brMoney(d.valor_hoje));
  safeSetText('stat-valor-mes', brMoney(d.valor_mes));
  safeSetText('stat-pedidos-hoje', d.pedidos_hoje);
  safeSetText('stat-pedidos-mes', d.pedidos_mes);

  await carregarPedidos();
  await carregarGrafico();
};

/* ================= PEDIDOS ================= */

window.carregarPedidos = async function () {
  const tbody = document.getElementById('lista-pedidos');
  tbody.innerHTML = `<tr><td colspan="9">Carregando...</td></tr>`;

  const r = await fetch('/api/admin/relatorios/pedidos-recentes');
  const d = await r.json();

  window.__pedidosMap = {};
  d.forEach(p => window.__pedidosMap[p.id] = p);

  if (!d.length) {
    tbody.innerHTML = `<tr><td colspan="9">Nenhum pedido</td></tr>`;
    return;
  }

  tbody.innerHTML = d.map(p => `
    <tr>
      <td>#${p.id}</td>
      <td>${formatDate(p.created_at)}</td>
      <td>${p.kit_quantidade}</td>
      <td>${p.cliente_nome || '-'}</td>
      <td>${p.cliente_telefone || '-'}</td>
      <td>${enderecoLinha(p)}</td>
      <td>${brMoney(p.valor_total)}</td>
      <td>
        <select class="inline-input" onchange="atualizarStatusPedido(${p.id}, this.value)">
          <option value="pendente" ${p.status==='pendente'?'selected':''}>pendente</option>
          <option value="confirmado" ${p.status==='confirmado'?'selected':''}>confirmado</option>
          <option value="cancelado" ${p.status==='cancelado'?'selected':''}>cancelado</option>
        </select>
      </td>
      <td style="display:flex;gap:6px">
        <button class="btn btn-primary btn-sm" onclick="abrirModalEntrega(${p.id})">Entrega</button>
        <button class="btn btn-secondary btn-sm" onclick="enviarWhatsEntrega(${p.id})">WhatsApp</button>
      </td>
    </tr>
  `).join('');
};

/* ================= GRÁFICO ================= */

window.carregarGrafico = async function () {
  const canvas = document.getElementById('chartVendas');
  if (!canvas) return;

  const r = await fetch('/api/admin/relatorios/vendas-por-periodo');
  const d = await r.json();
  if (!d.length) return;

  if (chartVendas) chartVendas.destroy();

  chartVendas = new Chart(canvas, {
    type: 'line',
    data: {
      labels: d.map(x => x.data),
      datasets: [{
        label: 'Vendas',
        data: d.map(x => Number(x.valor)),
        borderColor: '#23c483',
        tension: 0.3
      }]
    },
    options: { responsive: true, maintainAspectRatio: false }
  });
};

/* ================= INIT ================= */

document.addEventListener('DOMContentLoaded', async () => {
  await window.carregarRelatorios();
  await window.carregarPerfumesMaisVendidos();
  await window.carregarKitsMaisVendidos();
});
