/**
 * PEREZBOOST PRO — API CLIENT & AUTH ADAPTER
 */

const API_BASE = window.location.origin.includes('localhost') || window.location.origin.includes('127.0.0.1')
  ? `${window.location.origin}/api/v1`
  : '/api/v1';

class ApiService {
  constructor() {
    this.token = localStorage.getItem('perezboost_token') || null;
    this.user = JSON.parse(localStorage.getItem('perezboost_user') || 'null');
  }

  getHeaders() {
    const headers = { 'Content-Type': 'application/json' };
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }
    return headers;
  }

  async request(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    options.headers = { ...this.getHeaders(), ...(options.headers || {}) };

    try {
      const response = await fetch(url, options);
      
      if (response.status === 401) {
        this.logout();
        window.location.reload();
        throw new Error('Sesión expirada. Inicia sesión nuevamente.');
      }

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || `Error HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      this.showToast(error.message, 'error');
      throw error;
    }
  }

  async login(username, password) {
    const data = await this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password })
    });
    this.token = data.access_token;
    this.user = { name: data.name, role: data.role };
    localStorage.setItem('perezboost_token', this.token);
    localStorage.setItem('perezboost_user', JSON.stringify(this.user));
    return data;
  }

  logout() {
    this.token = null;
    this.user = null;
    localStorage.removeItem('perezboost_token');
    localStorage.removeItem('perezboost_user');
  }

  showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<span>${type === 'success' ? '✅' : '⚠️'}</span><span>${message}</span>`;
    container.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      setTimeout(() => toast.remove(), 300);
    }, 3500);
  }

  // Endpoints
  getMe() { return this.request('/auth/me'); }
  getPedidos(params = {}) {
    const query = new URLSearchParams(params).toString();
    return this.request(`/pedidos${query ? `?${query}` : ''}`);
  }
  getPedidosActivos() { return this.request('/pedidos/activos'); }
  crearPedido(data) { return this.request('/pedidos', { method: 'POST', body: JSON.stringify(data) }); }
  finalizarPedido(id, data) { return this.request(`/pedidos/${id}/finalizar`, { method: 'POST', body: JSON.stringify(data) }); }
  actualizarEstadoPedido(id, data) { return this.request(`/pedidos/${id}/estado`, { method: 'PATCH', body: JSON.stringify(data) }); }
  actualizarOpgg(id, opgg) { return this.request(`/pedidos/${id}/opgg`, { method: 'PATCH', body: JSON.stringify({ opgg }) }); }

  getInventario(elo = '') { return this.request(`/inventario${elo ? `?elo=${elo}` : ''}`); }
  getElosStock() { return this.request('/inventario/elos'); }
  agregarCuenta(data) { return this.request('/inventario', { method: 'POST', body: JSON.stringify(data) }); }
  agregarLoteCuentas(data) { return this.request('/inventario/lote', { method: 'POST', body: JSON.stringify(data) }); }
  eliminarCuenta(id) { return this.request(`/inventario/${id}`, { method: 'DELETE' }); }

  getBoosters() { return this.request('/boosters'); }
  crearBooster(data) { return this.request('/boosters', { method: 'POST', body: JSON.stringify(data) }); }
  toggleRankingBooster(id) { return this.request(`/boosters/${id}/toggle-ranking`, { method: 'PATCH' }); }
  eliminarBooster(id) { return this.request(`/boosters/${id}`, { method: 'DELETE' }); }

  // Booster Self-Service
  getMisPedidos() { return this.request('/boosters/me/pedidos'); }
  getMiSaldo() { return this.request('/boosters/me/saldo'); }
  actualizarMiPerfil(data) { return this.request('/boosters/me/perfil', { method: 'PATCH', body: JSON.stringify(data) }); }

  getRanking(mes = '') { return this.request(`/ranking${mes ? `?mes=${mes}` : ''}`); }
  getFinanzasResumen(mes = '') { return this.request(`/finanzas/resumen${mes ? `?mes=${mes}` : ''}`); }
  getSaldosPendientes() { return this.request('/finanzas/saldos-pendientes'); }
  liquidarBooster(nombre) { return this.request(`/finanzas/liquidar/${encodeURIComponent(nombre)}`, { method: 'POST' }); }

  getTarifas() { return this.request('/tarifas'); }
  crearTarifa(data) { return this.request('/tarifas', { method: 'POST', body: JSON.stringify(data) }); }
  eliminarTarifa(div) { return this.request(`/tarifas/${encodeURIComponent(div)}`, { method: 'DELETE' }); }

  getWalletBalance() { return this.request('/wallet/balance'); }
  getWalletTransacciones() { return this.request('/wallet/transacciones'); }
  crearTransaccionWallet(data) { return this.request('/wallet/transacciones', { method: 'POST', body: JSON.stringify(data) }); }
}

const api = new ApiService();
