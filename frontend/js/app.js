/**
 * PEREZBOOST PRO — MAIN SPA CONTROLLER & ROUTER
 */

document.addEventListener('DOMContentLoaded', () => {
  initAuthUI();
  setupNavigation();
  setupEventListeners();

  // Comprobar sesión activa
  if (api.token) {
    onLoginSuccess();
  } else {
    showLoginModal();
  }
});

function initAuthUI() {
  const loginForm = document.getElementById('form-login');
  if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const u = document.getElementById('login-username').value.trim();
      const p = document.getElementById('login-password').value.trim();
      const btn = loginForm.querySelector('button[type="submit"]');

      try {
        btn.textContent = 'Iniciando sesión...';
        btn.disabled = true;
        await api.login(u, p);
        api.showToast(`¡Bienvenido de nuevo, ${api.user.name}!`);
        document.getElementById('modal-login').classList.remove('active');
        onLoginSuccess();
      } catch (error) {
        console.error(error);
      } finally {
        btn.textContent = 'Ingresar al Sistema';
        btn.disabled = false;
      }
    });
  }

  const btnLogout = document.getElementById('btn-logout');
  if (btnLogout) {
    btnLogout.addEventListener('click', () => {
      api.logout();
      window.location.reload();
    });
  }
}

function showLoginModal() {
  document.getElementById('modal-login').classList.add('active');
}

function onLoginSuccess() {
  const user = api.user;
  document.getElementById('user-name-display').textContent = user.name;
  document.getElementById('user-role-display').textContent = user.role === 'admin' ? 'Administrador' : 'Booster';
  document.getElementById('user-avatar-text').textContent = (user.name || 'U')[0].toUpperCase();

  // Control de vistas por rol
  const adminNavItems = document.querySelectorAll('.admin-only');
  const boosterNavItems = document.querySelectorAll('.booster-only');

  if (user.role === 'admin') {
    adminNavItems.forEach(el => el.style.display = 'flex');
    boosterNavItems.forEach(el => el.style.display = 'none');
    navigateTo('dashboard');
  } else {
    adminNavItems.forEach(el => el.style.display = 'none');
    boosterNavItems.forEach(el => el.style.display = 'flex');
    navigateTo('booster-portal');
  }
}

function setupNavigation() {
  document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', (e) => {
      e.preventDefault();
      const target = item.getAttribute('data-target');
      if (target) navigateTo(target);
    });
  });
}

function navigateTo(viewId) {
  // Update nav active class
  document.querySelectorAll('.nav-item').forEach(item => {
    if (item.getAttribute('data-target') === viewId) {
      item.classList.add('active');
    } else {
      item.classList.remove('active');
    }
  });

  // Switch view containers
  document.querySelectorAll('.view-section').forEach(view => {
    if (view.id === `view-${viewId}`) {
      view.style.display = 'block';
    } else {
      view.style.display = 'none';
    }
  });

  // Load view data
  switch (viewId) {
    case 'dashboard':
      renderDashboard();
      break;
    case 'pedidos':
      renderPedidos();
      break;
    case 'inventario':
      renderInventario();
      break;
    case 'ranking':
      renderRanking();
      break;
    case 'finanzas':
      renderFinanzas();
      break;
    case 'booster-portal':
      renderBoosterPortal();
      break;
  }
}

function setupEventListeners() {
  // Edit pedido form
  const formEditPedido = document.getElementById('form-edit-pedido');
  if (formEditPedido) formEditPedido.addEventListener('submit', guardarEdicionPedido);

  // Add cuenta form
  const formAddCuenta = document.getElementById('form-add-cuenta');
  if (formAddCuenta) formAddCuenta.addEventListener('submit', agregarCuentaSubmit);

  // Add lote form
  const formAddLote = document.getElementById('form-add-lote');
  if (formAddLote) formAddLote.addEventListener('submit', agregarLoteSubmit);

  // Add tx wallet form
  const formAddTx = document.getElementById('form-add-tx');
  if (formAddTx) formAddTx.addEventListener('submit', agregarTransaccionWallet);

  // Search & Filter Pedidos
  const searchInput = document.getElementById('pedidos-search');
  if (searchInput) searchInput.addEventListener('input', filtrarYMostrarPedidos);

  const filterEstado = document.getElementById('pedidos-filter-estado');
  if (filterEstado) filterEstado.addEventListener('change', filtrarYMostrarPedidos);

  // Close modals
  document.querySelectorAll('.modal-close').forEach(btn => {
    btn.addEventListener('click', () => {
      btn.closest('.modal-backdrop').classList.remove('active');
    });
  });
}
