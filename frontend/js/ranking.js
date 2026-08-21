/**
 * PEREZBOOST PRO — RANKING & LEADERBOARD MODULE
 */

async function renderRanking() {
  const container = document.getElementById('ranking-table-tbody');
  const boteTxt = document.getElementById('ranking-bote-total');
  const metaBadge = document.getElementById('ranking-meta-badge');
  const progressBar = document.getElementById('ranking-progress-bar');
  if (!container) return;

  try {
    const data = await api.getRanking();

    if (boteTxt) boteTxt.textContent = `$${data.bote_total.toFixed(2)}`;
    if (metaBadge) {
      metaBadge.textContent = data.meta_cumplida ? '✅ Meta Cumplida (+15 Pedidos)' : `⏳ En progreso (${data.pedidos_actuales}/15)`;
      metaBadge.style.color = data.meta_cumplida ? '#10b981' : '#f59e0b';
    }
    if (progressBar) {
      const pct = Math.min(Math.round((data.pedidos_actuales / 15) * 100), 100);
      progressBar.style.width = `${pct}%`;
    }

    const leaderboard = data.ranking || [];
    if (leaderboard.length === 0) {
      container.innerHTML = '<tr><td colspan="5" style="text-align:center; padding:30px; color:#94a3b8;">No hay boosters clasificados en el mes actual.</td></tr>';
      return;
    }

    container.innerHTML = leaderboard.map(item => {
      let medal = `#${item.rango}`;
      if (item.rango === 1) medal = '🥇 Oro';
      else if (item.rango === 2) medal = '🥈 Plata';
      else if (item.rango === 3) medal = '🥉 Bronce';

      return `
        <tr>
          <td style="font-weight:700; font-size:14px; color:${item.rango <= 3 ? '#f59e0b' : '#94a3b8'};">${medal}</td>
          <td><b style="font-size:14px;">${item.booster_nombre}</b></td>
          <td><span class="badge badge-terminado">${item.terminados} completados</span></td>
          <td>${item.high_wr > 0 ? `🔥 <b style="color:#f59e0b;">${item.high_wr}</b>` : '0'}</td>
          <td><b style="font-size:15px; color:#10b981;">${item.score} pts</b></td>
        </tr>
      `;
    }).join('');
  } catch (error) {
    container.innerHTML = `<tr><td colspan="5" style="text-align:center; padding:30px; color:#f43f5e;">Error: ${error.message}</td></tr>`;
  }
}
