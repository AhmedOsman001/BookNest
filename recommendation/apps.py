from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _
import logging


class RecommendationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'recommendation'
    verbose_name = _('Book Recommendation')

    def ready(self):
        """
        Setup code that runs when Django starts
        """
        logger = logging.getLogger(__name__)
        logger.info("RecommendationsConfig ready method called.")
        import recommendation.signals

