"""util function common to different scrapers"""
import os
from src.common.logger import get_logger


def initialize_scraper(website_tag):
    logger = get_logger(logger_name=website_tag, log_file=f"scraper/{website_tag}")
    data_dir = os.path.join(
        os.getenv("DATA_ROOT", os.path.join(os.getcwd(), "data")),
        "scraped_data",
        website_tag,
    )
    data_dir_recipes = os.path.join(data_dir, "recepies")
    data_dir_images = os.path.join(data_dir, "images")
    os.makedirs(data_dir_recipes, exist_ok=True)
    os.makedirs(data_dir_images, exist_ok=True)

    return logger, data_dir_recipes, data_dir_images
