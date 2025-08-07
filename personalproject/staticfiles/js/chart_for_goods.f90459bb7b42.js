document.addEventListener("DOMContentLoaded", function () {
    var canvas = document.getElementById("salesChart");
    var labels = JSON.parse(canvas.getAttribute("data-labels")); // Загружаем метки
    var values = JSON.parse(canvas.getAttribute("data-values")); // Загружаем значения

    var ctx = canvas.getContext("2d");
    var salesChart = new Chart(ctx, {
        type: "line",
        data: {
            labels: labels,
            datasets: [{
                label: "Продажи",
                data: values,
                backgroundColor: "rgba(54, 162, 235, 0.5)",
                backgroundColor: "rgba(54, 162, 235, 0.5)",
                borderColor: "rgba(54, 162, 235, 1)",
                borderWidth: 1,
                fill: true 
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
});