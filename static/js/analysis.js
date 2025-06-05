// Configuration de base des graphiques
const chartConfig = {
    type: 'line',
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: false
            }
        },
        scales: {
            x: {
                grid: {
                    display: false
                }
            },
            y: {
                beginAtZero: true
            }
        }
    }
};

// Préparation des données
const dates = monthlyData.map(item => item.date);
const temperatures = monthlyData.map(item => item.temp_mean);
const gddCumul = monthlyData.map(item => item.gdd_cumul);

// Graphique des températures moyennes
const tempChart = new Chart(
    document.getElementById('monthlyTempChart'),
    {
        ...chartConfig,
        data: {
            labels: dates,
            datasets: [{
                label: 'Température Moyenne (°C)',
                data: temperatures,
                borderColor: '#dc3545',
                backgroundColor: 'rgba(220, 53, 69, 0.1)',
                fill: true,
                tension: 0.4
            }]
        }
    }
);

// Graphique du GDD cumulé
const gddChart = new Chart(
    document.getElementById('monthlyGddChart'),
    {
        ...chartConfig,
        data: {
            labels: dates,
            datasets: [{
                label: 'GDD Cumulé',
                data: gddCumul,
                borderColor: '#198754',
                backgroundColor: 'rgba(25, 135, 84, 0.1)',
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            ...chartConfig.options,
            scales: {
                ...chartConfig.options.scales,
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: '°C-jours'
                    }
                }
            }
        }
    }
);
