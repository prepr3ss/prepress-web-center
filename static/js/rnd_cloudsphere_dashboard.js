document.addEventListener('DOMContentLoaded', function() {
    const yearFilter = document.getElementById('filterYear');
    const monthFilter = document.getElementById('filterMonth');
    
    // Initialize filters from real database data
    initializeFiltersFromDatabase();
    
    // Add event listener for year filter change
    if (yearFilter) {
        yearFilter.addEventListener('change', function() {
            const selectedYear = this.value;
            populateMonthOptions(selectedYear);
            // Trigger data reload
            loadDashboardData();
        });
    }
    
    // Add event listener for month filter change
    if (monthFilter) {
        monthFilter.addEventListener('change', function() {
            loadDashboardData();
        });
    }

    async function initializeFiltersFromDatabase() {
        try {
            // Fetch available periods (years) from database
            const response = await fetch('/impact/rnd-cloudsphere/api/dashboard-available-periods');
            const data = await response.json();
            
            if (data.success && data.years && data.years.length > 0) {
                // Populate year filter with actual data
                populateYearOptionsFromYears(data.years);
                
                // Initialize month filter for first year
                const firstYear = data.years[0];
                yearFilter.value = firstYear; // Set first year as selected
                await populateMonthOptions(firstYear);
                
                // Load dashboard data after filters are initialized
                loadDashboardData();
            } else {
                console.warn('No years found in database');
                if (monthFilter) {
                    monthFilter.innerHTML = '<option value="">Semua Bulan</option>';
                }
                // Still load dashboard with no filters to show empty state
                loadDashboardData();
            }
        } catch (error) {
            console.error('Error initializing filters from database:', error);
            if (monthFilter) {
                monthFilter.innerHTML = '<option value="">Semua Bulan</option>';
            }
            // Still load dashboard even if filter init fails
            loadDashboardData();
        }
    }

    function populateYearOptionsFromYears(years) {
        if (yearFilter && years && years.length > 0) {
            yearFilter.innerHTML = '<option value="">Semua Tahun</option>';
            
            // Sort years in descending order (most recent first)
            const sortedYears = years.sort((a, b) => b - a);
            
            sortedYears.forEach(year => {
                const option = new Option(year, year);
                yearFilter.add(option);
            });
        }
    }

    async function populateMonthOptions(selectedYear = '') {
        try {
            if (monthFilter) {
                monthFilter.innerHTML = '<option value="">Semua Bulan</option>';
            }
            
            // If no year selected, keep empty
            if (!selectedYear) {
                return;
            }
            
            // Fetch months from database for selected year
            const response = await fetch(`/impact/rnd-cloudsphere/api/dashboard-available-months?year=${selectedYear}`);
            const data = await response.json();
            
            if (data.success && data.months && data.months.length > 0) {
                if (monthFilter) {
                    const monthNames = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'];
                    
                    data.months.forEach(month => {
                        const monthName = monthNames[month - 1] || `Bulan ${month}`;
                        const option = new Option(monthName, month);
                        monthFilter.add(option);
                    });
                }
            } else {
                console.warn(`No months found for year ${selectedYear}`);
            }
        } catch (error) {
            console.error('Error populating month options:', error);
        }
    }
    
    function loadDashboardData() {
        const year = yearFilter.value;
        const month = monthFilter.value;
        
        // Show loading states
        showLoadingStates();
        
        Promise.all([
            fetch(`/impact/rnd-cloudsphere/api/dashboard-stats?year=${year}&month=${month}`),
            fetch(`/impact/rnd-cloudsphere/api/dashboard-sla?year=${year}&month=${month}`),
            fetch(`/impact/rnd-cloudsphere/api/dashboard-performance-indicators?year=${year}&month=${month}`)
        ])
            .then(async ([resStats, resSla, resPerformance]) => {
                if (!resStats.ok) throw new Error(`HTTP error Stats! status: ${resStats.status}`);
                if (!resSla.ok) throw new Error(`HTTP error SLA! status: ${resSla.status}`);
                if (!resPerformance.ok) throw new Error(`HTTP error Performance Indicators! status: ${resPerformance.status}`);
    
                const stats = await resStats.json();
                const sla = await resSla.json();
                const performance = await resPerformance.json();
    
                if (!stats.success) throw new Error(stats.error || 'Unknown error from Stats server');
                if (!sla.success) throw new Error(sla.error || 'Unknown error from SLA server');
                if (!performance.success) throw new Error(performance.error || 'Unknown error from Performance Indicators server');
    
                // Update statistics cards
                updateStatisticsCards(stats.data, performance.data);
                
                // Update SLA chart
                updateSlaHealthChart(sla.data);
                
                // Load individual scores (default view)
                loadIndividualScores();
                
                // Don't load combined chart on initial load since scores is the default view
                
                // Hide loading states
                hideLoadingStates();
            })
            .catch(error => {
                hideLoadingStates();
                showToast('Failed to load dashboard data: ' + error.message, 'danger');
            });
    }
    
    function showLoadingStates() {
        document.getElementById('combinedChartLoading').classList.add('show');
        document.getElementById('slaLoading').classList.add('show');
        const scoresLoading = document.getElementById('scoresLoading');
        if (scoresLoading) scoresLoading.style.display = 'flex';
    }
    
    function hideLoadingStates() {
        document.getElementById('combinedChartLoading').classList.remove('show');
        document.getElementById('slaLoading').classList.remove('show');
        const scoresLoading = document.getElementById('scoresLoading');
        if (scoresLoading) scoresLoading.style.display = 'none';
    }
    
    function showScoresLoadingState() {
        const scoresLoading = document.getElementById('scoresLoading');
        if (scoresLoading) scoresLoading.style.display = 'flex';
    }
    
    function hideScoresLoadingState() {
        const scoresLoading = document.getElementById('scoresLoading');
        if (scoresLoading) scoresLoading.style.display = 'none';
    }
    
    // Chart navigation functionality
    let currentChartType = 'scores'; // Set scores as default
    let combinedChart = null;
    
    function initializeChartNavigation() {
        const chartButtons = document.querySelectorAll('.chart-nav-btn');
        const chartTitle = document.getElementById('combinedChartTitle');
        
        chartButtons.forEach(button => {
            button.addEventListener('click', function() {
                // Remove active class from all buttons
                chartButtons.forEach(btn => btn.classList.remove('active'));
                
                // Add active class to clicked button
                this.classList.add('active');
                
                // Update chart type
                currentChartType = this.getAttribute('data-chart');
                
                // Update chart title
                const titles = {
                    'trend': 'Job Trend',
                    'distribution': 'Job Distribution',
                    'pic': 'PIC Distribution',
                    'scores': 'Scores KPI'
                };
                chartTitle.textContent = titles[currentChartType] || 'Chart';
                
                // Handle different content views
                const chartContent = document.getElementById('chartContent');
                const scoresContent = document.getElementById('scoresContent');
                
                if (currentChartType === 'scores') {
                    // Show scores content, hide chart content
                    if (chartContent) chartContent.style.display = 'none';
                    if (scoresContent) scoresContent.style.display = 'block';
                    // Load individual scores when switching to scores view
                    loadIndividualScores();
                } else {
                    // Show chart content, hide scores content
                    if (chartContent) chartContent.style.display = 'block';
                    if (scoresContent) scoresContent.style.display = 'none';
                    // Reload chart data based on selected type
                    loadCombinedChart();
                }
            });
        });
    }
    
    function loadCombinedChart() {
        const year = yearFilter.value;
        const month = monthFilter.value;
        
        // Show loading state
        document.getElementById('combinedChartLoading').classList.add('show');
        
        // Determine which API to call based on chart type
        let apiUrl;
        switch(currentChartType) {
            case 'trend':
                apiUrl = `/impact/rnd-cloudsphere/api/dashboard-trend?year=${year}&month=${month}`;
                break;
            case 'distribution':
                apiUrl = `/impact/rnd-cloudsphere/api/dashboard-trend?year=${year}&month=${month}`;
                break;
            case 'pic':
                apiUrl = `/impact/rnd-cloudsphere/api/dashboard-stage-distribution?year=${year}&month=${month}`;
                break;
            default:
                apiUrl = `/impact/rnd-cloudsphere/api/dashboard-trend?year=${year}&month=${month}`;
        }
        
        fetch(apiUrl)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (!data.success) {
                    throw new Error(data.error || 'Unknown error from server');
                }
                
                // Update the combined chart based on type
                switch(currentChartType) {
                    case 'trend':
                        updateCombinedTrendChart(data.data);
                        break;
                    case 'distribution':
                        updateCombinedDistributionChart(data.data);
                        break;
                    case 'pic':
                        updateCombinedPicChart(data.data);
                        break;
                }
                
                // Hide loading state
                document.getElementById('combinedChartLoading').classList.remove('show');
            })
            .catch(error => {
                document.getElementById('combinedChartLoading').classList.remove('show');
                showToast('Failed to load chart data: ' + error.message, 'danger');
            });
    }
    
    function updateCombinedTrendChart(data) {
        const ctx = document.getElementById('combinedChart').getContext('2d');
        
        // Destroy previous chart if exists
        if (combinedChart) {
            combinedChart.destroy();
        }
        
        combinedChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels || [],
                datasets: [
                    {
                        label: 'Blank',
                        data: data.blank || [],
                        borderColor: '#1976D2',
                        backgroundColor: 'rgba(25, 118, 210, 0.1)',
                        borderWidth: 2,
                        tension: 0.25,
                        fill: true
                    },
                    {
                        label: 'RoHS ICB',
                        data: data.rohs_icb || [],
                        borderColor: '#4CAF50',
                        backgroundColor: 'rgba(76, 175, 80, 0.1)',
                        borderWidth: 2,
                        tension: 0.25,
                        fill: true
                    },
                    {
                        label: 'RoHS Ribbon',
                        data: data.rohs_ribbon || [],
                        borderColor: '#FF5722',
                        backgroundColor: 'rgba(255, 87, 34, 0.1)',
                        borderWidth: 2,
                        tension: 0.25,
                        fill: true
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        },
                        title: {
                            display: true,
                            text: 'Number of Jobs'
                        }
                    }
                }
            }
        });
    }
    
    function updateCombinedDistributionChart(data) {
        const ctx = document.getElementById('combinedChart').getContext('2d');
        
        // Destroy previous chart if exists
        if (combinedChart) {
            combinedChart.destroy();
        }
        
        combinedChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.labels || [],
                datasets: [
                    {
                        label: 'Blank',
                        data: data.blank || [],
                        backgroundColor: '#1976D2',
                        borderColor: '#1976D2',
                        borderWidth: 1
                    },
                    {
                        label: 'RoHS ICB',
                        data: data.rohs_icb || [],
                        backgroundColor: '#4CAF50',
                        borderColor: '#4CAF50',
                        borderWidth: 1
                    },
                    {
                        label: 'RoHS Ribbon',
                        data: data.rohs_ribbon || [],
                        backgroundColor: '#FF5722',
                        borderColor: '#FF5722',
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                },
                scales: {
                    x: {
                        stacked: true
                    },
                    y: {
                        stacked: true,
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        },
                        title: {
                            display: true,
                            text: 'Number of Jobs'
                        }
                    }
                }
            }
        });
    }
    
    function updateCombinedPicChart(data) {
        const ctx = document.getElementById('combinedChart').getContext('2d');
        
        // Destroy previous chart if exists
        if (combinedChart) {
            combinedChart.destroy();
        }
        
        // Extract data for pie chart
        const labels = data.map(item => item.pic_name);
        const values = data.map(item => item.count);
        
        combinedChart = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: labels || [],
                datasets: [{
                    data: values || [],
                    backgroundColor: [
                        '#667eea',
                        '#764ba2',
                        '#f093fb',
                        '#4facfe',
                        '#56ab2f',
                        '#fa709a',
                        '#9C27B0',
                        '#795548',
                        '#2196F3'
                    ],
                    borderColor: '#ffffff',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.raw || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(1);
                                return `${label}: ${value} jobs (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    }
    
    function updateStatisticsCards(statsData, performanceData) {
        // Job Statistics
        const totalJobs = (statsData.blank_jobs || 0) + (statsData.rohs_icb_jobs || 0) + (statsData.rohs_ribbon_jobs || 0);
        document.getElementById('totalJobsValue').textContent = totalJobs;
        document.getElementById('blankJobsValue').textContent = statsData.blank_jobs || 0;
        document.getElementById('rohsIcbValue').textContent = statsData.rohs_icb_jobs || 0;
        document.getElementById('rohsRibbonValue').textContent = statsData.rohs_ribbon_jobs || 0;
        
        // Performance Statistics
        document.getElementById('completedJobsValue').textContent = statsData.completed_jobs || 0;
        document.getElementById('overdueJobsValue').textContent = statsData.overdue_jobs || 0;
        
        // Performance Indicators (average completion time in days) - only show the three required indicators
        document.getElementById('avgBlankValue').textContent = (performanceData.avg_blank_time || 0) + ' hari';
        document.getElementById('avgRohsIcbValue').textContent = (performanceData.avg_rohs_icb_time || 0) + ' hari';
        document.getElementById('avgRohsRibbonValue').textContent = (performanceData.avg_rohs_ribbon_time || 0) + ' hari';
    }
    
    // Chart instances
    let jobTrendChart = null;
    let jobDistributionChart = null;
    let picDistributionChart = null;
    let slaHealthChart = null;
    
    function updateJobTrendChart(data) {
        const ctx = document.getElementById('jobTrendChart').getContext('2d');
        
        // Destroy previous chart if exists
        if (jobTrendChart) {
            jobTrendChart.destroy();
        }
        
        jobTrendChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels || [],
                datasets: [
                    {
                        label: 'Blank',
                        data: data.blank || [],
                        borderColor: '#1976D2',
                        backgroundColor: 'rgba(25, 118, 210, 0.1)',
                        borderWidth: 2,
                        tension: 0.25,
                        fill: true
                    },
                    {
                        label: 'RoHS ICB',
                        data: data.rohs_icb || [],
                        borderColor: '#4CAF50',
                        backgroundColor: 'rgba(76, 175, 80, 0.1)',
                        borderWidth: 2,
                        tension: 0.25,
                        fill: true
                    },
                    {
                        label: 'RoHS Ribbon',
                        data: data.rohs_ribbon || [],
                        borderColor: '#FF5722',
                        backgroundColor: 'rgba(255, 87, 34, 0.1)',
                        borderWidth: 2,
                        tension: 0.25,
                        fill: true
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        },
                        title: {
                            display: true,
                            text: 'Number of Jobs'
                        }
                    }
                }
            }
        });
    }
    
    function updateJobDistributionChart(data) {
        const ctx = document.getElementById('jobDistributionChart').getContext('2d');
        
        // Destroy previous chart if exists
        if (jobDistributionChart) {
            jobDistributionChart.destroy();
        }
        
        jobDistributionChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.labels || [],
                datasets: [
                    {
                        label: 'Blank',
                        data: data.blank || [],
                        backgroundColor: '#1976D2',
                        borderColor: '#1976D2',
                        borderWidth: 1
                    },
                    {
                        label: 'RoHS ICB',
                        data: data.rohs_icb || [],
                        backgroundColor: '#4CAF50',
                        borderColor: '#4CAF50',
                        borderWidth: 1
                    },
                    {
                        label: 'RoHS Ribbon',
                        data: data.rohs_ribbon || [],
                        backgroundColor: '#FF5722',
                        borderColor: '#FF5722',
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                },
                scales: {
                    x: {
                        stacked: true
                    },
                    y: {
                        stacked: true,
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        },
                        title: {
                            display: true,
                            text: 'Number of Jobs'
                        }
                    }
                }
            }
        });
    }
    
    function updatePicDistributionChart(data) {
        const ctx = document.getElementById('picDistributionChart').getContext('2d');
        
        // Destroy previous chart if exists
        if (picDistributionChart) {
            picDistributionChart.destroy();
        }
        
        // Extract data for pie chart
        const labels = data.map(item => item.pic_name);
        const values = data.map(item => item.count);
        
        picDistributionChart = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: labels || [],
                datasets: [{
                    data: values || [],
                    backgroundColor: [
                        '#667eea',
                        '#764ba2',
                        '#f093fb',
                        '#4facfe',
                        '#56ab2f',
                        '#fa709a',
                        '#9C27B0',
                        '#795548',
                        '#2196F3'
                    ],
                    borderColor: '#ffffff',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.raw || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(1);
                                return `${label}: ${value} jobs (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    }
    
    function updateSlaHealthChart(data) {
        const ctx = document.getElementById('slaHealthChart').getContext('2d');
        
        // Destroy previous chart if exists
        if (slaHealthChart) {
            slaHealthChart.destroy();
        }
        
        const onTimePercentage = data.on_time_pct || 0;
        const overduePercentage = 100 - onTimePercentage;
        
        slaHealthChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['On Time', 'Overdue'],
                datasets: [{
                    data: [onTimePercentage, overduePercentage],
                    backgroundColor: ['#56ab2f', '#fa709a'],
                    borderColor: '#ffffff',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.raw || 0;
                                return `${label}: ${value.toFixed(1)}%`;
                            }
                        }
                    }
                }
            }
        });
        
        // Update chart title to show percentage
        const chartTitle = document.querySelector('#slaHealthChart').closest('.chart-container-wrapper').querySelector('.chart-title');
        if (chartTitle) {
            chartTitle.textContent = `SLA Health (${onTimePercentage.toFixed(1)}% on-time)`;
        }
    }
    
    // Load Individual Scores
    async function loadIndividualScores() {
        try {
            const scoresLoading = document.getElementById('scoresLoading');
            const scoresContainer = document.getElementById('scoresContainer');
            
            if (!scoresContainer) return;
            
            // Show loading
            showScoresLoadingState();
            
            // Get filter values
            const year = yearFilter.value || null;
            const month = monthFilter.value || null;
            
            // Build URL with parameters
            let url = '/impact/rnd-cloudsphere/api/dashboard-individual-scores';
            const params = new URLSearchParams();
            if (year) params.append('year', year);
            if (month) params.append('month', month);
            if (params.toString()) url += '?' + params.toString();
            
            const response = await fetch(url);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success && data.data && Array.isArray(data.data)) {
                displayIndividualScores(data.data);
            } else {
                scoresContainer.innerHTML = '<p class="text-muted">Tidak ada data scores tersedia</p>';
            }
        } catch (error) {
            console.error('Error loading individual scores:', error);
            const scoresContainer = document.getElementById('scoresContainer');
            if (scoresContainer) {
                scoresContainer.innerHTML = '<p class="text-danger">Gagal memuat data scores</p>';
            }
        } finally {
            hideScoresLoadingState();
        }
    }
    
    function displayIndividualScores(usersData) {
        const scoresContainer = document.getElementById('scoresContainer');
        if (!scoresContainer) return;
        
        scoresContainer.innerHTML = '';
        
        if (!usersData || usersData.length === 0) {
            scoresContainer.innerHTML = '<p class="text-muted">Tidak ada data scores tersedia</p>';
            return;
        }
        
        // Stage order for display
        const stageOrder = ['Design', 'Mastercard', 'Blank', 'RoHS ICB', 'RoHS Ribbon', 'Polymer Ribbon', 'Light-Standard-Dark'];
        
        // Create card for each user
        usersData.forEach(user => {
            const scoreCard = document.createElement('div');
            scoreCard.className = 'score-card';
            
            // Header with user info
            const header = document.createElement('div');
            header.className = 'score-card-header';
            header.innerHTML = `
                <div class="score-card-username">${user.user_name}</div>
                <div class="score-card-userid">@${user.username}</div>
            `;
            scoreCard.appendChild(header);
            
            // Score items
            const scoresDiv = document.createElement('div');
            scoresDiv.className = 'score-items';
            
            stageOrder.forEach(stage => {
                let scoreValue = user.scores[stage] || 0;
                // Convert days to hours for Design stage
                if (stage === 'Design') {
                    scoreValue = scoreValue * 24;
                }
                const scoreItem = document.createElement('div');
                scoreItem.className = 'score-item';
                // Use 'jam' (hours) for Design, 'hari' (days) for others
                const unit = stage === 'Design' ? 'jam' : 'hari';
                scoreItem.innerHTML = `
                    <div class="score-item-label">${stage}</div>
                    <div>
                        <span class="score-item-value">${scoreValue.toFixed(2)}</span>
                        <span class="score-item-unit">${unit}</span>
                    </div>
                `;
                scoresDiv.appendChild(scoreItem);
            });
            
            scoreCard.appendChild(scoresDiv);
            scoresContainer.appendChild(scoreCard);
        });
    }
    
    // Event listeners
    if (yearFilter) yearFilter.addEventListener('change', loadDashboardData);
    if (monthFilter) monthFilter.addEventListener('change', loadDashboardData);
    
    // Initialize chart navigation
    initializeChartNavigation();
    
    // Load individual scores on page load since it's the default view
    loadIndividualScores();
    
    // Global toast function
    window.showToast = function(message, type = 'success') {
        const toastContainer = document.createElement('div');
        toastContainer.style.position = 'fixed';
        toastContainer.style.top = '1rem';
        toastContainer.style.right = '1rem';
        toastContainer.style.zIndex = '1050';
        
        toastContainer.innerHTML = `
            <div class="toast align-items-center text-white bg-${type} border-0" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="d-flex">
                    <div class="toast-body">
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
            </div>
        `;
        
        document.body.appendChild(toastContainer);
        const toast = new bootstrap.Toast(toastContainer.querySelector('.toast'));
        toast.show();
        
        // Remove the toast after it's hidden
        toastContainer.querySelector('.toast').addEventListener('hidden.bs.toast', () => {
            toastContainer.remove();
        });
    };
});
