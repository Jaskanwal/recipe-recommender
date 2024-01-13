from bs4 import BeautifulSoup
import requests
import time
import json
import os
from typing import List, Tuple, Dict
import uuid
import shutil
import re
from collections import defaultdict

from src.common.utils import clean_non_ascii
from src.scraper.constants import headers
from src.scraper.utils import initialize_scraper

website_tag = "archanaskitchen"
BASE_WEBSITE_URL = "https://www.archanaskitchen.com"

LOGGER, DATA_DIR_RECIPES, DATA_DIR_IMAGES = initialize_scraper(website_tag)


def get_recipe_links_on_single_page(x: int) -> Tuple[str, List[str]]:
    """Get links of all the recepies on a single page

    Args:
        x (int): Page number to access

    Returns:
        Tuple[str, List[str]]:: Tupe of parent url and list of recepie urls listed on the parent url
    """

    # page url to to scrape different recepie urls
    url = BASE_WEBSITE_URL + f"/recipes/page-{x}"
    r = requests.get(url, headers=headers)

    recipe_urls = []

    if r.status_code == 200:
        soup = BeautifulSoup(r.content, features="lxml")

        dishes = soup.find_all("div", class_="blogRecipe")

        for dish in dishes:
            recipe = BASE_WEBSITE_URL + dish.find("a").get("href")
            recipe_urls.append(recipe)

    return url, recipe_urls


def save_recipe_image(source_image_url: str, local_image_url: str) -> bool:
    """Save the image from source url on web to a destination local url

    Args:
        source_image_url (str): url of the source image on web
        local_image_url (str): url of the destination url

    Returns:
        bool: indicator if saving image is successful or not
    """
    r = requests.get(source_image_url, stream=True, headers=headers)

    try:
        with open(local_image_url, "wb") as f:
            r.raw.decode_content = True
            shutil.copyfileobj(r.raw, f)
        return True
    except Exception:
        LOGGER.info(
            "Could not download recipe image",
            source_image_url=source_image_url,
            local_image_url=local_image_url,
        )
        return False


def get_recipe_name(recipe_details: BeautifulSoup, recipe_url: str) -> str:
    """Get the recipe name"""
    try:
        name = clean_non_ascii(recipe_details.find("h1", class_="recipe-title").text)
    except Exception as e:
        LOGGER.error("Could not find recipe name", recipe_url=recipe_url)
        raise e
    return name


def get_recipe_description(recipe_details: BeautifulSoup, recipe_url: str) -> str:
    """Get the recipe description"""
    try:
        description = []
        for item in recipe_details.find("div", class_="row recipedescription").find("span").find_all("p"):
            if len(item.text) > 2:
                description.append(clean_non_ascii(item.text))

    except Exception as e:
        LOGGER.error("Could not find recipe description", recipe_url=recipe_url)
        raise e
    return "\n".join(description[:-1])


def get_recipe_ingredient_list(recipe_details: BeautifulSoup, recipe_url: str) -> List[str]:
    """Get the list of ingredients"""
    try:
        ingredients = [clean_non_ascii(item.text) for item in recipe_details.find_all("span", class_="ingredient_name")]
    except Exception as e:
        LOGGER.error("Could not find recipe ingredient list", recipe_url=recipe_url)
        raise e
    return ingredients


def get_recipe_cooking_steps(recipe_details: BeautifulSoup, recipe_url: str) -> Dict[str, List[str]]:
    """Get the recipe description"""
    parsed_recipe_steps = {}
    try:
        recipe_steps_groups = recipe_details.find_all("div", class_="recipeinstructions")
        for idx, recipe_steps_group in enumerate(recipe_steps_groups):
            try:
                key = clean_non_ascii(recipe_steps_group.find("h2", class_="recipeinstructionstitle").text)
            except AttributeError:
                key = f"group_{idx}"

            value = [
                clean_non_ascii(item.text)
                for item in recipe_steps_group.find_all("li", attrs={"itemprop": "recipeInstructions"})
            ]
            parsed_recipe_steps[key] = value

    except Exception as e:
        LOGGER.info("Could not find ingredient quantities", recipe_url=recipe_url)
        raise e
    return parsed_recipe_steps


def get_recipe_cusine(recipe_details: BeautifulSoup, recipe_url: str) -> str:
    """Get the recipe cusine"""
    try:
        cusine = clean_non_ascii(recipe_details.find("span", attrs={"itemprop": "recipeCuisine"}).text)
    except Exception:
        LOGGER.info("Could not find recipe cusine", recipe_url=recipe_url)
        cusine = ""
    return cusine


def get_recipe_diet(recipe_details: BeautifulSoup, recipe_url: str) -> str:
    """Get the recipe diet, e.g., veg, vegan etc"""
    try:
        diet = clean_non_ascii(
            recipe_details.find("div", class_="col-12 diet").find("span", attrs={"itemprop": "keywords"}).text
        )
    except Exception:
        LOGGER.info("Could not find recipe diet", recipe_url=recipe_url)
        diet = ""
    return diet


def get_recipe_servings(recipe_details: BeautifulSoup, recipe_url: str) -> str:
    "Get the number of servings based on which the ingredients are marked"
    try:
        servings = clean_non_ascii(recipe_details.find("span", attrs={"itemprop": "recipeYield"}).text)
        servings = re.search(re.compile(r"\d+"), servings).group()
    except Exception:
        LOGGER.info("Could not find number of servigs", recipe_url=recipe_url)
        servings = ""
    return servings


def get_recipe_cooking_difficulty(recipe_details: BeautifulSoup, recipe_url: str) -> str:
    """Difficulty level in cooking"""
    difficulty = ""
    return difficulty


def get_recipe_cooking_time(recipe_details: BeautifulSoup, recipe_url: str) -> str:
    """Total time estimate for cooking"""
    try:
        total_time = clean_non_ascii(recipe_details.find("span", attrs={"itemprop": "totalTime"}).text)
        total_time = re.search(re.compile(r"\d+\s."), total_time).group()
        total_time = total_time.replace(" M", " minutes")
        total_time = total_time.replace(" H", " hour")
    except Exception:
        LOGGER.info("Could not find total cooking time", recipe_url=recipe_url)
        total_time = ""
    return total_time


def get_recipe_ingredient_quantities(recipe_details: BeautifulSoup, recipe_url: str) -> Dict[str, List[str]]:
    """Detailed quantity of ingredients"""
    parsed_ingredients = defaultdict(list)
    try:
        ingredients = (
            recipe_details.find("div", class_="recipeingredients")
            .find("ul", class_="list-unstyled")
            .find_all(lambda tag: tag.name in ["li", "b"])
        )

        tag = "group_0"

        for ingredient in ingredients:
            content = ", ".join(
                [re.sub(r"^\s+|\s+$|\n|\t", "", clean_non_ascii(item)) for item in ingredient.text.split(",")]
            )
            if ingredient.name == "b":
                tag = content
                continue
            parsed_ingredients[tag].append(content)

    except Exception:
        LOGGER.info("Could not find ingredient quantities", recipe_url=recipe_url)
    return dict(parsed_ingredients)


def get_image_url(recipe_details: BeautifulSoup, recipe_url: str) -> str:
    "Url of a image showing the dish"
    try:
        source_image_url = recipe_details.find("div", class_="recipe-image").find("img").get("src")
        source_image_url = BASE_WEBSITE_URL + source_image_url

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
        image_download_status = save_recipe_image(source_image_url, local_image_url)

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
    page_number = 1
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
