document.addEventListener('DOMContentLoaded', function () {
    const container = document.getElementById('plateNotGoodMachineCard');
    if (!container) return;

    const ctx = document.getElementById('plateNotGoodByMachineChart');
    if (!ctx) return;

    const yearFilter = document.getElementById('yearFilter');
    const monthFilter = document.getElementById('monthFilter');

    const state = {
        chart: null,
        rawData: null
    };

    function getCurrentFilters() {
        return {
            year: yearFilter ? yearFilter.value : '',
            month: monthFilter ? monthFilter.value : ''
        };
    }

    async function loadDataAndRender() {
        const { year, month } = getCurrentFilters();
        container.classList.add('opacity-50');

        try {
            const params = new URLSearchParams();
            if (year) params.append('year', year);
            if (month) params.append('month', month);

            const res = await fetch(`/impact/api/ctp-not-good-by-machine?${params.toString()}`);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const payload = await res.json();
            if (!payload.success) throw new Error(payload.error || 'Gagal memuat data');

            state.rawData = payload.data || [];
            renderChart();
        } catch (err) {
            console.error('Error load plate NG by machine:', err);
            if (window.showToast) {
                window.showToast('Gagal memuat grafik Plate Not Good per Mesin: ' + err.message, 'danger');
            }
        } finally {
            container.classList.remove('opacity-50');
        }
    }

    function buildDatasetsFromRaw(raw) {
        const machineLabels = [];
        const reasonSet = new Set();

        raw.forEach(row => {
            const m = row.ctp_machine || 'Tidak diketahui';
            if (!machineLabels.includes(m)) machineLabels.push(m);
            Object.keys(row.reasons || {}).forEach(r => reasonSet.add(r));
        });

        // Define the fixed order of categories matching the group cards
        const fixedCategories = [
            'Plate Rontok / Botak',
            'Plate Baret',
            'Plate Penyok',
            'Plate Kotor',
            'Plate bergaris',
            'Plate tidak sesuai DP',
            'Nilai tidak sesuai',
            'Laser Jump',
            'Tidak masuk millar',
            'Error mesin Punch',
            'Plate Jump'
        ];
        
        // Filter to only include categories that exist in the data
        const reasonLabels = fixedCategories.filter(category => reasonSet.has(category));

        // Color palette matching the group cards
        const palette = [
            'rgba(255, 99, 132, 0.7)',   // Plate Rontok / Botak
            'rgba(54, 162, 235, 0.7)',   // Plate Baret
            'rgba(255, 206, 86, 0.7)',   // Plate Penyok
            'rgba(75, 192, 192, 0.7)',   // Plate Kotor
            'rgba(153, 102, 255, 0.7)',  // Plate bergaris
            'rgba(255, 159, 64, 0.7)',   // Plate tidak sesuai DP
            'rgba(205, 92, 92, 0.7)',    // Nilai tidak sesuai
            'rgba(72, 209, 204, 0.7)',   // Laser Jump
            'rgba(255, 182, 193, 0.7)',  // Tidak masuk millar
            'rgba(107, 142, 35, 0.7)',   // Error mesin Punch
            'rgba(255, 140, 0, 0.7)'     // Plate Jump
        ];
        
        // Border colors matching the group cards (more opaque versions)
        const borderColors = [
            'rgba(255, 99, 132, 1)',     // Plate Rontok / Botak
            'rgba(54, 162, 235, 1)',     // Plate Baret
            'rgba(255, 206, 86, 1)',     // Plate Penyok
            'rgba(75, 192, 192, 1)',     // Plate Kotor
            'rgba(153, 102, 255, 1)',    // Plate bergaris
            'rgba(255, 159, 64, 1)',     // Plate tidak sesuai DP
            'rgba(205, 92, 92, 1)',      // Nilai tidak sesuai
            'rgba(72, 209, 204, 1)',     // Laser Jump
            'rgba(255, 182, 193, 1)',    // Tidak masuk millar
            'rgba(107, 142, 35, 1)',     // Error mesin Punch
            'rgba(255, 140, 0, 1)'       // Plate Jump
        ];

        const datasets = reasonLabels.map((reason, idx) => {
            const data = machineLabels.map(machine => {
                const row = raw.find(r => (r.ctp_machine || 'Tidak diketahui') === machine);
                if (!row || !row.reasons) return 0;
                return row.reasons[reason] || 0;
            });

            // Find the index of this reason in the fixed categories to get the correct color
            const fixedIndex = fixedCategories.indexOf(reason);
            const colorIndex = fixedIndex !== -1 ? fixedIndex : idx;
            const baseColor = palette[colorIndex % palette.length];
            const borderColor = borderColors[colorIndex % borderColors.length];

            return {
                label: reason,
                data,
                backgroundColor: baseColor,
                borderColor: borderColor,
                borderWidth: 2,
                stack: 'stack-1',
                borderRadius: 4
            };
        });

        return { machineLabels, datasets };
    }

    function renderChart() {
        const raw = state.rawData || [];
        const canvas = ctx.getContext('2d');

        if (state.chart) {
            try { state.chart.destroy(); } catch (e) {}
            state.chart = null;
        }

        if (!raw.length) {
            const noDataEl = document.getElementById('plateNotGoodMachineNoData');
            if (noDataEl) noDataEl.classList.remove('d-none');
            return;
        }

        const { machineLabels, datasets } = buildDatasetsFromRaw(raw);
        const noDataEl = document.getElementById('plateNotGoodMachineNoData');
        if (noDataEl) noDataEl.classList.add('d-none');

        state.chart = new Chart(canvas, {
            type: 'bar',
            data: {
                labels: machineLabels,
                datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            boxWidth: 12,
                            boxHeight: 12,
                            usePointStyle: true
                        }
                    },
                    tooltip: {
                        callbacks: {
                            title: (items) => {
                                if (!items || !items.length) return '';
                                const idx = items[0].dataIndex;
                                return 'Mesin: ' + machineLabels[idx];
                            },
                            label: (ctx) => {
                                const reason = ctx.dataset.label;
                                const val = Number(ctx.raw || 0).toLocaleString('id-ID');
                                return ` ${reason}: ${val} plate`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        stacked: true,
                        ticks: {
                            autoSkip: false,
                            maxRotation: 30,
                            minRotation: 0
                        }
                    },
                    y: {
                        stacked: true,
                        beginAtZero: true,
                        ticks: {
                            precision: 0
                        }
                    }
                }
            }
        });
    }

    // Hook into existing KPI filter reloads by monkey-patching loadKpiData if available
    const originalLoadKpiData = typeof window.loadKpiData === 'function' ? window.loadKpiData : null;

    window.loadKpiData = function () {
        if (originalLoadKpiData) originalLoadKpiData();
        // Slight delay to ensure filters are applied before fetching chart data
        setTimeout(loadDataAndRender, 100);
    };

    // Also react to direct filter changes if they exist
    if (yearFilter) yearFilter.addEventListener('change', () => setTimeout(loadDataAndRender, 150));
    if (monthFilter) monthFilter.addEventListener('change', () => setTimeout(loadDataAndRender, 150));

    // Initial load
    loadDataAndRender();
});
