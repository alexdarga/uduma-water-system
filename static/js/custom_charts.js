/**
 * Graphiques JavaScript personnalisés pour Uduma Water Management
 * Utilise Chart.js pour des visualisations interactives
 */

// Configuration globale de Chart.js
Chart.defaults.font.family = 'Arial, sans-serif';
Chart.defaults.plugins.legend.position = 'top';
Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(0, 0, 0, 0.8)';
Chart.defaults.plugins.tooltip.titleColor = 'white';
Chart.defaults.plugins.tooltip.bodyColor = 'white';

/**
 * Créer un graphique de consommation mensuelle
 */
function createConsumptionChart(canvasId, data) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'Consommation (m³)',
                data: data.values,
                backgroundColor: 'rgba(54, 162, 235, 0.8)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 2,
                borderRadius: 4,
                borderSkipped: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Consommation Mensuelle par Point d\'Eau',
                    font: {
                        size: 16,
                        weight: 'bold'
                    }
                },
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Mois'
                    },
                    grid: {
                        display: false
                    }
                },
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Consommation (m³)'
                    }
                }
            },
            animation: {
                duration: 1000,
                easing: 'easeInOutQuart'
            }
        }
    });
}

/**
 * Créer un graphique de revenus avec tendance
 */
function createRevenueChart(canvasId, data) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'Revenus (FCFA)',
                data: data.values,
                borderColor: 'rgba(75, 192, 192, 1)',
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: 'rgba(75, 192, 192, 1)',
                pointBorderColor: 'white',
                pointBorderWidth: 2,
                pointRadius: 6,
                pointHoverRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Évolution des Revenus Mensuels',
                    font: {
                        size: 16,
                        weight: 'bold'
                    }
                },
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Mois'
                    }
                },
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Revenus (FCFA)'
                    },
                    ticks: {
                        callback: function(value) {
                            return value.toLocaleString('fr-FR') + ' FCFA';
                        }
                    }
                }
            },
            interaction: {
                intersect: false,
                mode: 'index'
            },
            animation: {
                duration: 1200,
                easing: 'easeInOutCubic'
            }
        }
    });
}

/**
 * Créer un graphique en secteurs pour les types de connexion
 */
function createConnectionTypePie(canvasId, data) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    const colors = [
        'rgba(255, 99, 132, 0.8)',
        'rgba(54, 162, 235, 0.8)',
        'rgba(255, 205, 86, 0.8)',
        'rgba(75, 192, 192, 0.8)'
    ];
    
    return new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.labels,
            datasets: [{
                data: data.values,
                backgroundColor: colors.slice(0, data.labels.length),
                borderColor: colors.slice(0, data.labels.length).map(color => color.replace('0.8', '1')),
                borderWidth: 2,
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Répartition par Type de Connexion',
                    font: {
                        size: 16,
                        weight: 'bold'
                    }
                },
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        usePointStyle: true
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((context.raw / total) * 100).toFixed(1);
                            return `${context.label}: ${context.raw} (${percentage}%)`;
                        }
                    }
                }
            },
            cutout: '50%',
            animation: {
                animateRotate: true,
                duration: 1000
            }
        }
    });
}

/**
 * Créer un graphique radar pour les performances
 */
function createPerformanceRadar(canvasId, data) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    return new Chart(ctx, {
        type: 'radar',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'Performance',
                data: data.values,
                borderColor: 'rgba(255, 99, 132, 1)',
                backgroundColor: 'rgba(255, 99, 132, 0.2)',
                borderWidth: 2,
                pointBackgroundColor: 'rgba(255, 99, 132, 1)',
                pointBorderColor: 'white',
                pointBorderWidth: 2,
                pointRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Analyse de Performance Multi-critères',
                    font: {
                        size: 16,
                        weight: 'bold'
                    }
                }
            },
            scales: {
                r: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        stepSize: 20
                    }
                }
            }
        }
    });
}

