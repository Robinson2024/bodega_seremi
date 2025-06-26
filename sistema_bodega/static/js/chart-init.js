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

        // Función para crear gradientes radiales 3D
        function createGradient(context, color1, color2, color3) {
            const gradient = context.createRadialGradient(0, 0, 0, 0, 0, 200);
            gradient.addColorStop(0, color1);
            gradient.addColorStop(0.6, color2);
            gradient.addColorStop(1, color3);
            return gradient;
        }

        // Colores modernos con gradientes 3D realistas
        const colors = {
            bajo: {
                background: createGradient(ctx, '#FF4757', '#FF3742', '#FF6B7D'),
                border: '#FF3742',
                hover: createGradient(ctx, '#FF5A67', '#FF4757', '#FF7B8D') // Más sutil
            },
            medio: {
                background: createGradient(ctx, '#FFA502', '#FF9500', '#FFBA3A'),
                border: '#FF9500',
                hover: createGradient(ctx, '#FFB020', '#FFA502', '#FFC450') // Más sutil
            },
            alto: {
                background: createGradient(ctx, '#2ED573', '#26D063', '#45E682'),
                border: '#26D063',
                hover: createGradient(ctx, '#40DD83', '#2ED573', '#55EE92') // Más sutil
            }
        };

        const stockChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Stock Bajo (1-10)', 'Stock Medio (11-50)', 'Stock Alto (51+)'],
                datasets: [{
                    label: 'Distribución de Stock',
                    data: chartData.porcentajes,
                    backgroundColor: [
                        colors.bajo.background,
                        colors.medio.background,
                        colors.alto.background
                    ],
                    borderColor: [
                        colors.bajo.border,
                        colors.medio.border,
                        colors.alto.border
                    ],
                    borderWidth: 3,
                    hoverBackgroundColor: [
                        colors.bajo.hover,
                        colors.medio.hover,
                        colors.alto.hover
                    ],
                    hoverBorderWidth: 3, // Reducido de 4 a 3
                    cutout: '70%',
                    spacing: 2,
                    // Configuración de transiciones suaves
                    hoverOffset: 4, // Separación sutil al hacer hover
                    borderAlign: 'inner'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: {
                    animateRotate: true,
                    animateScale: true,
                    duration: 3000,
                    easing: 'easeInOutElastic',
                    delay: (context) => {
                        return context.dataIndex * 300; // Animación escalonada
                    }
                },
                // Configuración de transiciones suaves para hover
                transitions: {
                    hover: {
                        duration: 300,
                        easing: 'easeInOutCubic'
                    },
                    active: {
                        duration: 200,
                        easing: 'easeOutQuart'
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'nearest'
                },
                elements: {
                    arc: {
                        borderWidth: 3, // Reducido de 4 a 3
                        borderJoinStyle: 'round',
                        borderRadius: 6, // Reducido de 8 a 6
                        // Sombras más sutiles
                        shadowOffsetX: 2, // Reducido de 3 a 2
                        shadowOffsetY: 2, // Reducido de 3 a 2
                        shadowBlur: 6, // Reducido de 10 a 6
                        shadowColor: 'rgba(0, 0, 0, 0.15)' // Reducido opacidad de 0.3 a 0.15
                    }
                },
                plugins: {
                    legend: { 
                        display: false 
                    },
                    tooltip: {
                        enabled: true,
                        backgroundColor: 'rgba(255, 255, 255, 0.98)',
                        titleColor: '#2D3748',
                        bodyColor: '#4A5568',
                        borderColor: 'rgba(0, 0, 0, 0.1)',
                        borderWidth: 2,
                        cornerRadius: 12,
                        displayColors: true,
                        padding: 12,
                        titleFont: {
                            size: 14,
                            weight: 'bold'
                        },
                        bodyFont: {
                            size: 13,
                            weight: '500'
                        },
                        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.15)',
                        callbacks: {
                            title: function(tooltipItems) {
                                return tooltipItems[0].label;
                            },
                            label: function(context) {
                                const value = context.parsed || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(1);
                                return `${value}% del inventario (${percentage}% del gráfico)`;
                            },
                            afterLabel: function(context) {
                                const labels = ['🔴 Requiere atención', '🟡 Nivel moderado', '🟢 Stock saludable'];
                                return labels[context.dataIndex] || '';
                            }
                        }
                    }
                },
                onHover: (event, activeElements) => {
                    event.native.target.style.cursor = activeElements.length > 0 ? 'pointer' : 'default';
                    // Transición suave del cursor
                    event.native.target.style.transition = 'all 0.2s ease';
                }
            },
            plugins: [{
                id: 'centerText',
                beforeDraw: function(chart) {
                    const ctx = chart.ctx;
                    const centerX = chart.chartArea.left + (chart.chartArea.right - chart.chartArea.left) / 2;
                    const centerY = chart.chartArea.top + (chart.chartArea.bottom - chart.chartArea.top) / 2;
                    
                    ctx.save();
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'middle';
                    
                    // Sombra para el texto principal
                    ctx.shadowColor = 'rgba(0, 0, 0, 0.3)';
                    ctx.shadowOffsetX = 2;
                    ctx.shadowOffsetY = 2;
                    ctx.shadowBlur = 4;
                    
                    // Total de productos (número grande con gradiente)
                    const gradient = ctx.createLinearGradient(0, centerY - 40, 0, centerY + 10);
                    gradient.addColorStop(0, '#667eea');
                    gradient.addColorStop(1, '#764ba2');
                    
                    ctx.font = 'bold 3rem "Roboto", Arial, sans-serif';
                    ctx.fillStyle = gradient;
                    ctx.fillText(chart.animatedNumber || chartData.totalProductos, centerX, centerY - 15);
                    
                    // Resetear sombra
                    ctx.shadowColor = 'transparent';
                    ctx.shadowOffsetX = 0;
                    ctx.shadowOffsetY = 0;
                    ctx.shadowBlur = 0;
                    
                    // Texto "productos" con estilo más sutil
                    ctx.font = 'normal 1.1rem "Roboto", Arial, sans-serif';
                    ctx.fillStyle = '#8E9AAF';
                    ctx.fillText('PRODUCTOS', centerX, centerY + 25);
                    
                    // Línea decorativa
                    ctx.beginPath();
                    ctx.moveTo(centerX - 30, centerY + 40);
                    ctx.lineTo(centerX + 30, centerY + 40);
                    ctx.strokeStyle = '#E2E8F0';
                    ctx.lineWidth = 2;
                    ctx.stroke();
                    
                    ctx.restore();
                }
            }, {
                id: 'animatedCounter',
                afterRender: function(chart) {
                    // Animación de contador mejorada
                    if (!chart.animatedCounter) {
                        chart.animatedCounter = true;
                        let currentNumber = 0;
                        const targetNumber = chartData.totalProductos;
                        const duration = 2000; // 2 segundos
                        const startTime = Date.now();
                        
                        const animateCounter = () => {
                            const elapsed = Date.now() - startTime;
                            const progress = Math.min(elapsed / duration, 1);
                            
                            // Función de easing para suavizar la animación
                            const easeOutQuart = 1 - Math.pow(1 - progress, 4);
                            currentNumber = Math.floor(targetNumber * easeOutQuart);
                            
                            chart.animatedNumber = currentNumber;
                            chart.draw();
                            
                            if (progress < 1) {
                                requestAnimationFrame(animateCounter);
                            } else {
                                chart.animatedNumber = targetNumber;
                                chart.draw();
                            }
                        };
                        
                        // Iniciar la animación después de un delay
                        setTimeout(() => {
                            if (targetNumber > 0) {
                                animateCounter();
                            }
                        }, 800);
                    }
                }
            }, {
                id: 'hoverEffects',
                beforeDatasetsDraw: function(chart, args, options) {
                    const ctx = chart.ctx;
                    const meta = chart.getDatasetMeta(0);
                    
                    // Efectos de hover 3D más sutiles
                    meta.data.forEach((arc, index) => {
                        if (arc.active) {
                            ctx.save();
                            // Sombras más suaves para hover
                            ctx.shadowColor = 'rgba(0, 0, 0, 0.2)'; // Reducido de 0.4 a 0.2
                            ctx.shadowOffsetX = 2; // Reducido de 4 a 2
                            ctx.shadowOffsetY = 2; // Reducido de 4 a 2
                            ctx.shadowBlur = 8; // Reducido de 15 a 8
                            ctx.restore();
                        }
                    });
                }
            }]
        });

        // Añadir animación de entrada suave
        setTimeout(() => {
            canvas.style.opacity = '1';
            canvas.style.transform = 'scale(1)';
        }, 100);

    } else {
        console.log("No hay datos para mostrar el gráfico (chartData no definido o totalProductos <= 0)");
    }
});