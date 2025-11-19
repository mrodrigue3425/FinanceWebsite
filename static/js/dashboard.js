window.addEventListener("DOMContentLoaded", () => {

    // === 1. DATE PICKER ===

    // computus algorithm for easter sunday
    function getEasterDate(year) {
        const a = year % 19;
        const b = Math.floor(year / 100);
        const c = year % 100;
        const d = Math.floor(b / 4);
        const e = b % 4;
        const f = Math.floor((b + 8) / 25);
        const g = Math.floor((b - f + 1) / 3);
        const h = (19 * a + b - d - g + 15) % 30;
        const i = Math.floor(c / 4);
        const k = c % 4;
        const l = (32 + 2 * e + 2 * i - h - k) % 7;
        const m = Math.floor((a + 11 * h + 22 * l) / 451);
        const month = Math.floor((h + l - 7 * m + 114) / 31) - 1;  
        const day = ((h + l - 7 * m + 114) % 31) + 1;
    
        return new Date(year, month, day);
    }

    flatpickr("#date-selector", {
        dateFormat: "d/m/Y",
        defaultDate: window.anchorDate,
        maxDate: window.anchorDate,
        allowInput: true,
        
        // disable non business days
        "disable": [
            // weekends
            function(date) {
                return (date.getDay() === 0 || date.getDay() === 6);
    
            },

            // christmas: 25/12
            function(date) {
                return (date.getMonth() === 11 && date.getDate() === 25);
            },
            // new years day: 01/01
            function(date) {
                return (date.getMonth() === 0 && date.getDate() === 1);
            },
            // labor day: 01/05
            function(date) {
                return (date.getMonth() === 4 && date.getDate() === 1);
            },
            // independence day: 16/09
            function(date) {
                return (date.getMonth() === 8 && date.getDate() === 16);
            },
            // virgin of guadalupe day
            function(date) {
                return (date.getMonth() === 11 && date.getDate() === 12);
            },
            // all saints day: 01/11
            function(date) {
                return (date.getMonth() === 10 && date.getDate() === 1);
            },

            // constitution day: every first monday of february
            function(date) {
                return (
                    date.getDay() === 1 &&
                    date.getMonth() === 1 &&
                    date.getDate() < 8)
            },
            // revolution day: every third monday of november
            function(date) {
                return (
                    date.getDay() === 1 &&
                    date.getMonth() === 10 &&
                    date.getDate() > 14 &&
                    date.getDate() < 22
                )
            },
            // benito juarez birthday: every third monday of march
            function(date) {
                return(
                    date.getMonth() === 2 &&    
                    date.getDay() === 1 &&      
                    date.getDate() > 14 &&     
                    date.getDate() < 22        
                )
            },
            // holy thursday and friday: thursday and friday preceding easter sunday
            function(date) {
                const year = date.getFullYear();
                const easter = getEasterDate(year);

                console.log(easter)

                const holyThursday = new Date(easter);
                holyThursday.setDate(holyThursday.getDate() -3)

                const holyFriday = new Date(easter)
                holyFriday.setDate(holyFriday.getDate() -2)

                return(
                    date.toDateString() ===  holyThursday.toDateString() ||
                    date.toDateString() === holyFriday.toDateString()
                )
            },
        ],
        onOpen(selectedDates, dateStr, instance) {
            instance.calendarContainer.style.fontFamily = 'Inter, system-ui, sans-serif';
            instance.calendarContainer.style.fontSize = '1rem';
        }
    });

    // === 2. SUMMARY TOOLTIP INITIALIZATION ===
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });


    // === 3. CHART ===
    const { labels, yields, dtms, prices, ids } = window.curveData;

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
                            return `${labels[i]}\n${ids[i]}`;
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