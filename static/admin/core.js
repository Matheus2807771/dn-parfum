/* ================= CORE ADMIN ================= */

window.showTab = function (tab, btn) {
  // Esconde todos os conteúdos
  document.querySelectorAll('.tab-content').forEach(el => {
    el.classList.remove('active');
  });

  // Remove active dos botões
  document.querySelectorAll('.tab-btn').forEach(el => {
    el.classList.remove('active');
  });

  // Mostra a aba selecionada
  const content = document.getElementById('tab-' + tab);
  if (content) {
    content.classList.add('active');
  } else {
    console.warn('Tab não encontrada:', tab);
  }

  // Ativa o botão clicado
  if (btn) btn.classList.add('active');

  // Carregadores por aba
  if (tab === 'relatorios' && window.carregarRelatorios) {
    window.carregarRelatorios();
  }

  if (tab === 'kits' && window.carregarKits) {
    window.carregarKits();
  }

  if (tab === 'perfumes' && window.carregarPerfumes) {
    window.carregarPerfumes();
  }

  // Configurações NÃO precisa carregar nada automaticamente
  // pois só salva quando clicar no botão
};

/* ================= INIT ================= */

document.addEventListener('DOMContentLoaded', () => {
  if (window.carregarRelatorios) {
    window.carregarRelatorios();
  }
});
