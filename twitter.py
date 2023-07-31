import json
import os
from typing import Dict
from pathlib import Path

from loguru import logger as log
from scrapfly import ScrapeConfig, ScrapflyClient, ScrapeApiResponse

SCRAPFLY = ScrapflyClient(key=os.environ["SCRAPFLY_KEY"])
BASE_CONFIG = {
    "asp": True,
    "render_js": True,
}


def parse_user(data: Dict) -> Dict:
    """parse Twitter user JSON data into a flat structure"""
    if type(data) is dict:
        return {"id": data["id"], "rest_id": data["rest_id"], "verified": data["is_blue_verified"], **data["legacy"]}
    return {"data": "null"}


async def _scrape_twitter_app(url: str, _retries: int = 0, **scrape_config) -> str | ScrapeApiResponse:
    """Scrape Twitter page and scroll to the end of the page if possible"""
    if not _retries:
        log.info("scraping {}", url)
    else:
        log.info("retrying {}/2 {}", _retries, url)
    result = await SCRAPFLY.async_scrape(
        ScrapeConfig(url, auto_scroll=True, **scrape_config, **BASE_CONFIG)
    )
    if "Something went wrong. Try reloading." in result.content:
        if _retries >= 1:
            # raise Exception("Twitter web app crashed too many times")
            log.error(f"Twitter Profile:: {url} not found")
            return "null"
        return await _scrape_twitter_app(url, _retries=_retries + 1, **scrape_config)
    return result


async def scrape_profile(username: str) -> Dict:
    """
    Scrapes Twitter user profile page
    returns user data
    """
    url = f"https://twitter.com/{username}"
    result = await _scrape_twitter_app(url, wait_for_selector="[data-testid='tweet']")
    users = {}
    if result != "null":
        # capture background requests and extract ones that contain user data
        _xhr_calls = result.scrape_result["browser_data"]["xhr_call"]
        user_calls = [f for f in _xhr_calls if "UserBy" in f["url"]]
        for xhr in user_calls:
            data = json.loads(xhr["response"]["body"])
            if data['data']:
                parsed = parse_user(data["data"]["user"]["result"])
                users[parsed["screen_name"]] = parsed
            else:
                users[username] = {username: "null"}
    else:
        users[username] = {username: "null"}

    return users[username]


async def write_profile_to_json(username):

    profile = await scrape_profile(username)

    output = Path(__file__).parent / "results"
    output.mkdir(exist_ok=True)
    if not Path.exists(output.joinpath("profile.json")):
        output.joinpath("profile.json").touch(exist_ok=True)
    write_json(profile, output.joinpath("profile.json"))


def write_json(new_data, filename):
    with open(filename, 'r+') as file:
        # First we load existing data into a dict.
        file_data = json.load(file)
        # Join new_data with file_data inside emp_details
        file_data["users"].append(new_data)
        # Sets file's current position at offset.
        file.seek(0)
        # convert back to json.
        json.dump(file_data, file, indent=4)

# list_of_urls = [
#     'http://quotes.toscrape.com/page/1/',
#     'http://quotes.toscrape.com/page/2/',
# ]
#
# scraped_quotes = []
#
# with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
#     executor.map(scrape_profile, list_of_urls)
