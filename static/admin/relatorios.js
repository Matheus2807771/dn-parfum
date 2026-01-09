/* ================= RELATÓRIOS (COMPLETO) ================= */

let chartVendas = null;

function setRelStatus(msg) {
  const el = document.getElementById('rel-status');
  if (el) el.textContent = msg || '';
}

function brMoney(v) {
  const n = Number(v || 0);
  return 'R$ ' + n.toFixed(2).replace('.', ',');
}

function safeSetText(id, value) {
  const el = document.getElementById(id);
  if (el) el.innerText = value;
}

function formatDate(dt) {
  // dt pode vir como "2026-01-08T15:31:00..." (UTC do supabase)
  if (!dt) return '-';
  try {
    // exibe "YYYY-MM-DD HH:mm"
    return String(dt).replace('T', ' ').slice(0, 16);
  } catch {
    return '-';
  }
}

/* ================= PERFUMES MAIS VENDIDOS ================= */
window.carregarPerfumesMaisVendidos = async function () {
  const container = document.getElementById('ranking-perfumes');
  if (!container) return;

  const r = await fetch('/api/admin/relatorios/perfumes-mais-vendidos');
  const d = await r.json();

  container.innerHTML = d.length
    ? d.slice(0, 10).map((p, i) => `
      <div class="ranking-card">
        <div class="ranking-pos">#${i + 1}</div>
        <div class="ranking-nome">${p.perfume}</div>
        <div class="ranking-qtd">${p.quantidade} unidades vendidas</div>
      </div>
    `).join('')
    : `<div style="color:#9aa3c7">Nenhum dado disponível</div>`;
};


/* ================= KITS MAIS VENDIDOS (ROBUSTO) ================= */
window.carregarKitsMaisVendidos = async function () {
  const container = document.getElementById('ranking-kits');
  if (!container) return;

  try {
    const r = await fetch('/api/admin/relatorios/kits-mais-vendidos');
    const d = await r.json();

    if (!Array.isArray(d) || !d.length) {
      container.innerHTML =
        `<div style="color:#9aa3c7">Nenhum kit vendido</div>`;
      return;
    }

    container.innerHTML = d.map((k, i) => `
      <div class="ranking-card">
        <div class="ranking-pos">#${i + 1}</div>
        <div class="ranking-nome">
          Kit ${k.kit_quantidade} perfumes
        </div>
        <div class="ranking-qtd">
          ${k.quantidade_vendida} vendidos
        </div>
      </div>
    `).join('');

  } catch (e) {
    console.error('Erro kits mais vendidos:', e);
    container.innerHTML =
      `<div style="color:#ff4444">Erro ao carregar kits</div>`;
  }
};


/* ================= STATUS PEDIDO ================= */
window.atualizarStatusPedido = async function (pedidoId, novoStatus) {
  try {
    const r = await fetch(`/api/admin/pedidos/${pedidoId}/status`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: novoStatus })
    });

    if (!r.ok) {
      const t = await r.text().catch(() => '');
      alert('Erro ao atualizar status.\n' + t);
      return;
    }

    // recarrega a lista para refletir o status atualizado
    await window.carregarPedidos();
  } catch (e) {
    console.error('Erro atualizar status:', e);
    alert('Erro ao atualizar status.');
  }
};

/* ================= RELATÓRIOS (RESUMO + KPIs) ================= */
window.carregarRelatorios = async function () {
  try {
    setRelStatus('Atualizando...');

    const r = await fetch('/api/admin/relatorios/resumo');
    const d = await r.json();

    // IDs atuais que você já usa
    safeSetText('stat-valor-total', brMoney(d.valor_total || 0));
    safeSetText('stat-total-pedidos', String(d.total_pedidos || 0));

    // KPIs adicionais (se você criar esses IDs no HTML, já aparece)
    // Sugestão de IDs: stat-valor-hoje, stat-valor-mes, stat-pedidos-hoje, stat-pedidos-mes
    safeSetText('stat-valor-hoje', brMoney(d.valor_hoje || 0));
    safeSetText('stat-valor-mes', brMoney(d.valor_mes || 0));
    safeSetText('stat-pedidos-hoje', String(d.pedidos_hoje || 0));
    safeSetText('stat-pedidos-mes', String(d.pedidos_mes || 0));

    await window.carregarPedidos();
    await window.carregarGrafico();
    await window.carregarPerfumesMaisVendidos();
    await window.carregarKitsMaisVendidos();

    setRelStatus('OK');
  } catch (e) {
    console.error('Erro relatórios:', e);
    setRelStatus('Erro ao carregar');
  }
};

/* ================= PEDIDOS (COM ALTERAÇÃO DE STATUS) ================= */
window.carregarPedidos = async function () {
  const tbody = document.getElementById('lista-pedidos');
  if (!tbody) return;

  tbody.innerHTML = `<tr><td colspan="8">Carregando...</td></tr>`;

  try {
    const r = await fetch('/api/admin/relatorios/pedidos-recentes');
    const d = await r.json();

    if (!d || !d.length) {
      tbody.innerHTML = `<tr><td colspan="8">Nenhum pedido</td></tr>`;
      return;
    }

    tbody.innerHTML = d.map(p => {
      const status = (p.status || 'pendente').toLowerCase();
      const id = p.id;

      return `
        <tr>
          <td>#${id}</td>
          <td>${formatDate(p.created_at)}</td>
          <td>${p.kit_quantidade ?? '-'}</td>
          <td>${p.cliente_nome || '-'}</td>
          <td>${p.cliente_telefone || '-'}</td>
          <td>${p.cliente_cidade || '-'}</td>
          <td>${brMoney(p.valor_total || 0)}</td>
          <td>
            <select class="inline-input"
                    onchange="atualizarStatusPedido(${id}, this.value)">
              <option value="pendente" ${status === 'pendente' ? 'selected' : ''}>pendente</option>
              <option value="confirmado" ${status === 'confirmado' ? 'selected' : ''}>confirmado</option>
              <option value="cancelado" ${status === 'cancelado' ? 'selected' : ''}>cancelado</option>
            </select>
          </td>
        </tr>
      `;
    }).join('');
  } catch (e) {
    console.error('Erro pedidos recentes:', e);
    tbody.innerHTML = `<tr><td colspan="8">Erro ao carregar pedidos</td></tr>`;
  }
};

/* ================= GRÁFICO ================= */
window.carregarGrafico = async function () {
  const canvas = document.getElementById('chartVendas');
  if (!canvas) return;

  try {
    const r = await fetch('/api/admin/relatorios/vendas-por-periodo');
    const d = await r.json();

    if (!d || !d.length) {
      // sem dados -> destrói gráfico anterior e não quebra
      if (chartVendas) {
        chartVendas.destroy();
        chartVendas = null;
      }
      return;
    }

    if (chartVendas) chartVendas.destroy();

    chartVendas = new Chart(canvas, {
      type: 'line',
      data: {
        labels: d.map(x => x.data),
        datasets: [{
          label: 'Vendas',
          data: d.map(x => Number(x.valor || 0)),
          borderColor: '#23c483',
          tension: 0.3
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false
      }
    });
  } catch (e) {
    console.error('Erro gráfico:', e);
  }
};
