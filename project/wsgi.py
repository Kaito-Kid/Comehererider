import logging
import os
from app import create_app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = create_app(os.getenv('FLASK_ENV') or 'default')

if __name__ == "__main__":
    logger.info("Project starting...")
    app.run()
