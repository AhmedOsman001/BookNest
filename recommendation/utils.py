import os
import sys
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

def ensure_recommendation_engine_in_path():
    """
    Make sure the recommendation_engine module is in the Python path
    This allows importing the module from anywhere in the Django project
    """
    # Path to the recommendation engine module
    engine_path = os.path.join(settings.BASE_DIR, 'recommendation', 'engine')
    
    if not os.path.exists(engine_path):
        # Create the directory if it doesn't exist
        os.makedirs(engine_path, exist_ok=True)
        
    # Add to Python path if not already there
    if engine_path not in sys.path:
        sys.path.append(engine_path)
        
    logger.info(f"Added recommendation engine path to sys.path: {engine_path}")


def save_recommendation_engine_code():
    """
    Save the recommendation engine code to a file in the Django project.
    This allows using the recommendation engine without external dependencies.
    """
    engine_path = os.path.join(settings.BASE_DIR, 'recommendation', 'engine')
    engine_file = os.path.join(engine_path, 'recommendation_engine.py')
    
    if not os.path.exists(engine_path):
        os.makedirs(engine_path, exist_ok=True)
    
    # The content from the recommendation_engine.py would be placed here
    # This would be a long string with the entire code
    
    # Write the engine code to file if it doesn't exist
    # if not os.path.exists(engine_file):
    #     with open(engine_file, 'w') as f:
    #         f.write(get_recommendation_engine_code())
    #     logger.info(f"Recommendation engine code saved to {engine_file}")


