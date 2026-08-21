/**
 * PEREZBOOST PRO — INVENTARIO MODULE
 */

let inventarioCache = [];

async function renderInventario() {
  const container = document.getElementById('inventario-grid');
  if (!container) return;

  container.innerHTML = '<div style="color:#94a3b8; text-align:center; grid-column:1/-1;">Cargando stock de cuentas...</div>';

  try {
    inventarioCache = await api.getInventario();
    
    if (inventarioCache.length === 0) {
      container.innerHTML = '<div style="color:#94a3b8; text-align:center; grid-column:1/-1; padding:40px;">No hay cuentas disponibles en stock.</div>';
      return;
    }

    container.innerHTML = inventarioCache.map(c => `
      <div class="card" style="padding:18px; display:flex; flex-direction:column; justify-content:space-between; border-color:rgba(56, 189, 248, 0.2);">
        <div>
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
            <span class="badge" style="background:rgba(56, 189, 248, 0.15); color:#38bdf8; border:1px solid rgba(56, 189, 248, 0.3);">
              ${c.elo_tipo || 'FRESH'}
            </span>
            <small style="color:#64748b;">ID #${c.id}</small>
          </div>
          <div style="font-family:monospace; background:#0f172a; padding:8px; border-radius:6px; font-size:12px; color:#f8fafc; word-break:break-all;">
            ${c.user_pass}
          </div>
          <p style="font-size:11px; color:#94a3b8; margin-top:6px;">${c.descripcion || 'Sin descripción'}</p>
        </div>
        <div style="display:flex; justify-content:space-between; align-items:center; margin-top:14px; padding-top:10px; border-top:1px solid var(--border-subtle);">
          <button onclick="copiarAlPortapapeles('${c.user_pass}')" class="btn btn-secondary" style="padding:4px 10px; font-size:11px;">
            📋 Copiar
          </button>
          <button onclick="eliminarCuentaInv(${c.id})" class="btn btn-danger" style="padding:4px 10px; font-size:11px;">
            🗑️ Eliminar
          </button>
        </div>
      </div>
    `).join('');
  } catch (error) {
    container.innerHTML = `<div style="color:#f43f5e; text-align:center; grid-column:1/-1;">Error: ${error.message}</div>`;
  }
}

async function agregarCuentaSubmit(e) {
  e.preventDefault();
  const user_pass = document.getElementById('inv-user-pass').value.trim();
  const elo_tipo = document.getElementById('inv-elo').value;
  const descripcion = document.getElementById('inv-desc').value.trim();

  try {
    await api.agregarCuenta({ user_pass, elo_tipo, descripcion });
    api.showToast('Cuenta agregada al inventario.');
    document.getElementById('modal-add-cuenta').classList.remove('active');
    document.getElementById('form-add-cuenta').reset();
    renderInventario();
  } catch (error) {
    console.error(error);
  }
}

async function agregarLoteSubmit(e) {
  e.preventDefault();
  const cuentasRaw = document.getElementById('lote-cuentas-raw').value.split('\n').filter(c => c.trim() !== '');
  const elo_tipo = document.getElementById('lote-elo').value;

  try {
    const res = await api.agregarLoteCuentas({ cuentas: cuentasRaw, elo_tipo, descripcion: 'Lote Importado' });
    api.showToast(`Lote procesado: ${res.agregadas} agregadas, ${res.duplicadas} duplicadas.`);
    document.getElementById('modal-add-lote').classList.remove('active');
    document.getElementById('form-add-lote').reset();
    renderInventario();
  } catch (error) {
    console.error(error);
  }
}

async function eliminarCuentaInv(id) {
  if (!confirm(`¿Estás seguro de eliminar la cuenta #${id} del inventario?`)) return;
  try {
    await api.eliminarCuenta(id);
    api.showToast(`Cuenta #${id} eliminada.`);
    renderInventario();
  } catch (error) {
    console.error(error);
  }
}

function copiarAlPortapapeles(texto) {
  navigator.clipboard.writeText(texto).then(() => {
    api.showToast('Credenciales copiadas al portapapeles.');
  });
}
