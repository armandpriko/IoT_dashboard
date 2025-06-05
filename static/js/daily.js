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
const times = dailyData.map(item => item.time);
const temperatures = dailyData.map(item => item.temperature);
const humidity = dailyData.map(item => item.humidity);

// Graphique des températures
const tempChart = new Chart(
    document.getElementById('dailyTempChart'),
    {
        ...chartConfig,
        data: {
            labels: times,
            datasets: [{
                label: 'Température (°C)',
                data: temperatures,
                borderColor: '#dc3545',
                backgroundColor: 'rgba(220, 53, 69, 0.1)',
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            ...chartConfig.options,
            plugins: {
                ...chartConfig.options.plugins,
                title: {
                    display: true,
                    text: 'Température Journalière'
                }
            }
        }
    }
);

// Graphique de l'humidité
const humidityChart = new Chart(
    document.getElementById('dailyHumidityChart'),
    {
        ...chartConfig,
        data: {
            labels: times,
            datasets: [{
                label: 'Humidité (%)',
                data: humidity,
                borderColor: '#0d6efd',
                backgroundColor: 'rgba(13, 110, 253, 0.1)',
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            ...chartConfig.options,
            plugins: {
                ...chartConfig.options.plugins,
                title: {
                    display: true,
                    text: 'Humidité Journalière'
                }
            }
        }
    }
);
