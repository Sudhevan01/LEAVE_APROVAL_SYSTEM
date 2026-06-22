/* ============================================
   HRMS Leave Management System - Main JavaScript
   ============================================ */

document.addEventListener('DOMContentLoaded', function () {

    // ── Dark Mode Toggle ──
    initTheme();

    // ── Sidebar Toggle (mobile) ──
    initSidebar();

    // ── Table Search ──
    initTableSearch();

    // ── Fade-in Animations ──
    initAnimations();

    // ── Auto-dismiss alerts ──
    initAlerts();
});


/* ── Theme / Dark Mode ── */

function initTheme() {
    const saved = localStorage.getItem('hrms-theme');
    if (saved) {
        document.documentElement.setAttribute('data-theme', saved);
    }

    const toggle = document.getElementById('themeToggle');
    if (!toggle) return;

    toggle.checked = (document.documentElement.getAttribute('data-theme') === 'dark');

    toggle.addEventListener('change', function () {
        const theme = this.checked ? 'dark' : 'light';
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('hrms-theme', theme);
        updateChartsTheme();
    });
}


/* ── Sidebar ── */

function initSidebar() {
    const toggleBtn = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');

    if (!toggleBtn || !sidebar) return;

    toggleBtn.addEventListener('click', function () {
        sidebar.classList.toggle('show');
        if (overlay) overlay.classList.toggle('show');
    });

    if (overlay) {
        overlay.addEventListener('click', function () {
            sidebar.classList.remove('show');
            overlay.classList.remove('show');
        });
    }
}


/* ── Table Search / Filter ── */

function initTableSearch() {
    const searchInput = document.getElementById('tableSearch');
    if (!searchInput) return;

    searchInput.addEventListener('input', function () {
        const query = this.value.toLowerCase();
        const rows = document.querySelectorAll('.table-modern tbody tr');

        rows.forEach(function (row) {
            const text = row.textContent.toLowerCase();
            row.style.display = text.includes(query) ? '' : 'none';
        });

        updateEmptyState(rows);
    });
}

function updateEmptyState(rows) {
    const table = document.querySelector('.table-modern');
    if (!table) return;

    const visibleRows = Array.from(rows).filter(function (r) { return r.style.display !== 'none'; });
    let emptyMsg = table.parentElement.querySelector('.search-empty');

    if (visibleRows.length === 0) {
        if (!emptyMsg) {
            emptyMsg = document.createElement('div');
            emptyMsg.className = 'search-empty empty-state';
            emptyMsg.innerHTML = '<i class="bi bi-search"></i><h5>No results found</h5><p>Try a different search term</p>';
            table.parentElement.appendChild(emptyMsg);
        }
        emptyMsg.style.display = '';
    } else if (emptyMsg) {
        emptyMsg.style.display = 'none';
    }
}


/* ── Animations ── */

function initAnimations() {
    const cards = document.querySelectorAll('.animate-in');
    cards.forEach(function (card, i) {
        card.style.opacity = '0';
        card.style.transform = 'translateY(12px)';
        setTimeout(function () {
            card.style.transition = 'all 0.4s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, i * 60);
    });
}


/* ── Alerts auto-dismiss ── */

function initAlerts() {
    const alerts = document.querySelectorAll('.alert-hrms');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            alert.style.transition = 'opacity 0.3s ease';
            alert.style.opacity = '0';
            setTimeout(function () { alert.remove(); }, 300);
        }, 5000);
    });
}


/* ── Chart.js Helpers ── */

function getChartColors() {
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    return {
        textColor: isDark ? '#E8C4C4' : '#5C3A46',
        gridColor: isDark ? 'rgba(255,255,255,0.06)' : 'rgba(45,10,22,0.06)',
        pending: { bg: 'rgba(245, 166, 35, 0.75)', border: '#F5A623' },
        approved: { bg: 'rgba(46, 204, 113, 0.75)', border: '#2ECC71' },
        rejected: { bg: 'rgba(237, 24, 72, 0.75)', border: '#ED1848' },
    };
}

