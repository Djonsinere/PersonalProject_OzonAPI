document.addEventListener('submit', function(event) {
    const overlay = document.getElementById('global-loading-overlay');
    if (overlay) {
        overlay.style.display = 'flex';  
    }
});

window.addEventListener('load', function() {
    const overlay = document.getElementById('global-loading-overlay');
    if (overlay) {
        overlay.style.display = 'none';
    }
});