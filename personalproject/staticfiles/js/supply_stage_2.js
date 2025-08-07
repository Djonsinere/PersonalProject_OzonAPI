

  // Подтверждение удаления поставки
  const deleteButtons = document.querySelectorAll('.btn-delete-shipment');
  deleteButtons.forEach(btn => {
    btn.addEventListener('click', function(e) {
      if (!confirm('Вы действительно хотите удалить эту поставку?')) {
        e.preventDefault();
      } else {
        alert('Поставка удалена (пример).');
      }
    });
  });