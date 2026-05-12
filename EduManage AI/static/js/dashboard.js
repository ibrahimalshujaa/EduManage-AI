// Dashboard functionality
document.addEventListener('DOMContentLoaded', () => {
    console.log('EduManage AI Dashboard Initialized');
});

// Utility function to format numbers
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

// Global search functionality (Real-time Filtering)
const searchInput = document.querySelector('.navbar-actions input');
if (searchInput) {
    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase();
        
        // 1. Filter Table Rows
        const rows = document.querySelectorAll('table tbody tr');
        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            row.style.display = text.includes(query) ? '' : 'none';
        });

        // 2. Filter Cards (excluding the top stats grid and search container)
        // We target cards that are children of the main-content or specifically lesson cards
        const cards = document.querySelectorAll('.main-content > .card, .main-content > div > .card, .lesson-card');
        cards.forEach(card => {
            // Don't filter cards inside stats-grid (top stats)
            if (card.closest('.stats-grid') && !card.classList.contains('lesson-card')) return;
            
            const text = card.textContent.toLowerCase();
            card.style.display = text.includes(query) ? '' : 'none';
        });
    });
}
