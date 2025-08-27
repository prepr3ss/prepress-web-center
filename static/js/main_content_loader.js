// static/js/main_content_loader.js

// This file now primarily handles navigation for the main dashboard and other non-KPI CTP dynamic content.
// The KPI CTP page (/kpi-ctp) is now a full page load, not loaded dynamically into main-content-area.

async function loadContent(url, targetElementId) {
    console.log("main_content_loader.js: loadContent() called for URL:", url);
    const targetElement = document.getElementById(targetElementId);
    if (!targetElement) {
        console.error("main_content_loader.js: Target element not found:", targetElementId);
        return;
    }

    targetElement.innerHTML = `
        <div class="d-flex flex-column justify-content-center align-items-center" style="min-height: 200px;">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-3 text-muted">Memuat konten...</p>
        </div>
    `;

    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const html = await response.text();
        targetElement.innerHTML = html;

        // No need to call initializeKpiCtpForm here anymore as kpictp.html is a full page.
        // If you add other dynamic forms later, you would add their initialization here.

    } catch (error) {
        console.error("main_content_loader.js: Gagal memuat konten:", error);
        targetElement.innerHTML = `
            <div class="alert alert-danger" role="alert">
                Terjadi kesalahan saat memuat konten: ${error.message}. Silakan coba lagi.
            </div>
        `;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    console.log("main_content_loader.js: DOMContentLoaded fired.");

    // Link for Input KPI CTP (now directs to a full page)
    const inputKpiCtpLink = document.getElementById('inputKpiCtpLink');
    if (inputKpiCtpLink) {
        inputKpiCtpLink.addEventListener('click', function(event) {
            // Allow default navigation for full page load
            // event.preventDefault(); // Removed to allow full page navigation
            // No need to call loadContent here, browser will handle navigation
            console.log("Navigating to /kpi-ctp...");

            // Update active classes
            document.querySelectorAll('.sidebar .nav-link').forEach(link => link.classList.remove('active'));
            this.classList.add('active');
            const ctpSubmenuParent = document.querySelector('a[data-bs-toggle="collapse"][href="#ctpSubmenu"]');
            if (ctpSubmenuParent) ctpSubmenuParent.classList.add('active');
        });
    }

    // Link for Dashboard CTP (still loads content dynamically for the main dashboard)
    const dashboardCtpLink = document.getElementById('dashboardCtpLink');
    if (dashboardCtpLink) {
        dashboardCtpLink.addEventListener('click', function(event) {
            event.preventDefault(); // Prevent full page redirect for dynamic content

            document.getElementById('main-content-area').innerHTML = `
                <h1>Selamat Datang di Dashboard CTP Production Log</h1>
                <p class="lead">
                    Ini adalah halaman utama Anda untuk memantau Key Performance Indicator (KPI) produksi CTP. <br>
                    Gunakan menu di sebelah kiri untuk navigasi.
                </p>
                <div class="mt-4">
                    <p>Silakan pilih menu dari sidebar untuk melihat detail data atau menambahkan log baru.</p>
                </div>
            `;
            // Update active classes
            document.querySelectorAll('.sidebar .nav-link').forEach(link => link.classList.remove('active'));
            this.classList.add('active');
            const ctpSubmenuParent = document.querySelector('a[data-bs-toggle="collapse"][href="#ctpSubmenu"]');
            if (ctpSubmenuParent) ctpSubmenuParent.classList.add('active');
        });
    }
});