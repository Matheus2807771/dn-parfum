function setCfgStatus(msg) {
  const el = document.getElementById('cfg-status');
  if (el) el.textContent = msg || '';
}

function onlyDigits(v) {
  return String(v || '').replace(/[^\d]/g, '');
}

window.carregarConfig = function () {
  // seu backend renderiza config no template, mas você não está usando jinja aqui.
  // então deixo neutro (sem quebrar). Se quiser, a gente cria GET /api/admin/config.
  setCfgStatus('Preencha e clique em Salvar.');
};

window.salvarConfig = async function () {
  const whatsapp = onlyDigits(document.getElementById('cfg-whats')?.value);
  const cep_origem = onlyDigits(document.getElementById('cfg-cep')?.value);
  const nova_senha = document.getElementById('cfg-senha')?.value || '';

  setCfgStatus('Salvando...');
  const r = await fetch('/api/admin/config', {
    method: 'PUT',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({ whatsapp, cep_origem, nova_senha })
  });

  if (!r.ok) {
    setCfgStatus('Erro ao salvar.');
    alert('Erro ao salvar configurações.');
    return;
  }

  document.getElementById('cfg-senha').value = '';
  setCfgStatus('Configurações salvas com sucesso.');
};
