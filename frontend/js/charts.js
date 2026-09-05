let comparisonChartInstance = null;
let decisionsChartInstance = null;

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

    const baselineRate = comparisonData?.baseline?.recovery_rate ?? 12.0;
    const aiRate = comparisonData?.ai_model?.recovery_rate ?? 68.5;

    comparisonChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Baseline (Static Retry)', 'AI Recovery Engine'],
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

    // Fallback if zero
    const total = retryCount + stopCount + customerActionCount;
    const chartData = total > 0 
        ? [retryCount, stopCount, customerActionCount]
        : [1, 1, 1];

    decisionsChartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: [
                `Immediate Retry (${retryCount})`,
                `Stop Retry (${stopCount})`,
                `Customer Action (${customerActionCount})`
            ],
            datasets: [{
                data: chartData,
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
