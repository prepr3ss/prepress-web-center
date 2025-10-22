// static/js/mounting_dashboard_handler.js

document.addEventListener('DOMContentLoaded', function() {
    const yearFilter = document.getElementById('yearFilter');
    const monthFilter = document.getElementById('monthFilter');
    
    // Add "All Years" option
    yearFilter.add(new Option('Semua Tahun', ''));
    
    // Populate year filter (last 5 years)
    const currentYear = new Date().getFullYear();
    for (let year = currentYear; year >= currentYear - 4; year--) {
        const option = new Option(year, year);
        yearFilter.add(option);
    }
    
    // Add "All Months" option at the beginning of month filter
    monthFilter.innerHTML = `
        <option value="">Semua Bulan</option>
        <option value="1">Januari</option>
        <option value="2">Februari</option>
        <option value="3">Maret</option>
        <option value="4">April</option>
        <option value="5">Mei</option>
        <option value="6">Juni</option>
        <option value="7">Juli</option>
        <option value="8">Agustus</option>
        <option value="9">September</option>
        <option value="10">Oktober</option>
        <option value="11">November</option>
        <option value="12">Desember</option>
    `;
    
    async function loadMountingData() {
        const year = yearFilter.value;
        const month = monthFilter.value;
        
        // Hide no data message and clear previous data
        document.getElementById('noDataMessage').classList.add('d-none');
        document.getElementById('overallMountingContainer').classList.add('d-none');
        document.getElementById('userCards').innerHTML = '';
        
        const hasYearFilter = year !== '';
        const hasMonthFilter = month !== '';

        // Show loading state
        const cardsContainer = document.getElementById('userCards');
        cardsContainer.innerHTML = `
            <div class="col-12 text-center">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-2">Memuat data...</p>
            </div>
        `;
        
        // Reset all stats to loading state
        document.getElementById('totalAdjustment').textContent = '-';
        document.getElementById('totalFA').textContent = '-';
        document.getElementById('totalCurve').textContent = '-';
        document.getElementById('totalMinutes').textContent = '-';
        document.getElementById('avgMinutesPerJob').textContent = '-';
        
        fetch(`/get-mounting-dashboard-data?year=${year}&month=${month}`)
            .then(async response => {
                const text = await response.text();
                let json = null;
                try { json = text ? JSON.parse(text) : null; } catch(e) { json = null; }
                if (!response.ok) {
                    const msg = json && json.message ? json.message : (json && json.error ? json.error : response.statusText);
                    throw new Error(msg || 'Network response was not ok');
                }
                return json;
            })
            .then(data => {
                // Check if we have actual data
                if (!data.overall || Number(data.overall.total_adjustments) === 0) {
                    // No data for the selected period
                    document.getElementById('noDataMessage').classList.remove('d-none');
                    document.getElementById('overallMountingContainer').classList.add('d-none');
                    document.getElementById('userCards').innerHTML = '';
                    return;
                }

                // Hide no data message since we have data
                document.getElementById('noDataMessage').classList.add('d-none');
                
                // We have data, proceed with display
                document.getElementById('overallMountingContainer').classList.remove('d-none');
                updateDashboard(data);
            })
            .catch(error => {
                console.error('Error:', error);
                document.getElementById('noDataMessage').classList.remove('d-none');
                document.getElementById('overallMountingContainer').classList.add('d-none');
                document.getElementById('userCards').innerHTML = '';
            });
    }
    
    function updateDashboard(data) {
        const overall = data.overall || {};
        const totalAdjustments = Number(overall.total_adjustments) || 0;
        const totalFA = Number(overall.total_fa) || 0;
        const totalCurve = Number(overall.total_curve) || 0;
        const totalMinutes = Number(overall.total_minutes) || 0;
        const avgMinutes = Number(overall.avg_minutes_per_job) || 0;

        document.getElementById('totalAdjustment').textContent = totalAdjustments.toLocaleString();
        document.getElementById('totalFA').textContent = totalFA.toLocaleString();
        document.getElementById('totalCurve').textContent = totalCurve.toLocaleString();
        document.getElementById('totalMinutes').textContent = totalMinutes.toLocaleString();
        document.getElementById('avgMinutesPerJob').textContent = avgMinutes.toFixed(1);

        // Update user cards
        const cardsContainer = document.getElementById('userCards');
        cardsContainer.innerHTML = '';

        // Support both 'users' (old) and 'adjusters' (new) keys
        const usersList = data.users || data.adjusters || [];

        if (!usersList || usersList.length === 0) {
            document.getElementById('noDataMessage').classList.remove('d-none');
            return;
        }

        // Create KPI cards for each user
        usersList.forEach(user => {
            const uTotal = Number(user.total_adjustments) || 0;
            const uFa = Number(user.total_fa) || 0;
            const uCurve = Number(user.total_curve) || 0;
            const uMinutes = Number(user.total_minutes) || 0;
            const uAvg = Number(user.avg_minutes_per_job) || 0;

            const cardHtml = `
                <div class="col-md-6 col-lg-4 mb-4">
                    <div class="summary-5col-container">
                        <div class="card-header-clean">
                            <h5 class="mb-0">
                                <i class="fas fa-user me-2"></i>
                                ${user.name}
                            </h5>
                        </div>
                        <div class="summary-5col">
                            <div class="summary-item">
                                <div class="summary-icon icon-primary mb-2">
                                    <i class="fas fa-tasks"></i>
                                </div>
                                <div class="fw-semibold mb-2">Total Adjustment</div>
                                <span class="h4 mb-0 fw-bold">${uTotal.toLocaleString()}</span>
                                <div class="division-stats">
                                    FA: <span class="text-success">${uFa.toLocaleString()}</span>
                                    <span class="stats-divider">|</span>
                                    Curve: <span class="text-info">${uCurve.toLocaleString()}</span>
                                </div>
                            </div>
                            <div class="summary-item">
                                <div class="summary-icon icon-success mb-2">
                                    <i class="fas fa-clock"></i>
                                </div>
                                <div class="fw-semibold mb-2">Total Menit</div>
                                <span class="h4 mb-0 fw-bold">${uMinutes.toLocaleString()}</span>
                            </div>
                            <div class="summary-item">
                                <div class="summary-icon icon-info mb-2">
                                    <i class="fas fa-stopwatch"></i>
                                </div>
                                <div class="fw-semibold mb-2">Rata-rata Menit/Job</div>
                                <span class="h4 mb-0 fw-bold">${uAvg.toFixed(1)}</span>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            cardsContainer.insertAdjacentHTML('beforeend', cardHtml);
        });
    }
    
    // Event listeners
    yearFilter.addEventListener('change', loadMountingData);
    monthFilter.addEventListener('change', loadMountingData);
    
    // Initial load
    loadMountingData();
});