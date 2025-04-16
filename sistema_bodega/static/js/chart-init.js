document.addEventListener('DOMContentLoaded', function() {
    // Obtener el elemento canvas
    const canvas = document.getElementById('stockChart');
    if (!canvas) {
        console.error("No se encontró el elemento canvas con id 'stockChart'");
        return;
    }

    // Obtener los datos del atributo data-chart-data
    const chartDataString = canvas.getAttribute('data-chart-data');
    if (!chartDataString) {
        console.error("No se encontraron datos en el atributo data-chart-data");
        return;
    }

    // Parsear los datos JSON
    let chartData;
    try {
        chartData = JSON.parse(chartDataString);
    } catch (e) {
        console.error("Error al parsear los datos JSON:", e);
        return;
    }

    console.log("Datos del gráfico cargados:", chartData);

    // Inicializar el gráfico si hay datos válidos
    if (chartData && chartData.totalProductos > 0) {
        console.log("Inicializando gráfico con datos:", chartData.porcentajes);
        const ctx = canvas.getContext('2d');
        if (!ctx) {
            console.error("No se pudo obtener el contexto 2D del canvas");
            return;
        }

        const stockChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Stock Bajo (1-10)', 'Stock Medio (11-50)', 'Stock Alto (>50)'],
                datasets: [{
                    label: 'Distribución de Stock',
                    data: chartData.porcentajes,
                    backgroundColor: ['#dc3545', '#f59e0b', '#28a745'],
                    borderColor: ['#ffffff', '#ffffff', '#ffffff'],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    title: {
                        display: true,
                        text: 'Distribución de Stock de Productos',
                        font: {
                            size: 16,
                            weight: '500'
                        },
                        color: '#1a3c5e'
                    }
                }
            }
        });
    } else {
        console.log("No hay datos para mostrar el gráfico (chartData no definido o totalProductos <= 0)");
    }
});