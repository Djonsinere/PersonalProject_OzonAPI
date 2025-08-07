
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('filterForm');
    const checkboxes = document.querySelectorAll('.cluster-checkbox');
    const regFilterInput = document.getElementById('regFilterInput');
    const urlParams = new URLSearchParams(window.location.search);
    const regFilter = urlParams.get('reg_filter');

    // восстановления состояния
    function restoreCheckboxes() {
        if (regFilter) {
            if (regFilter === 'all') {
                checkboxes.forEach(checkbox => checkbox.checked = true);
            } else {
                const selectedIds = regFilter.split(',');
                checkboxes.forEach(checkbox => {
                    checkbox.checked = selectedIds.includes(checkbox.value);
                });
            }
        } else {
            checkboxes.forEach(checkbox => checkbox.checked = true);
            regFilterInput.value = 'all';
        }
    }

    // обновления скрытого поля
    function updateRegFilter() {
        const selected = Array.from(checkboxes)
            .filter(checkbox => checkbox.checked)
            .map(checkbox => checkbox.value);
        
        regFilterInput.value = selected.length === checkboxes.length ? 'all' : selected.join(',');
    }

    restoreCheckboxes();
    updateRegFilter();
    
    // Обработчики событий
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', updateRegFilter);
    });

    form.addEventListener('submit', function(e) {
        updateRegFilter();
    });
});
