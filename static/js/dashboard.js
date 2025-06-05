// Configuration des graphiques
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

// Initialisation des graphiques
const tempChart = new Chart(
    document.getElementById('tempChart'),
    {
        ...chartConfig,
        data: {
            labels: [],
            datasets: [{
                label: 'Température (°C)',
                data: [],
                borderColor: '#dc3545',
                backgroundColor: 'rgba(220, 53, 69, 0.1)',
                fill: true,
                tension: 0.4
            }]
        }
    }
);

const humidityChart = new Chart(
    document.getElementById('humidityChart'),
    {
        ...chartConfig,
        data: {
            labels: [],
            datasets: [{
                label: 'Humidité (%)',
                data: [],
                borderColor: '#0d6efd',
                backgroundColor: 'rgba(13, 110, 253, 0.1)',
                fill: true,
                tension: 0.4
            }]
        }
    }
);

// Fonction de mise à jour des données
function updateData() {
    fetch('/data')
        .then(response => response.json())
        .then(data => {
            // Mise à jour des valeurs actuelles
            if (data.length > 0) {
                document.getElementById('current-temp').textContent = data[0].temperature.toFixed(1);
                document.getElementById('current-humidity').textContent = data[0].humidity.toFixed(1);
                document.getElementById('current-gdd').textContent = data[0].gdd.toFixed(2);
                document.getElementById('last-update').textContent = new Date().toLocaleString();
            }

            // Préparation des données pour les graphiques
            const times = data.map(item => item.time).reverse();
            const temps = data.map(item => item.temperature).reverse();
            const humidity = data.map(item => item.humidity).reverse();

            // Mise à jour des graphiques
            tempChart.data.labels = times;
            tempChart.data.datasets[0].data = temps;
            tempChart.update();

            humidityChart.data.labels = times;
            humidityChart.data.datasets[0].data = humidity;
            humidityChart.update();
        })
        .catch(error => console.error('Erreur lors de la récupération des données:', error));
}

// Mise à jour initiale et rafraîchissement toutes les 5 minutes
updateData();
setInterval(updateData, 300000);
