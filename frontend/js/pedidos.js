/**
 * PEREZBOOST PRO — PEDIDOS MODULE
 */

let pedidosCache = [];

async function renderPedidos() {
  const tbody = document.getElementById('pedidos-tbody');
  if (!tbody) return;

  tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding:30px; color:#94a3b8;">Cargando pedidos...</td></tr>';

  try {
    pedidosCache = await api.getPedidos();
    filtrarYMostrarPedidos();
  } catch (error) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding:30px; color:#f43f5e;">Error cargando pedidos: ${error.message}</td></tr>`;
  }
}

function filtrarYMostrarPedidos() {
  const tbody = document.getElementById('pedidos-tbody');
  const busqueda = (document.getElementById('pedidos-search')?.value || '').toLowerCase();
  const filtroEstado = document.getElementById('pedidos-filter-estado')?.value || 'Todos';

  let filtrados = pedidosCache.filter(p => {
    const matchTxt = (p.booster_nombre || '').toLowerCase().includes(busqueda) ||
                     (p.user_pass || '').toLowerCase().includes(busqueda) ||
                     (p.elo_inicial || '').toLowerCase().includes(busqueda) ||
                     (p.elo_final || '').toLowerCase().includes(busqueda);
    const matchEstado = filtroEstado === 'Todos' || p.estado === filtroEstado;
    return matchTxt && matchEstado;
  });

  if (filtrados.length === 0) {
    tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding:30px; color:#94a3b8;">No se encontraron pedidos con los filtros aplicados.</td></tr>';
    return;
  }

  tbody.innerHTML = filtrados.map(p => {
    const badgeClass = p.estado === 'Terminado' ? 'badge-terminado' : (p.estado === 'En progreso' ? 'badge-progreso' : 'badge-abandonado');
    const opggBtn = p.opgg ? `<a href="${p.opgg}" target="_blank" class="btn btn-secondary" style="padding:4px 8px; font-size:11px;">🔗 OP.GG</a>` : '<span style="color:#64748b;">-</span>';
    
    return `
      <tr>
        <td style="font-weight:700;">#${p.id}</td>
        <td>
          <div style="font-weight:600;">${p.booster_nombre || 'Sin asignar'}</div>
          <small style="color:#64748b; font-size:11px;">Inicio: ${p.fecha_inicio || '-'}</small>
        </td>
        <td>
          <code style="background:#1e293b; padding:2px 6px; border-radius:4px; font-size:11px; color:#38bdf8;">${p.user_pass || '-'}</code>
          <div style="font-size:11px; color:#94a3b8; margin-top:2px;">${p.elo_inicial || ''} ${p.elo_final ? `➔ <b style="color:#10b981;">${p.elo_final}</b>` : ''}</div>
        </td>
        <td><span class="badge ${badgeClass}">${p.estado}</span></td>
        <td>
          <div style="font-weight:600; color:#10b981;">$${(p.pago_cliente || 0).toFixed(2)}</div>
          <small style="color:#94a3b8; font-size:11px;">Staff: $${(p.pago_booster || 0).toFixed(2)}</small>
        </td>
        <td>${opggBtn}</td>
        <td>
          <button onclick="abrirModalEdicionPedido(${p.id})" class="btn btn-secondary" style="padding:6px 12px; font-size:12px;">
            ✏️ Modificar
          </button>
        </td>
      </tr>
    `;
  }).join('');
}

function abrirModalEdicionPedido(id) {
  const p = pedidosCache.find(item => item.id === id);
  if (!p) return;

  document.getElementById('edit-pedido-id').value = p.id;
  document.getElementById('edit-booster-nombre').value = p.booster_nombre || '';
  document.getElementById('edit-estado').value = p.estado || 'En progreso';
  document.getElementById('edit-elo-final').value = p.elo_final || '';
  document.getElementById('edit-wr').value = p.wr || 0;
  document.getElementById('edit-pago-cliente').value = p.pago_cliente || 0;
  document.getElementById('edit-pago-booster').value = p.pago_booster || 0;
  document.getElementById('edit-opgg').value = p.opgg || '';

  document.getElementById('modal-edit-pedido').classList.add('active');
}

async function guardarEdicionPedido(e) {
  e.preventDefault();
  const id = document.getElementById('edit-pedido-id').value;
  const payload = {
    estado: document.getElementById('edit-estado').value,
    booster_nombre: document.getElementById('edit-booster-nombre').value,
    elo_final: document.getElementById('edit-elo-final').value,
    wr: parseFloat(document.getElementById('edit-wr').value || 0),
    pago_cliente: parseFloat(document.getElementById('edit-pago-cliente').value || 0),
    pago_booster: parseFloat(document.getElementById('edit-pago-booster').value || 0)
  };

  const opggVal = document.getElementById('edit-opgg').value;

  try {
    await api.actualizarEstadoPedido(id, payload);
    if (opggVal !== undefined) {
      await api.actualizarOpgg(id, opggVal);
    }
    api.showToast(`Pedido #${id} actualizado exitosamente.`);
    document.getElementById('modal-edit-pedido').classList.remove('active');
    renderPedidos();
  } catch (error) {
    console.error(error);
  }
}
