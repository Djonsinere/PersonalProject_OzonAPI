document.addEventListener("DOMContentLoaded", function () {
    function setupTableHandlers(tableId, selectAllId, confirmId, tableName, apiUrl) {
        const table = document.getElementById(tableId);
        if (!table) return;

        const selectAll = document.getElementById(selectAllId);
        const confirmBtn = document.getElementById(confirmId);

        function updateCheckboxes() {
            return Array.from(table.querySelectorAll('input[type="checkbox"]'));
        }

        selectAll?.addEventListener("click", function () {
            const checkboxes = updateCheckboxes();
            const allChecked = checkboxes.every(cb => cb.checked);
            checkboxes.forEach(cb => cb.checked = !allChecked);
        });

        confirmBtn?.addEventListener("click", function () {
            const checkboxes = updateCheckboxes();
            const selectedIds = checkboxes.filter(cb => cb.checked).map(cb => cb.value);

            if (selectedIds.length === 0) {
                alert(`Выберите хотя бы один элемент в таблице "${tableName}"`);
                return;
            }

            fetch(apiUrl, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCookie("csrftoken")
                },
                body: JSON.stringify({
                    selected_ids: selectedIds,
                    table_name: tableName
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    document.getElementById("urgent-table").innerHTML = data.urgent_table;
                    document.getElementById("normal-table").innerHTML = data.normal_table;
                    //alert(`Перемещено ${data.moved} товаров!`);
                } else {
                    alert(`Ошибка: ${data.error}`);
                }
            })
            .catch(error => console.error("Ошибка:", error));
        });
    }

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.startsWith(name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    setupTableHandlers("urgent-table", "select-all-urgent", "confirm-urgent", "Срочные", "/change_table/");
    setupTableHandlers("normal-table", "select-all-normal", "confirm-normal", "Плановые", "/change_table/");
});