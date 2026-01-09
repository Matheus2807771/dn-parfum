function setKitsStatus(msg) {
  const el = document.getElementById('kits-status');
  if (el) el.textContent = msg || '';
}

function onlyNumber(v) {
  return String(v || '').replace(/[^\d]/g, '');
}

window.carregarKits = async function () {
  try {
    setKitsStatus('Carregando...');
    const r = await fetch('/api/admin/kits');
    const d = await r.json();

    const tbody = document.getElementById('kits-tbody');
    if (!tbody) return;

    const entries = Object.entries(d || {}).sort((a,b)=>Number(a[0])-Number(b[0]));

    tbody.innerHTML = entries.length ? entries.map(([qtd, obj]) => {
      const ativo = !!obj.ativo;
      return `
        <tr>
          <td><b>${qtd}</b></td>
          <td>
            <input class="inline-input" id="kit-preco-${qtd}" value="${obj.preco}" />
          </td>
          <td>
            <span class="badge ${ativo ? 'badge-on' : 'badge-off'}">${ativo ? 'Ativo' : 'Inativo'}</span>
          </td>
          <td style="display:flex;gap:8px;flex-wrap:wrap;">
            <button class="btn btn-primary btn-sm" onclick="atualizarKit('${qtd}')">Salvar</button>
            <button class="btn btn-warning btn-sm" onclick="toggleKit('${qtd}', ${ativo ? 'true' : 'false'})">
              ${ativo ? 'Desativar' : 'Ativar'}
            </button>
            <button class="btn btn-danger btn-sm" onclick="excluirKit('${qtd}')">Excluir</button>
          </td>
        </tr>
      `;
    }).join('') : `<tr><td colspan="4">Nenhum kit cadastrado</td></tr>`;

    setKitsStatus('OK');
  } catch (e) {
    console.error(e);
    setKitsStatus('Erro');
  }
};

window.criarKit = async function () {
  const qtd = onlyNumber(document.getElementById('kit-qtd')?.value);
  const precoRaw = document.getElementById('kit-preco')?.value || '';
  const preco = Number(String(precoRaw).replace(',','.'));

  if (!qtd || !Number.isFinite(preco)) {
    alert('Informe quantidade e preço válidos.');
    return;
  }

  setKitsStatus('Salvando...');
  const r = await fetch('/api/admin/kits', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({ quantidade: qtd, preco })
  });

  if (!r.ok) {
    alert('Erro ao criar kit.');
    setKitsStatus('Erro');
    return;
  }

  document.getElementById('kit-qtd').value = '';
  document.getElementById('kit-preco').value = '';
  await window.carregarKits();
};

window.atualizarKit = async function (qtd) {
  const precoRaw = document.getElementById(`kit-preco-${qtd}`)?.value || '';
  const preco = Number(String(precoRaw).replace(',','.'));

  if (!Number.isFinite(preco)) {
    alert('Preço inválido.');
    return;
  }

  setKitsStatus('Atualizando...');
  const r = await fetch(`/api/admin/kits/${qtd}`, {
    method: 'PUT',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({ preco })
  });

  if (!r.ok) {
    alert('Erro ao atualizar kit.');
    setKitsStatus('Erro');
    return;
  }

  await window.carregarKits();
};

window.toggleKit = async function (qtd, ativoAtual) {
  setKitsStatus('Atualizando status...');
  const r = await fetch(`/api/admin/kits/${qtd}`, {
    method: 'PUT',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({ ativo: !ativoAtual })
  });

  if (!r.ok) {
    alert('Erro ao alterar status.');
    setKitsStatus('Erro');
    return;
  }

  await window.carregarKits();
};

window.excluirKit = async function (qtd) {
  if (!confirm(`Excluir Kit ${qtd}?`)) return;

  setKitsStatus('Excluindo...');
  const r = await fetch(`/api/admin/kits/${qtd}`, { method: 'DELETE' });

  if (!r.ok) {
    alert('Erro ao excluir kit.');
    setKitsStatus('Erro');
    return;
  }

  await window.carregarKits();
};
