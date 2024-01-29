"""util function common to different scrapers"""
import os
from src.common.logger import get_logger
import requests
import shutil
from src.scraper.constants import headers
import structlog


def initialize_scraper(website_tag):
    logger = get_logger(logger_name=website_tag, log_file=f"scraper/{website_tag}")
    data_dir = os.path.join(
        os.getenv("SCRAPED_DATA_ROOT"),
        website_tag,
    )
    data_dir_recipes = os.path.join(data_dir, "recipes")
    data_dir_images = os.path.join(data_dir, "images")
    os.makedirs(data_dir_recipes, exist_ok=True)
    os.makedirs(data_dir_images, exist_ok=True)

    return logger, data_dir_recipes, data_dir_images


def save_recipe_image(source_image_url: str, local_image_url: str, logger: structlog.stdlib.BoundLogger) -> bool:
    """Save the image from source url on web to a destination local url

    Args:
        source_image_url (str): url of the source image on web
        local_image_url (str): url of the destination url

    Returns:
        bool: indicator if saving image is successful or not
    """

    if os.path.exists(local_image_url):
        return True
    try:
        r = requests.get(source_image_url, stream=True, headers=headers)
        with open(local_image_url, "wb") as f:
            r.raw.decode_content = True
            shutil.copyfileobj(r.raw, f)
        return True
    except Exception:
        logger.info(
            "Could not download recipe image",
            source_image_url=source_image_url,
            local_image_url=local_image_url,
        )
        return False
