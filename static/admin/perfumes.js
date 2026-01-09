/* ================= PERFUMES ================= */

/* LISTAR PERFUMES */
window.carregarPerfumes = async function () {
  const tbody = document.getElementById('perfumes-tbody');
  if (!tbody) return;

  tbody.innerHTML = '<tr><td colspan="5">Carregando...</td></tr>';

  try {
    const r = await fetch('/api/admin/perfumes');
    if (!r.ok) throw new Error('Erro ao buscar perfumes');

    const d = await r.json();

    if (!Array.isArray(d) || !d.length) {
      tbody.innerHTML =
        '<tr><td colspan="5">Nenhum perfume cadastrado</td></tr>';
      return;
    }

    tbody.innerHTML = d.map(p => `
      <tr>
        <td>${p.nome ?? '-'}</td>
        <td>${p.categoria ?? '-'}</td>
        <td>${p.ml ?? '-'}</td>
        <td>
          <span class="badge ${p.ativo ? 'badge-on' : 'badge-off'}">
            ${p.ativo ? 'Ativo' : 'Inativo'}
          </span>
        </td>
        <td>
          <button class="btn btn-warning btn-sm"
            onclick="togglePerfume(${p.id}, ${p.ativo ? 'true' : 'false'})">
            ${p.ativo ? 'Desativar' : 'Ativar'}
          </button>
        </td>
      </tr>
    `).join('');

  } catch (e) {
    console.error('Erro carregar perfumes:', e);
    tbody.innerHTML =
      '<tr><td colspan="5">Erro ao carregar perfumes</td></tr>';
  }
};


/* CRIAR PERFUME */
window.criarPerfume = async function () {
  const nome = document.getElementById('p-nome')?.value?.trim();
  const categoria = document.getElementById('p-cat')?.value;
  const ml = document.getElementById('p-ml')?.value;

  if (!nome) {
    alert('Informe o nome do perfume.');
    return;
  }

  try {
    const r = await fetch('/api/admin/perfumes', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ nome, categoria, ml })
    });

    if (!r.ok) throw new Error('Erro ao criar perfume');

    document.getElementById('p-nome').value = '';
    await window.carregarPerfumes();

  } catch (e) {
    console.error('Erro criar perfume:', e);
    alert('Erro ao criar perfume');
  }
};


/* ATIVAR / DESATIVAR PERFUME (TOGGLE) */
window.togglePerfume = async function (id, ativoAtual) {
  try {
    const r = await fetch(`/api/admin/perfumes/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ativo: !ativoAtual })
    });

    if (!r.ok) throw new Error('Erro ao atualizar perfume');

    await window.carregarPerfumes();

  } catch (e) {
    console.error('Erro toggle perfume:', e);
    alert('Erro ao alterar status do perfume');
  }
};
