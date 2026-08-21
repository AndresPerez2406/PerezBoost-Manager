/**
 * PEREZBOOST PRO — FINANZAS & LIQUIDACIONES MODULE
 */

async function renderFinanzas() {
  const saldosTbody = document.getElementById('saldos-tbody');
  const txTbody = document.getElementById('tx-tbody');
  const binanceTotal = document.getElementById('fin-binance-total');
  const netoTotal = document.getElementById('fin-neto-total');
  const boteTotal = document.getElementById('fin-bote-total');

  if (!saldosTbody) return;

  try {
    const [saldos, wallet, txs] = await Promise.all([
      api.getSaldosPendientes(),
      api.getWalletBalance(),
      api.getWalletTransacciones()
    ]);

    if (binanceTotal) binanceTotal.textContent = `$${wallet.total_binance.toFixed(2)}`;
    if (netoTotal) netoTotal.textContent = `$${wallet.saldo_neto.toFixed(2)}`;
    if (boteTotal) boteTotal.textContent = `$${wallet.saldo_bote.toFixed(2)}`;

    // 1. Render Liquidaciones Pendientes
    if (saldos.length === 0) {
      saldosTbody.innerHTML = '<tr><td colspan="4" style="text-align:center; padding:24px; color:#10b981;">🎉 No hay pagos pendientes. ¡Todo el staff está al día!</td></tr>';
    } else {
      saldosTbody.innerHTML = saldos.map(s => `
        <tr>
          <td><b>${s.booster_nombre}</b></td>
          <td><span class="badge badge-progreso">${s.cantidad_pedidos} pedidos</span></td>
          <td><b style="color:#10b981; font-size:14px;">$${s.total_pendiente.toFixed(2)}</b></td>
          <td>
            <button onclick="ejecutarLiquidacion('${s.booster_nombre}', ${s.total_pendiente})" class="btn btn-primary" style="padding:6px 14px; font-size:12px;">
              💸 Liquidar
            </button>
          </td>
        </tr>
      `).join('');
    }

    // 2. Render Transacciones Binance
    if (txTbody) {
      txTbody.innerHTML = txs.slice(0, 10).map(t => {
        const isIngreso = t.tipo === 'INGRESO';
        return `
          <tr>
            <td><small style="color:#64748b;">${t.fecha || '-'}</small></td>
            <td><span class="badge ${isIngreso ? 'badge-terminado' : 'badge-abandonado'}">${t.tipo}</span></td>
            <td><b>${t.categoria}</b></td>
            <td style="color:${isIngreso ? '#10b981' : '#f43f5e'}; font-weight:700;">${isIngreso ? '+' : '-'}$${t.monto.toFixed(2)}</td>
            <td><small style="color:#94a3b8;">${t.descripcion || '-'}</small></td>
          </tr>
        `;
      }).join('');
    }
  } catch (error) {
    console.error('Error cargando finanzas:', error);
  }
}

async function ejecutarLiquidacion(boosterNombre, monto) {
  if (!confirm(`¿Confirmas la liquidación de $${monto.toFixed(2)} para ${boosterNombre}?`)) return;

  try {
    await api.liquidarBooster(boosterNombre);
    api.showToast(`Pagos liquidados con éxito para ${boosterNombre}.`);
    renderFinanzas();
  } catch (error) {
    console.error(error);
  }
}

async function agregarTransaccionWallet(e) {
  e.preventDefault();
  const tipo = document.getElementById('tx-tipo').value;
  const categoria = document.getElementById('tx-cat').value;
  const monto = parseFloat(document.getElementById('tx-monto').value);
  const descripcion = document.getElementById('tx-desc').value.trim();

  try {
    await api.crearTransaccionWallet({ tipo, categoria, monto, descripcion });
    api.showToast('Transacción registrada en Wallet.');
    document.getElementById('modal-add-tx').classList.remove('active');
    document.getElementById('form-add-tx').reset();
    renderFinanzas();
  } catch (error) {
    console.error(error);
  }
}
