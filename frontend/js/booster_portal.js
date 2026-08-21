/**
 * PEREZBOOST PRO — BOOSTER PORTAL (MOBILE FIRST PWA)
 */

async function renderBoosterPortal() {
  const container = document.getElementById('booster-pedidos-list');
  const saldoTxt = document.getElementById('booster-saldo-pendiente');
  const userGreeting = document.getElementById('booster-greeting-name');

  if (!container) return;

  if (userGreeting) userGreeting.textContent = api.user?.name || 'Booster';

  try {
    const [saldoData, misPedidos] = await Promise.all([
      api.getMiSaldo(),
      api.getMisPedidos()
    ]);

    if (saldoTxt) saldoTxt.textContent = `$${saldoData.saldo_pendiente.toFixed(2)}`;

    if (misPedidos.length === 0) {
      container.innerHTML = '<div class="card" style="text-align:center; color:#94a3b8; padding:30px;">No tienes cuentas asignadas actualmente.</div>';
      return;
    }

    container.innerHTML = misPedidos.map(p => {
      const isActivo = p.estado === 'En progreso';
      return `
        <div class="card" style="margin-bottom:16px; border-left:4px solid ${isActivo ? '#06b6d4' : '#10b981'};">
          <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:12px;">
            <div>
              <span class="badge ${isActivo ? 'badge-progreso' : 'badge-terminado'}">${p.estado}</span>
              <h3 style="margin-top:6px; font-size:16px;">Pedido #${p.id} — <b style="color:#10b981;">${p.elo_inicial}</b></h3>
            </div>
            <div style="text-align:right;">
              <small style="color:#64748b; font-size:11px;">Pago Staff</small>
              <div style="font-size:16px; font-weight:800; color:#10b981;">$${(p.pago_booster || 0).toFixed(2)}</div>
            </div>
          </div>

          <div style="background:#0f172a; padding:12px; border-radius:8px; margin-bottom:14px;">
            <div style="font-size:11px; color:#94a3b8; margin-bottom:4px;">CREDENCIALES DE LA CUENTA:</div>
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <code style="font-size:13px; color:#38bdf8; font-weight:700;">${p.user_pass}</code>
              <button onclick="copiarAlPortapapeles('${p.user_pass}')" class="btn btn-secondary" style="padding:4px 10px; font-size:11px;">
                📋 Copiar
              </button>
            </div>
          </div>

          <div style="display:flex; gap:10px; align-items:center;">
            <input type="url" id="opgg-input-${p.id}" value="${p.opgg || ''}" placeholder="Pega tu enlace OP.GG aquí..." class="input-field" style="flex:1; font-size:12px;" />
            <button onclick="guardarOpggBooster(${p.id})" class="btn btn-primary" style="padding:8px 14px; font-size:12px;">
              💾 Guardar OP.GG
            </button>
          </div>
        </div>
      `;
    }).join('');
  } catch (error) {
    console.error('Error en portal de booster:', error);
  }
}

async function guardarOpggBooster(id) {
  const input = document.getElementById(`opgg-input-${id}`);
  const opgg = input ? input.value.trim() : '';

  try {
    await api.actualizarOpgg(id, opgg);
    api.showToast(`Enlace OP.GG guardado para el pedido #${id}.`);
  } catch (error) {
    console.error(error);
  }
}
