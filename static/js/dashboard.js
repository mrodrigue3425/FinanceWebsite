window.addEventListener("DOMContentLoaded", () => {
  let currentCurveData = window.curveData || {};
  let currentSummaryData = window.summaryData || {};
  let currentAnchorDate = window.anchorDate || "";

  // elements to update
  let TIIEFContainer = document.getElementById("card-TIIEF");
  let TIIE28Container = document.getElementById("card-TIIE28");
  let TargetRateContainer = document.getElementById("card-TargetRate");
  let CPIYOYContainer = document.getElementById("card-MonthlyCPIYoY");
  let UDIContainer = document.getElementById("card-UDI_MXN");
  let USDContainer = document.getElementById("card-USD_MXN");

  const updateMap = {
    TIIEF: { container: TIIEFContainer, pre: "Effective Date: ", unit: "%" },
    TIIE28: { container: TIIE28Container, pre: "Effective Date: ", unit: "%" },
    TargetRate: {
      container: TargetRateContainer,
      pre: "Effective Date: ",
      unit: "%",
    },
    MonthlyCPIYoY: { container: CPIYOYContainer, pre: "", unit: "%" },
    UDI_MXN: { container: UDIContainer, pre: "Effective Date: ", unit: "" },
    USD_MXN: { container: USDContainer, pre: "Effective Date: ", unit: "" },
  };

  // --- chart update logic ---
  function updateYieldCurveChart(data) {
    currentCurveData = {
      labels: data.curve_labels,
      yields: data.curve_yields,
      dtms: data.curve_dtms,
      prices: data.curve_pxs,
      ids: data.curve_ids,
    };
    currentAnchorDate = data.anchor_date;

    let { labels, yields, dtms, prices, ids } = currentCurveData;

    // recalculate the points (x=years to maturity, y=yields)
    const points = dtms.map((dtm, i) => ({
      x: dtm / 365.25, // convert days to years
      y: yields[i],
    }));

    // update existing chart
    if (window.yieldCurveChart instanceof Chart) {
      // update data points and labels
      window.yieldCurveChart.data.labels = labels;
      window.yieldCurveChart.data.datasets[0].data = points;

      // re-render the chart
      window.yieldCurveChart.update();
    }
  }

  // --- summary update logic ---

  function updateSummaryTable(summaryData) {
    currentSummaryData = summaryData;

    for (const key in updateMap) {
      if (key) {
        console.log(`found ${key}`);

        const container = updateMap[key].container;
        const pre = updateMap[key].pre;
        const unit = updateMap[key].unit;

        // destroy current tooltip
        const tooltipInstance = bootstrap.Tooltip.getInstance(container);
        if (tooltipInstance) {
          tooltipInstance.dispose();
        }

        //update tooltip
        container.title = `${pre}${summaryData[key].date}`;
        new bootstrap.Tooltip(container);

        //update value
        container.querySelector(
          "h7"
        ).innerHTML = `${summaryData[key].value}${unit}`;
      }
    }
  }

  async function fetchCurveDataByDate(dateStr) {
    console.log(`Selected date: ${dateStr}`);
    const response = await fetch("/api/yield-curve", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        date: dateStr,
      }),
    });

    let data;

    try {
      data = await response.json();
    } catch (e) {
      if (!response.ok) {
        throw new Error(`Server Error: ${response.status}`);
      }
    }

    if (!response.ok) {
      const errorMessage = data?.message || "Unknown error";
      throw new Error(
        `Server returned error ${response.status}: ${errorMessage}`
      );
    }
    console.log("Success data:", data);

    // update yield curve chart
    updateYieldCurveChart(data);

    // update summary bar
    updateSummaryTable(data.summary_data);
  }

  // === 1. DATE PICKER ===

  // function to check if date is a holiday
  function isHoliday(date) {
    const d = date.getDate();
    const m = date.getMonth();
    const day = date.getDay();

    // fixed-date holidays
    if (m === 11 && d === 25) return `Christmas`;
    if (m === 0 && d === 1) return `New Year's Day`;
    if (m === 4 && d === 1) return `Labor Day`;
    if (m === 8 && d === 16) return `Independence Day`;
    if (m === 11 && d === 12) return `Our Lady of Guadalupe`;
    if (m === 10 && d === 1) return `All Saints Day`;

    // Constitution Day: first Monday of Feb
    if (m === 1 && day === 1 && d < 8) return `Constitution Day`;

    // Benito Juárez: third Monday of March
    if (m === 2 && day === 1 && d > 14 && d < 22)
      return `Birthday of Benito Juárez`;

    // Revolution Day: third Monday of November
    if (m === 10 && day === 1 && d > 14 && d < 22) return `Revolution Day`;

    // Holy Thursday & Friday
    const year = date.getFullYear();
    const easter = getEasterDate(year);

    const holyThu = new Date(easter);
    holyThu.setDate(holyThu.getDate() - 3);

    const holyFri = new Date(easter);
    holyFri.setDate(holyFri.getDate() - 2);

    if (date.toDateString() === holyThu.toDateString()) return `Holy Thursday`;
    if (date.toDateString() === holyFri.toDateString()) return `Holy Friday`;

    return false;
  }

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
    disable: [
      function (date) {
        // weekends
        if (date.getDay() === 0 || date.getDay() === 6) return true;

        // holidays
        return isHoliday(date);
      },
    ],
    onDayCreate: function (dObj, dStr, fp, dayElem) {
      const date = dayElem.dateObj;

      // WEEKENDS
      if (date.getDay() === 0 || date.getDay() === 6) {
        dayElem.classList.add("wknd");
        return;
      }

      // HOLIDAYS
      if (isHoliday(date)) {
        dayElem.classList.add("holiday");
        dayElem.title = isHoliday(date);
      }
    },
    onOpen(selectedDates, dateStr, instance) {
      instance.calendarContainer.style.fontFamily =
        "Inter, system-ui, sans-serif";
      instance.calendarContainer.style.fontSize = "1rem";
    },
    onChange: function (selectedDates, dateStr, instance) {
      if (selectedDates.length > 0) {
        fetchCurveDataByDate(dateStr);
      }
    },
  });

  // === 2. SUMMARY TOOLTIP INITIALIZATION ===
  var tooltipTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="tooltip"]')
  );
  var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });

  // === 3. CHART ===
  const { labels, yields, dtms, prices, ids } = window.curveData;

  const points = dtms.map((dtm, i) => ({
    x: dtm / 365.25,
    y: yields[i],
  }));

  const yieldCurve = document
    .getElementById("yieldCurveChart")
    .getContext("2d");

  // Destroy existing chart if present
  if (window.yieldCurveChart instanceof Chart) {
    window.yieldCurveChart.destroy();
  }

  window.yieldCurveChart = new Chart(yieldCurve, {
    type: "line",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Yield (%)",
          data: points,
          borderColor: "#0d6efd",
          backgroundColor: "rgba(13, 110, 253, 0.1)",
          showLine: false,
          pointRadius: 5,
          pointHoverRadius: 7,
        },
      ],
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
                `Days to Maturity: ${dtms[i].toLocaleString()}`,
              ];
            },
          },
          titleFont: {
            family: '"Helvetica Neue", Helvetica, Arial, sans-serif',
            size: 15,
          },
          bodyFont: {
            family: '"Helvetica Neue", Helvetica, Arial, sans-serif',
            size: 13,
          },
        },
        legend: { display: false },
      },
      scales: {
        x: {
          type: "linear",
          title: {
            display: true,
            font: {
              family: '"Helvetica Neue", Helvetica, Arial, sans-serif',
              size: 15,
            },
            text: "Term to Maturity (Years)",
          },
        },
        y: {
          title: {
            display: true,
            font: {
              family: '"Helvetica Neue", Helvetica, Arial, sans-serif',
              size: 15,
            },
            text: "Yield to Maturity (%)",
          },
        },
      },
    },
  });
});
