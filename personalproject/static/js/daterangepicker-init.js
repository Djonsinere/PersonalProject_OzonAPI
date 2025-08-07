document.addEventListener('DOMContentLoaded', function() {
    const startDate = $('#startDate').val();
    const endDate = $('#endDate').val();

    // Настройки локализации
    const localeSettings = {
        format: 'DD.MM.YYYY',
        cancelLabel: 'Отмена',
        applyLabel: 'Применить',
        daysOfWeek: ['Вс', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб'],
        monthNames: [
            'Январь', 'Февраль', 'Март', 'Апрель',
            'Май', 'Июнь', 'Июль', 'Август',
            'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
        ],
        firstDay: 1
    };

    // Инициализация datepicker с начальными значениями
    $('#date-range').daterangepicker({
        showCustomRangeLabel: false,
        opens: 'left',
        locale: localeSettings,
        linkedCalendars: false,
        alwaysShowCalendars: true,
        autoUpdateInput: true, // Должно автоматически обновлять поле
        startDate: startDate ? moment(startDate, 'YYYY-MM-DD') : moment().subtract(45, 'days'),
        endDate: endDate ? moment(endDate, 'YYYY-MM-DD') : moment()
    });

    // Обновление скрытых полей при выборе даты
    $('#date-range').on('apply.daterangepicker', function(ev, picker) {
        $(this).val(picker.startDate.format('DD.MM.YYYY') + ' - ' + picker.endDate.format('DD.MM.YYYY'));
        $('#startDate').val(picker.startDate.format('YYYY-MM-DD'));
        $('#endDate').val(picker.endDate.format('YYYY-MM-DD'));
    });

    // Если даты загружены – обновить отображение
    if (startDate && endDate) {
        $('#date-range').val(moment(startDate, 'YYYY-MM-DD').format('DD.MM.YYYY') + ' - ' + moment(endDate, 'YYYY-MM-DD').format('DD.MM.YYYY'));
    }
});
