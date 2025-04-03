document.addEventListener('DOMContentLoaded', function () {
    // Toggle sidebar
    const sidebarCollapse = document.getElementById('sidebarCollapse');
    if (sidebarCollapse) {
        sidebarCollapse.addEventListener('click', function () {
            const sidebar = document.getElementById('sidebar');
            const content = document.getElementById('content');
            
            sidebar.classList.toggle('active');
            content.classList.toggle('w-100');
        });
    }
    
    // Auto-dismiss des alertes après 5 secondes
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
    
    // Initialiser les tableaux avec DataTables si la page contient des tableaux
    const tables = document.querySelectorAll('.datatable');
    tables.forEach(function(table) {
        if (typeof $.fn.DataTable !== 'undefined') {
            $(table).DataTable({
                language: {
                    url: "//cdn.datatables.net/plug-ins/1.10.25/i18n/French.json"
                },
                responsive: true
            });
        }
    });
    
    // Initialisation des graphiques si nécessaire
    initCharts();
});

// Fonction pour initialiser les graphiques
function initCharts() {
    // Graphique des accès par jour
    const accessChartEl = document.getElementById('accessChart');
    if (accessChartEl) {
        const ctx = accessChartEl.getContext('2d');
        const data = JSON.parse(accessChartEl.dataset.stats);
        
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.map(item => item.date),
                datasets: [{
                    label: 'Nombre d\'accès',
                    data: data.map(item => item.count),
                    backgroundColor: 'rgba(75, 108, 183, 0.7)',
                    borderColor: 'rgba(75, 108, 183, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0
                        }
                    }
                }
            }
        });
    }
    
    // Graphique des accès réussis/échoués
    const accessPieChartEl = document.getElementById('accessPieChart');
    if (accessPieChartEl) {
        const ctx = accessPieChartEl.getContext('2d');
        const success = parseInt(accessPieChartEl.dataset.success);
        const failed = parseInt(accessPieChartEl.dataset.failed);
        
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Réussis', 'Échoués'],
                datasets: [{
                    data: [success, failed],
                    backgroundColor: [
                        'rgba(40, 167, 69, 0.7)',
                        'rgba(220, 53, 69, 0.7)'
                    ],
                    borderColor: [
                        'rgba(40, 167, 69, 1)',
                        'rgba(220, 53, 69, 1)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false
            }
        });
    }
} 