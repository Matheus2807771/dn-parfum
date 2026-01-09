window.alterarStatusPedido = async function (id, status) {
  const r = await fetch(`/api/admin/pedidos/${id}/status`, {
    method: 'PUT',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({ status })
  });

  if (!r.ok) {
    alert('Erro ao atualizar status');
    return;
  }

  // Atualiza só os badges sem recarregar tudo
  carregarPedidos();
};
