from bs4 import BeautifulSoup
import requests
import time
import json
import os
from typing import List, Tuple, Dict
import uuid
from src.common.utils import clean_string
from src.scraper.constants import headers
from src.scraper.utils import initialize_scraper, save_recipe_image


website_tag = "vegrecipesofindia"
BASE_WEBSITE_URL = "https://www.vegrecipesofindia.com"
LOGGER, DATA_DIR_RECIPES, DATA_DIR_IMAGES = initialize_scraper(website_tag)


def get_recipe_links_on_single_page(x: int) -> Tuple[str, List[str]]:
    """Get links of all the recipes on a single page

    Args:
        x (int): Page number to access

    Returns:
        Tuple[str, List[str]]:: Tupe of parent url and list of recepie urls listed on the parent url
    """

    # page url to to scrape different recepie urls
    url = BASE_WEBSITE_URL + f"/recipes/?fwp_paged={x}"
    r = requests.get(url, headers=headers)

    recipe_urls = []

    if r.status_code == 200:
        soup = BeautifulSoup(r.content, features="lxml")

        dishes = soup.find_all("article", class_="post-summary primary")

        for dish in dishes:
            recipe = dish.find("a", class_="post-summary__image")["href"]
            recipe_urls.append(recipe)

    return url, recipe_urls


def get_recipe_name(recipe_details: BeautifulSoup, recipe_url: str) -> str:
    """Get the recipe name"""
    try:
        name = clean_string(recipe_details.find("h2", class_="wprm-recipe-name wprm-block-text-normal").text)
    except Exception as e:
        LOGGER.error("Could not find recipe name", recipe_url=recipe_url)
        raise e
    return name


def get_recipe_description(recipe_details: BeautifulSoup, recipe_url: str) -> str:
    """Get the recipe description"""
    try:
        desciption = clean_string(recipe_details.find("div", class_="wprm-recipe-summary wprm-block-text-normal").text)
    except Exception as e:
        LOGGER.error("Could not find recipe description", recipe_url=recipe_url)
        raise e
    return desciption


def get_recipe_ingredient_list(recipe_details: BeautifulSoup, recipe_url: str) -> List[str]:
    """Get the list of ingredients"""
    try:
        ingredients = [
            clean_string(item.text) for item in recipe_details.find_all(class_="wprm-recipe-ingredient-name")
        ]
    except Exception as e:
        LOGGER.error("Could not find recipe ingredient list", recipe_url=recipe_url)
        raise e
    return ingredients


def get_recipe_cooking_steps(recipe_details: BeautifulSoup, recipe_url: str) -> Dict[str, List[str]]:
    """Get the recipe description"""
    parsed_recipe_steps = {}
    try:
        recipe_steps_groups = recipe_details.find_all("div", class_="wprm-recipe-instruction-group")
        for idx, recipe_steps_group in enumerate(recipe_steps_groups):
            try:
                key = clean_string(recipe_steps_group.find(class_="wprm-recipe-instruction-group-name").text)
            except AttributeError:
                key = f"group_{idx}"

            value = [
                clean_string(item.text) for item in recipe_steps_group.find_all("li", class_="wprm-recipe-instruction")
            ]
            parsed_recipe_steps[key] = value

    except Exception as e:
        LOGGER.info("Could not find ingredient quantities", recipe_url=recipe_url)
        raise e
    return parsed_recipe_steps


def get_recipe_cusine(recipe_details: BeautifulSoup, recipe_url: str) -> str:
    """Get the recipe cusine"""
    try:
        cusine = clean_string(recipe_details.find("span", class_="wprm-recipe-cuisine wprm-block-text-bold").text)
    except Exception:
        LOGGER.info("Could not find recipe cusine", recipe_url=recipe_url)
        cusine = ""
    return cusine


def get_recipe_diet(recipe_details: BeautifulSoup, recipe_url: str) -> str:
    """Get the recipe diet, e.g., veg, vegan etc"""
    try:
        diet = clean_string(recipe_details.find("span", class_="wprm-recipe-suitablefordiet wprm-block-text-bold").text)
    except Exception:
        LOGGER.info("Could not find recipe diet", recipe_url=recipe_url)
        diet = ""
    return diet


def get_recipe_servings(recipe_details: BeautifulSoup, recipe_url: str) -> str:
    "Get the number of servings based on which the ingredients are marked"
    try:
        servings = clean_string(recipe_details.find(class_="wprm-recipe-servings").text)
    except Exception:
        LOGGER.info("Could not find number of servigs", recipe_url=recipe_url)
        servings = ""
    return servings


def get_recipe_cooking_difficulty(recipe_details: BeautifulSoup, recipe_url: str) -> str:
    """Difficulty level in cooking"""
    try:
        difficulty = clean_string(
            recipe_details.find("div", class_="wprm-recipe-difficulty-container")
            .find("span", class_="wprm-recipe-difficulty")
            .text
        )
    except Exception:
        LOGGER.info("Could not find cooking difficulty", recipe_url=recipe_url)
        difficulty = ""
    return difficulty


def get_recipe_cooking_time(recipe_details: BeautifulSoup, recipe_url: str) -> str:
    """Total time estimate for cooking"""
    try:
        total_time = clean_string(
            recipe_details.find("div", class_="wprm-recipe-total-time-container")
            .find("span", class_="wprm-recipe-total_time")
            .text
        )
    except Exception:
        LOGGER.info("Could not find total cooking time", recipe_url=recipe_url)
        total_time = ""
    return total_time


