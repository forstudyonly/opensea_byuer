import json
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium import webdriver


def load_cookies(driver):
    with open("assets/cookies.txt", "r", encoding="utf-8") as file:
        cookies = json.loads(file.read())
    for cook in cookies:
        # print(cook)
        if cook.get("sameSite", False):
            del cook['sameSite']
        driver.add_cookie(cook)


def get_chromedriver():
    chrome_options = Options()
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    error = False
    try:
        driver.get(f"https://core-api.prod.blur.io/v1/collections/nakamigos/executable-bids")
        load_cookies(driver)
    except BaseException as ex:
        print("не можем добавить куки")
        error = True
    try:
        driver.refresh()

        json_data = json.loads(driver.find_element(By.TAG_NAME, "pre").text)
        if "Unauthorized" in json_data:
            error = True

    except BaseException as ex:
        error = True
        print(ex)
    if error:
        return False
    else:
        return driver


def get_top_bid(driver, collection):
    try:
        driver.get(f"https://core-api.prod.blur.io/v1/collections/{collection}/executable-bids")
        json_data = json.loads(driver.find_element(By.TAG_NAME, "pre").text)
        if "Unauthorized" in json_data:
            load_cookies(driver)
            driver.refresh()
        else:
            top_bid = json_data['priceLevels'][0]['price']
            return top_bid

    except BaseException as ex:
        with open("assets/parser_blur_errors.txt", "a", encoding="utf-8") as file:
            file.write(f"{ex}\n")
        return False
