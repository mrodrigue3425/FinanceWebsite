window.addEventListener("DOMContentLoaded", () => {
    
    // === 1. DATE PICKER ===
    flatpickr("#date-selector", {
        dateFormat: "d-m-Y",
        defaultDate: "2025-10-17",
        maxDate: "2025-10-17",
        allowInput: true,
        onOpen(selectedDates, dateStr, instance) {
            instance.calendarContainer.style.fontFamily = 'Inter, system-ui, sans-serif';
            instance.calendarContainer.style.fontSize = '1rem';
        }
    });


    // === 2. CHART ===
    const { labels, yields, dtms, prices } = window.curveData;

    const points = dtms.map((dtm, i) => ({
        x: dtm / 365.25,
        y: yields[i]
    }));

    const yieldCurve = document.getElementById('yieldCurveChart').getContext('2d');

    // Destroy existing chart if present
    if (window.yieldCurveChart instanceof Chart) {
        window.yieldCurveChart.destroy();
    }

    window.yieldCurveChart = new Chart(yieldCurve, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Yield (%)',
                    data: points,
                    borderColor: '#0d6efd',
                    backgroundColor: 'rgba(13, 110, 253, 0.1)',
                    showLine: false,
                    pointRadius: 5,
                    pointHoverRadius: 7
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                tooltip: {
                    displayColors: false,
                    callbacks: {
                        title(context) {
                            const i = context[0].dataIndex;
                            return labels[i];
                        },
                        label(context) {
                            const i = context.dataIndex;
                            return [
                                `Yield (%): ${context.parsed.y.toFixed(8)}`,
                                `Clean Price (MXN): ${prices[i].toFixed(6)}`,
                                `Days to Maturity: ${dtms[i].toLocaleString()}`
                            ];
                        }
                    },
                    titleFont: { family: '"Helvetica Neue", Helvetica, Arial, sans-serif', size: 15 },
                    bodyFont: { family: '"Helvetica Neue", Helvetica, Arial, sans-serif', size: 13 }
                },
                legend: { display: false }
            },
            scales: {
                x: {
                    type: 'linear',
                    title: { 
                        display: true,
                        font: { family: '"Helvetica Neue", Helvetica, Arial, sans-serif', size: 15 },
                        text: 'Term to Maturity (Years)'
                    }
                },
                y: {
                    title: {
                        display: true,
                        font: { family: '"Helvetica Neue", Helvetica, Arial, sans-serif', size: 15 },
                        text: 'Yield to Maturity (%)'
                    },
                }
            }
        }
    });

});