def get_recipe_ingredient_quantities(recipe_details: BeautifulSoup, recipe_url: str) -> Dict[str, List[str]]:
    """Detailed quantity of ingredients"""
    parsed_ingredients = {}
    try:
        ingredient_groups = recipe_details.find_all("div", class_="wprm-recipe-ingredient-group")

        for idx, ingredient_group in enumerate(ingredient_groups):
            try:
                key = clean_string(ingredient_group.find(class_="wprm-recipe-ingredient-group-name").text)
            except AttributeError:
                key = f"group_{idx}"

            value = [
                clean_string(item.text) for item in ingredient_group.find_all("li", class_="wprm-recipe-ingredient")
            ]
            parsed_ingredients[key] = value

    except Exception:
        LOGGER.info("Could not find ingredient quantities", recipe_url=recipe_url)
    return parsed_ingredients


def get_image_url(recipe_details: BeautifulSoup, recipe_url: str) -> str:
    "Url of a image showing the dish"
    try:
        source_image_url = recipe_details.find("div", class_="entry-content").find("img")
        source_image_url = source_image_url.get(
            "data-lazy-src",
            source_image_url.get("data-pin-media", source_image_url.get("src")),
        )
    except Exception:
        LOGGER.info("Could not find image_url", recipe_url=recipe_url)
        source_image_url = ""
    return source_image_url


def fetch_recipe_details(recipe_url: str, recipe_id: str) -> bool:
    """Fetch details of each recipe

    Args:
        recipe_url (str): url rom which the recipe is downloaded.
        recipe_id (str): unique identifier for the recipe.

    Returns:
        bool, represents if the call is successful or not.
    """
    r = requests.get(recipe_url, headers=headers)

    try:
        recipe_details = BeautifulSoup(r.content, features="lxml")

        # Get the recipe name
        name = get_recipe_name(recipe_details, recipe_url)

        # Get the recipe description
        description = get_recipe_description(recipe_details, recipe_url)

        # Detailed cooking steps
        parsed_recipe_steps = get_recipe_cooking_steps(recipe_details, recipe_url)

        # Get the recipe ingredients
        ingredients = get_recipe_ingredient_list(recipe_details, recipe_url)

        # Get the recipe cusine
        cusine = get_recipe_cusine(recipe_details, recipe_url)

        # Get the recipe diet, e.g., veg, vegan etc
        diet = get_recipe_diet(recipe_details, recipe_url)

        # Get the number of servings based on which the ingredients are marked
        servings = get_recipe_servings(recipe_details, recipe_url)

        # Difficulty level in cooking
        difficulty = get_recipe_cooking_difficulty(recipe_details, recipe_url)

        # Total time estimate for cooking
        total_time = get_recipe_cooking_time(recipe_details, recipe_url)

        # Detailed quantity of ingredients
        parsed_ingredients = get_recipe_ingredient_quantities(recipe_details, recipe_url)

        # Url of the image
        source_image_url = get_image_url(recipe_details, recipe_url)

        # Download the image to local .,
        local_image_url = os.path.join(DATA_DIR_IMAGES, f"{recipe_id}.jpg")
        image_download_status = save_recipe_image(
            source_image_url=source_image_url,
            local_image_url=local_image_url,
            logger=LOGGER,
        )

        # Create json blob to save the recipe data
        recipe = {
            "recipe_id": recipe_id,
            "name": name,
            "description": description,
            "ingredients": ingredients,
            "cusine": cusine,
            "diet": diet,
            "servings": servings,
            "difficulty": difficulty,
            "total_time": total_time,
            "ingredient_quantity": parsed_ingredients,
            "recipe_steps": parsed_recipe_steps,
            "source_image_url": source_image_url,
            "source_recipe_url": recipe_url,
            "image_avalable": image_download_status,
        }

        with open(os.path.join(DATA_DIR_RECIPES, f"{recipe_id}.json"), "w") as outfile:
            json.dump(recipe, outfile)

        return True

    except Exception:
        LOGGER.info("Could not process a recipe url", recipe_url=recipe_url)

        return False


def run_scraper():
    """Main function to run the scraper."""
    page_number = 0
    url, recipe_urls = get_recipe_links_on_single_page(page_number)
    total_calls = 0
    successful_calls = 0
    LOGGER.info("Starting scraping.")
    while len(recipe_urls) > 0:
        for recipe_url in recipe_urls:
            recipe_id = str(
                uuid.uuid5(
                    uuid.NAMESPACE_DNS,
                    name=recipe_url.strip("https://").strip("http://").strip("www."),
                )
            )
            if not os.path.exists(os.path.join(DATA_DIR_RECIPES, f"{recipe_id}.json")):
                total_calls += 1
                successful_calls += fetch_recipe_details(recipe_url=recipe_url, recipe_id=recipe_id)
                time.sleep(5)

        LOGGER.info(
            "Completed processing a page",
            url=url,
            total_calls=total_calls,
            successful_calls=successful_calls,
            success_rate=round(successful_calls * 100 / total_calls, 2),
        )
        page_number += 1
        url, recipe_urls = get_recipe_links_on_single_page(page_number)


if __name__ == "__main__":
    run_scraper()
