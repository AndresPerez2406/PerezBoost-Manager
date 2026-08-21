/**
 * PEREZBOOST PRO — DASHBOARD & ANALYTICS MODULE
 */

let financialChart = null;

async function renderDashboard() {
  const container = document.getElementById('view-dashboard');
  if (!container) return;

  try {
    const [finanzas, wallet, pedidosActivos] = await Promise.all([
      api.getFinanzasResumen(),
      api.getWalletBalance().catch(() => ({ total_binance: 0, saldo_neto: 0, saldo_bote: 0 })),
      api.getPedidosActivos().catch(() => [])
    ]);

    // 1. Render KPI Cards
    document.getElementById('kpi-neto').textContent = `$${finanzas.mi_neto.toFixed(2)}`;
    document.getElementById('kpi-ventas').textContent = `$${finanzas.ventas_totales.toFixed(2)}`;
    document.getElementById('kpi-bote').textContent = `$${finanzas.bote_ranking.toFixed(2)}`;
    document.getElementById('kpi-velocidad').textContent = `${finanzas.velocidad_media_dias.toFixed(1)} d`;
    document.getElementById('kpi-binance').textContent = `$${wallet.total_binance.toFixed(2)}`;
    document.getElementById('kpi-activos').textContent = pedidosActivos.length;

    // 2. Render Chart.js
    renderFinancialChart(finanzas);
  } catch (error) {
    console.error('Error cargando Dashboard:', error);
  }
}

function renderFinancialChart(data) {
  const canvas = document.getElementById('financialChart');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  if (financialChart) {
    financialChart.destroy();
  }

  financialChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['Pago Staff', 'Mi Neto (Perez)', 'Bote Ranking'],
      datasets: [{
        label: 'Monto USD ($)',
        data: [data.pago_staff, data.mi_neto, data.bote_ranking],
        backgroundColor: [
          'rgba(6, 182, 212, 0.75)',
          'rgba(16, 185, 129, 0.75)',
          'rgba(245, 158, 11, 0.75)'
        ],
        borderColor: [
          '#06b6d4',
          '#10b981',
          '#f59e0b'
        ],
        borderWidth: 2,
        borderRadius: 8
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#111827',
          titleColor: '#fff',
          bodyColor: '#10b981',
          borderColor: 'rgba(255,255,255,0.1)',
          borderWidth: 1,
          padding: 12,
          displayColors: false,
          callbacks: {
            label: (item) => `Total: $${item.raw.toFixed(2)} USD`
          }
        }
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { color: '#94a3b8', font: { weight: '600' } }
        },
        y: {
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: {
            color: '#94a3b8',
            callback: (val) => `$${val}`
          }
        }
      }
    }
  });
}
