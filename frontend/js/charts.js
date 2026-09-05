let comparisonChartInstance = null;
let decisionsChartInstance = null;

function getOrCreateEmptyOverlay(canvas, id, text) {
    const parent = canvas.parentElement;
    let overlay = document.getElementById(id);
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = id;
        overlay.style.position = 'absolute';
        overlay.style.top = '0';
        overlay.style.left = '0';
        overlay.style.right = '0';
        overlay.style.bottom = '0';
        overlay.style.display = 'flex';
        overlay.style.alignItems = 'center';
        overlay.style.justifyContent = 'center';
        overlay.style.flexDirection = 'column';
        overlay.style.gap = '8px';
        overlay.style.color = 'var(--text-muted, #718096)';
        overlay.style.fontSize = '14px';
        overlay.style.fontWeight = '500';
        overlay.style.background = 'rgba(255, 255, 255, 0.95)';
        overlay.style.borderRadius = '8px';
        overlay.style.zIndex = '2';
        overlay.style.pointerEvents = 'none';
        parent.style.position = 'relative';
        parent.appendChild(overlay);
    }
    overlay.innerHTML = `<span style="font-size: 24px; opacity: 0.6;">📊</span><span>${text}</span>`;
    return overlay;
}

/**
 * Render or update the Baseline vs AI Comparison Bar Chart
 */
function updateComparisonChart(comparisonData) {
    const canvas = document.getElementById('comparisonChart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    if (comparisonChartInstance) {
        comparisonChartInstance.destroy();
    }

    const totalRetries = comparisonData?.baseline?.retry_attempts || 0;
    const overlay = getOrCreateEmptyOverlay(canvas, 'comparison-empty-overlay', 'No analyzed transactions yet.');

    if (totalRetries === 0) {
        overlay.style.display = 'flex';
        // Render empty chart with 0s
        comparisonChartInstance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Naive Baseline', 'Adaptive AI Engine'],
                datasets: [{
                    label: 'Recovery Rate (%)',
                    data: [0, 0],
                    backgroundColor: ['rgba(178, 206, 255, 0.4)', 'rgba(49, 162, 76, 0.4)'],
                    borderRadius: 8,
                    barThickness: 48
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: { beginAtZero: true, max: 100, ticks: { callback: v => v + '%' } },
                    x: { grid: { display: false } }
                }
            }
        });
        return;
    }

    overlay.style.display = 'none';

    const baselineRate = comparisonData?.baseline?.recovery_rate ?? 0.0;
    const aiRate = comparisonData?.ai_model?.recovery_rate ?? 0.0;

    comparisonChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Naive Baseline (Blind Retry All)', 'Adaptive AI Recovery Engine'],
            datasets: [{
                label: 'Recovery Rate (%)',
                data: [baselineRate, aiRate],
                backgroundColor: [
                    'rgba(178, 206, 255, 0.75)',
                    'rgba(49, 162, 76, 0.85)'
                ],
                borderColor: [
                    '#0052CC',
                    '#27873F'
                ],
                borderWidth: 2,
                borderRadius: 8,
                barThickness: 56
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return ` Recovery Rate: ${context.raw}%`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    },
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        },
                        font: {
                            family: 'Inter, -apple-system, sans-serif'
                        }
                    }
                },
                x: {
                    grid: { display: false },
                    ticks: {
                        font: {
                            weight: '600',
                            family: 'Inter, -apple-system, sans-serif'
                        }
                    }
                }
            }
        }
    });
}

/**
 * Render or update the Recovery Decisions Distribution Doughnut Chart
 */
function updateDecisionsChart(overviewData) {
    const canvas = document.getElementById('decisionsChart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    if (decisionsChartInstance) {
        decisionsChartInstance.destroy();
    }

    const retryCount = overviewData?.retry_recommended || 0;
    const stopCount = overviewData?.stop_recommended || 0;
    const customerActionCount = overviewData?.customer_action_recommended || 0;
    const total = retryCount + stopCount + customerActionCount;

    const overlay = getOrCreateEmptyOverlay(canvas, 'decisions-empty-overlay', 'No analyzed transactions yet.');

    if (total === 0) {
        overlay.style.display = 'flex';
        return;
    }

    overlay.style.display = 'none';

    decisionsChartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: [
                `Immediate Retry (${retryCount})`,
                `Stop Retry (${stopCount})`,
                `Customer Action (${customerActionCount})`
            ],
            datasets: [{
                data: [retryCount, stopCount, customerActionCount],
                backgroundColor: [
                    '#0052CC', // Primary Blue
                    '#E74C3C', // Danger Red
                    '#F79646'  // Warning Orange
                ],
                hoverOffset: 6,
                borderWidth: 2,
                borderColor: '#ffffff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '68%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        usePointStyle: true,
                        boxWidth: 8,
                        padding: 16,
                        font: {
                            family: 'Inter, -apple-system, sans-serif',
                            size: 12
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const val = context.raw;
                            const pct = total > 0 ? ((val / total) * 100).toFixed(1) : 0;
                            return ` ${context.label}: ${val} (${pct}%)`;
                        }
                    }
                }
            }
        }
    });
}
