import logging
from celery import shared_task
from .ozon_api.update_data_api import OzonAPI
from django.contrib.auth import get_user_model
from .models import UserProfile

logger = logging.getLogger(__name__)

@shared_task
def update_ozon_data():
    """Фоновое обновление данных из Ozon API для всех пользователей с профилем"""
    logger.info("Запуск обновления данных из Ozon API")
    
    User = get_user_model()
    
    # Оптимизация: выбираем пользователей с предзагруженным профилем
    users = User.objects.filter(profile__isnull=False).prefetch_related('profile')

    for user in users:
        try:
            # Проверяем наличие профиля (двойная проверка для безопасности)
            if not hasattr(user, 'profile'):
                logger.warning(f"Пропуск пользователя {user.username} - профиль отсутствует")
                continue

            # Передаем профиль вместо пользователя
            api = OzonAPI(user.profile)
            api.update_all_data()
            logger.info(f"Обновление завершено для пользователя: {user.username}")

        except Exception as e:
            logger.error(f"Ошибка при обновлении данных для {user.username}: {str(e)}", exc_info=True)

    logger.info("Обновление данных завершено")

@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=3, max_retries=3)
def initial_data_update(self, user_id):
    try:
        profile = UserProfile.objects.get(user__id=user_id)
        logger.info(f"Starting initial data update for user {user_id}")
        
        ozon_api = OzonAPI(profile)
        
        # Первичное обновление данных
        ozon_api.update_all_data()
        ozon_api.update_attributes_for_existing()
        
        # Помечаем профиль как инициализированный
        profile.data_initialized = True
        profile.save()
        
        logger.info(f"Successfully initialized data for user {user_id}")
        return True
    
    except Exception as e:
        logger.error(f"Initial data update failed for {user_id}: {str(e)}", exc_info=True)
        profile.data_initialized = False
        profile.save()
        raise self.retry(exc=e)