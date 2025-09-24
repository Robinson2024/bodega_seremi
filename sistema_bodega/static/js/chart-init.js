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

    console.log("Datos del gráfico cargados:", chartData);        // Inicializar el gráfico si hay datos válidos
        if (chartData && chartData.totalProductos > 0) {
            console.log("Inicializando gráfico con datos:", chartData.porcentajes);
            const ctx = canvas.getContext('2d');
            if (!ctx) {
                console.error("No se pudo obtener el contexto 2D del canvas");
                return;
            }

            // Optimizar el canvas para alta resolución y nitidez
            const devicePixelRatio = window.devicePixelRatio || 1;
            const rect = canvas.getBoundingClientRect();
            
            // Configurar el tamaño del canvas para alta resolución
            canvas.width = rect.width * devicePixelRatio;
            canvas.height = rect.height * devicePixelRatio;
            canvas.style.width = rect.width + 'px';
            canvas.style.height = rect.height + 'px';
            
            // Escalar el contexto para alta resolución
            ctx.scale(devicePixelRatio, devicePixelRatio);
            
            // Configuraciones avanzadas para renderizado súper nítido
            ctx.imageSmoothingEnabled = true;
            ctx.imageSmoothingQuality = 'high';
            ctx.textRenderingOptimization = 'optimizeQuality';
            
            // Configuraciones adicionales para nitidez
            canvas.style.imageRendering = '-webkit-optimize-contrast';
            canvas.style.imageRendering = '-moz-crisp-edges';  
            canvas.style.imageRendering = 'crisp-edges';
            canvas.style.imageRendering = 'pixelated';

        // Función para crear gradientes radiales 3D
        function createGradient(context, color1, color2, color3) {
            const gradient = context.createRadialGradient(0, 0, 0, 0, 0, 200);
            gradient.addColorStop(0, color1);
            gradient.addColorStop(0.6, color2);
            gradient.addColorStop(1, color3);
            return gradient;
        }

        // Colores modernos con gradientes 3D realistas - SIN HOVER EFFECTS
        const colors = {
            bajo: {
                background: createGradient(ctx, '#FF4757', '#FF3742', '#FF6B7D'),
                border: '#FF3742'
            },
            medio: {
                background: createGradient(ctx, '#FFA502', '#FF9500', '#FFBA3A'),
                border: '#FF9500'
            },
            alto: {
                background: createGradient(ctx, '#2ED573', '#26D063', '#45E682'),
                border: '#26D063'
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
                    // Mantener los mismos colores para hover para evitar cambios visuales
                    hoverBackgroundColor: [
                        colors.bajo.background,
                        colors.medio.background,
                        colors.alto.background
                    ],
                    hoverBorderColor: [
                        colors.bajo.border,
                        colors.medio.border,
                        colors.alto.border
                    ],
                    hoverBorderWidth: 3,
                    cutout: '70%',
                    spacing: 2,
                    // Desactivar completamente efectos de hover visuales
                    hoverOffset: 0,
                    borderAlign: 'inner'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: {
                    animateRotate: true, // Reactivar para la entrada espectacular
                    animateScale: false, // Mantener desactivado para nitidez
                    duration: 2000, // Duración más larga para efecto dramático
                    easing: 'easeOutBack', // Easing dramático para entrada espectacular
                    delay: (context) => {
                        return context.dataIndex * 300; // Delay más largo para efecto escalonado
                    }
                },
                // Transiciones completamente deshabilitadas para máxima nitidez
                transitions: {
                    hover: {
                        duration: 0,
                        animation: {
                            duration: 0
                        }
                    },
                    active: {
                        duration: 0,
                        animation: {
                            duration: 0
                        }
                    }
                },
                interaction: {
                    intersect: true,
                    mode: 'point'
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
                        padding: 16,
                        usePointStyle: true,
                        titleFont: {
                            size: 15,
                            weight: 'bold',
                            family: "'Roboto', Arial, sans-serif"
                        },
                        bodyFont: {
                            size: 14,
                            weight: '500',
                            family: "'Roboto', Arial, sans-serif"
                        },
                        // Tooltip súper nítido y sin animaciones
                        position: 'nearest',
                        caretSize: 8,
                        caretPadding: 12,
                        animation: false, // Completamente sin animación para tooltip
                        // Configuraciones para tooltip estable y nítido
                        filter: function(tooltipItem) {
                            return true;
                        },
                        callbacks: {
                            title: function(tooltipItems) {
                                return tooltipItems[0].label;
                            },
                            label: function(context) {
                                const value = context.parsed || 0;
                                return `${value.toFixed(1)}% del inventario`;
                            },
                            afterLabel: function(context) {
                                const labels = ['🔴 Requiere atención', '🟡 Nivel moderado', '🟢 Stock saludable'];
                                return labels[context.dataIndex] || '';
                            }
                        }
                    }
                },
                onHover: (event, activeElements) => {
                    // Solo cambio de cursor, sin efectos visuales adicionales
                    event.native.target.style.cursor = activeElements.length > 0 ? 'pointer' : 'default';
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
                    // Animación de contador espectacular mejorada
                    if (!chart.animatedCounter) {
                        chart.animatedCounter = true;
                        let currentNumber = 0;
                        const targetNumber = chartData.totalProductos;
                        const duration = 3000; // 3 segundos para más drama
                        const startTime = Date.now();
                        
                        const animateCounter = () => {
                            const elapsed = Date.now() - startTime;
                            const progress = Math.min(elapsed / duration, 1);
                            
                            // Función de easing más dramática para la entrada
                            const easeOutElastic = (t) => {
                                if (t === 0) return 0;
                                if (t === 1) return 1;
                                const c4 = (2 * Math.PI) / 3;
                                return Math.pow(2, -10 * t) * Math.sin((t * 10 - 0.75) * c4) + 1;
                            };
                            
                            const easedProgress = easeOutElastic(progress);
                            currentNumber = Math.floor(targetNumber * easedProgress);
                            
                            chart.animatedNumber = currentNumber;
                            chart.draw();
                            
                            if (progress < 1) {
                                requestAnimationFrame(animateCounter);
                            } else {
                                chart.animatedNumber = targetNumber;
                                chart.draw();
                            }
                        };
                        
                        // Iniciar la animación con el gráfico
                        setTimeout(() => {
                            if (targetNumber > 0) {
                                animateCounter();
                            }
                        }, 1500); // Delay para sincronizar con la entrada del contenedor
                    }
                }
            }
            ]
        });

        // Entrada espectacular del canvas sincronizada con CSS
        canvas.style.opacity = '0';
        canvas.style.transform = 'scale(0.5) rotate(-10deg)';
        canvas.style.filter = 'blur(5px)';
        
        // Animación de entrada del canvas
        setTimeout(() => {
            canvas.style.transition = 'all 1.5s cubic-bezier(0.23, 1, 0.32, 1)';
            canvas.style.opacity = '1';
            canvas.style.transform = 'scale(1) rotate(0deg)';
            canvas.style.filter = 'blur(0px)';
            
            // Limpiar la transición después de la animación para mantener nitidez
            setTimeout(() => {
                canvas.style.transition = 'none';
            }, 1500);
        }, 1200); // Sincronizado con la animación del contenedor

    } else {
        console.log("No hay datos para mostrar el gráfico (chartData no definido o totalProductos <= 0)");
    }
});