function getChartDefaults() {
    var colors = getChartColors();
    return {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
            legend: {
                labels: {
                    color: colors.textColor,
                    font: { family: "'Inter', sans-serif", size: 12, weight: 500 },
                    padding: 16,
                    usePointStyle: true,
                    pointStyleWidth: 10,
                }
            }
        },
        scales: {
            x: {
                ticks: { color: colors.textColor, font: { size: 11 } },
                grid: { color: colors.gridColor }
            },
            y: {
                beginAtZero: true,
                ticks: { color: colors.textColor, font: { size: 11 }, stepSize: 1 },
                grid: { color: colors.gridColor }
            }
        }
    };
}

var chartInstances = [];

function registerChart(chart) {
    chartInstances.push(chart);
}

function updateChartsTheme() {
    var colors = getChartColors();
    chartInstances.forEach(function (chart) {
        if (chart.options.scales && chart.options.scales.x) {
            chart.options.scales.x.ticks.color = colors.textColor;
            chart.options.scales.x.grid.color = colors.gridColor;
        }
        if (chart.options.scales && chart.options.scales.y) {
            chart.options.scales.y.ticks.color = colors.textColor;
            chart.options.scales.y.grid.color = colors.gridColor;
        }
        if (chart.options.plugins && chart.options.plugins.legend) {
            chart.options.plugins.legend.labels.color = colors.textColor;
        }
        chart.update();
    });
}


/* ── Calendar Navigation ── */

function navigateCalendar(direction) {
    var currentMonth = parseInt(document.getElementById('calendarMonth').value);
    var currentYear = parseInt(document.getElementById('calendarYear').value);

    if (direction === 'prev') {
        currentMonth--;
        if (currentMonth < 1) { currentMonth = 12; currentYear--; }
    } else {
        currentMonth++;
        if (currentMonth > 12) { currentMonth = 1; currentYear++; }
    }

    window.location.href = '?month=' + currentMonth + '&year=' + currentYear;
}


/* ── Client-side Pagination ── */

function initPagination(tableId, rowsPerPage) {
    rowsPerPage = rowsPerPage || 10;
    var table = document.getElementById(tableId);
    if (!table) return;

    var tbody = table.querySelector('tbody');
    var rows = Array.from(tbody.querySelectorAll('tr'));
    var totalPages = Math.ceil(rows.length / rowsPerPage);
    var currentPage = 1;

    function showPage(page) {
        currentPage = page;
        rows.forEach(function (row, i) {
            row.style.display = (i >= (page - 1) * rowsPerPage && i < page * rowsPerPage) ? '' : 'none';
        });
        renderPaginationControls();
    }

    function renderPaginationControls() {
        var container = document.getElementById(tableId + 'Pagination');
        if (!container) return;
        container.innerHTML = '';

        if (totalPages <= 1) return;

        var prevBtn = createPageBtn('<i class="bi bi-chevron-left"></i>', currentPage > 1, function () { showPage(currentPage - 1); });
        container.appendChild(prevBtn);

        for (var i = 1; i <= totalPages; i++) {
            (function (page) {
                var btn = createPageBtn(page, true, function () { showPage(page); });
                if (page === currentPage) btn.classList.add('active');
                container.appendChild(btn);
            })(i);
        }

        var nextBtn = createPageBtn('<i class="bi bi-chevron-right"></i>', currentPage < totalPages, function () { showPage(currentPage + 1); });
        container.appendChild(nextBtn);
    }

    function createPageBtn(html, enabled, onClick) {
        var btn = document.createElement('button');
        btn.className = 'page-btn';
        btn.innerHTML = html;
        btn.disabled = !enabled;
        if (!enabled) btn.style.opacity = '0.4';
        if (enabled) btn.addEventListener('click', onClick);
        return btn;
    }

    if (rows.length > 0) showPage(1);
}