/**
 * Créer un graphique de comparaison multi-barres
 */
function createComparisonChart(canvasId, data) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.labels,
            datasets: [
                {
                    label: 'Consommation (m³)',
                    data: data.consumption,
                    backgroundColor: 'rgba(54, 162, 235, 0.8)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1,
                    yAxisID: 'y'
                },
                {
                    label: 'Revenus (k FCFA)',
                    data: data.revenue.map(v => v / 1000), // Convertir en milliers
                    backgroundColor: 'rgba(255, 99, 132, 0.8)',
                    borderColor: 'rgba(255, 99, 132, 1)',
                    borderWidth: 1,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Comparaison Consommation vs Revenus',
                    font: {
                        size: 16,
                        weight: 'bold'
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Points d\'Eau'
                    }
                },
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Consommation (m³)'
                    }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Revenus (k FCFA)'
                    },
                    grid: {
                        drawOnChartArea: false
                    }
                }
            }
        }
    });
}

/**
 * Créer un graphique de gauge circulaire (KPI)
 */
function createGaugeChart(canvasId, value, max, label) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    const percentage = (value / max) * 100;
    const color = percentage >= 80 ? 'rgba(75, 192, 192, 1)' : 
                  percentage >= 50 ? 'rgba(255, 205, 86, 1)' : 'rgba(255, 99, 132, 1)';
    
    return new Chart(ctx, {
        type: 'doughnut',
        data: {
            datasets: [{
                data: [value, max - value],
                backgroundColor: [color, 'rgba(200, 200, 200, 0.3)'],
                borderWidth: 0,
                circumference: 180,
                rotation: 270
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    enabled: false
                }
            },
            cutout: '80%'
        },
        plugins: [{
            id: 'gaugeText',
            beforeDraw: function(chart) {
                const ctx = chart.ctx;
                ctx.save();
                
                const centerX = chart.width / 2;
                const centerY = chart.height / 2 + 20;
                
                // Valeur principale
                ctx.fillStyle = color;
                ctx.font = 'bold 24px Arial';
                ctx.textAlign = 'center';
                ctx.fillText(value.toFixed(1), centerX, centerY - 10);
                
                // Label
                ctx.fillStyle = 'rgba(100, 100, 100, 1)';
                ctx.font = '14px Arial';
                ctx.fillText(label, centerX, centerY + 15);
                
                // Pourcentage
                ctx.fillStyle = 'rgba(150, 150, 150, 1)';
                ctx.font = '12px Arial';
                ctx.fillText(`${percentage.toFixed(1)}%`, centerX, centerY + 35);
                
                ctx.restore();
            }
        }]
    });
}

/**
 * Initialiser tous les graphiques avec des données d'exemple
 */
function initializeDashboardCharts() {
    // Données d'exemple
    const monthlyData = {
        labels: ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Jun', 'Jul'],
        values: [120, 150, 180, 140, 200, 175, 220]
    };
    
    const revenueData = {
        labels: ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Jun', 'Jul'],
        values: [85000, 95000, 105000, 88000, 110000, 98000, 115000]
    };
    
    const connectionData = {
        labels: ['Borne Fontaine', 'Connexion Privée'],
        values: [9, 6]
    };
    
    // Initialiser les graphiques s'ils existent
    if (document.getElementById('consumptionChart')) {
        createConsumptionChart('consumptionChart', monthlyData);
    }
    
    if (document.getElementById('revenueChart')) {
        createRevenueChart('revenueChart', revenueData);
    }
    
    if (document.getElementById('connectionPieChart')) {
        createConnectionTypePie('connectionPieChart', connectionData);
    }
}

// Initialiser quand le DOM est prêt
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboardCharts();
});

// Utilitaires pour la responsivité
function resizeCharts() {
    Chart.instances.forEach(function(instance) {
        instance.resize();
    });
}

window.addEventListener('resize', resizeCharts);