import argparse
from pathlib import Path
from time import sleep
import re

import requests
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

from browsers.chrome import ChromeBrowser, Follow
from utils import fetch_proxies, read_accounts
from base import Base
from bypass_captcha.binance import PuzleSolver

class CoinMarketCap(Base):
    def __init__(self, accounts: list, proxies: list, src_profile_path: Path, profile_path: Path):
        super().__init__(accounts, proxies, src_profile_path, profile_path)

    def get_and_download_captcha(self, chrome_browser: ChromeBrowser):
        captcha_image = chrome_browser.wait_and_get_element("//div[contains(@style, 'antibot')]", raise_exception=False, print_log=False, timeout=10)
        if not captcha_image:
            return None
        captcha_style = captcha_image.get_attribute("style")
        captcha_url = re.search(r'https(.*?)png', captcha_style).group()
        return requests.get(captcha_url, headers={'referer': 'https://coinmarketcap.com/'}).content
    
    def bypass_captcha(self, chrome_browser: ChromeBrowser):
        while True:
            try:
                btn_submit = chrome_browser.wait_and_get_element("//button[contains(text(), 'Join Airdrop')]", raise_exception=False, print_log=False, timeout=10)
                img_str = self.get_and_download_captcha(chrome_browser)
                if not btn_submit:
                    break
                else:
                    if not img_str:
                        chrome_browser.scroll_into_view(btn_submit)
                        sleep(5)
                        try:
                            btn_submit.click()
                        except Exception as err:
                            break
                        sleep(10)
                        img_str = self.get_and_download_captcha(chrome_browser)

                    move_x_pixel = PuzleSolver().get_position(img_str)
                    move_x_pixel_ = move_x_pixel + 10

                    slide_btn = chrome_browser.wait_and_get_element("//div[@_id='ar']")
                    actions = ActionChains(chrome_browser.browser).drag_and_drop_by_offset(slide_btn, move_x_pixel_, 0)
                    actions.perform()
                    self._log(f"move_x_pixel: {move_x_pixel} {move_x_pixel_}")
            except Exception as err:
                self._log("Error: {err}", True)

    def run_script(self, chrome_browser: ChromeBrowser, account: dict, link: str = None, **kwargs):
        gmail = account["gmail"]["user"]
        driver = chrome_browser.browser
        driver.get(link)

        join_btn = chrome_browser.wait_and_get_element("//button[contains(text(), 'Join This Airdrop')]")
        join_btn.click()

        jobs: list = driver.find_elements(by=By.CSS_SELECTOR, value='div.has-title.has-footer > div > div')
        for job in jobs:
            sleep(1)
            chrome_browser.scroll_into_view(job)
            job_text = job.text.split('\n')[0]
            if 'input' in job.get_attribute('innerHTML'):
                input_box: WebElement = job.find_element(by=By.TAG_NAME, value='input')
                chrome_browser.scroll_into_view(input_box)
                placeholder = input_box.get_attribute('placeholder')
                if len(placeholder) > 0:
                    self._log(placeholder)
                    if 'BEP20' in placeholder:
                        input_box.send_keys(account["metamask"]["addr"])
                    elif 'Ethereum Wallet Address' in placeholder:
                        input_box.send_keys(account["metamask"]["addr"])
                    elif 'Twitter handle' in placeholder:
                        input_box.send_keys(f'@{account["twitter"]["user"]}')
                    elif 'Facebook handle' in placeholder:
                        input_box.send_keys(account["facebook"]["link"])
                    elif 'Telegram handle' in placeholder:
                        input_box.send_keys(account["telegram"]["link"])
                    elif 'link to retweeted' in placeholder:
                        input_box.send_keys(Keys.CONTROL + 'v')
                else:
                    tick: WebElement = job.find_element(by=By.TAG_NAME, value='label')
                    tick.click()
                
            else:
                btn: WebElement = job.find_element(by=By.TAG_NAME, value='button')
                success = False
                for txt in ['Twitter Account', 'Facebook Account', 'Telegram Channel', 'YouTube Account', 'Retweet']:
                    if txt.lower() in job_text.lower():
                        chrome_browser.scroll_into_view(btn)
                        success = True
                        btn.click()
                        
                if success:
                    chrome_browser.switch_to_window(1)
                    follow_success: Follow = None

                    if 'Twitter Account' in job_text:
                        follow_success: Follow = chrome_browser.follow_twitter()
                    elif 'Facebook Account' in job_text:
                        follow_success: Follow = chrome_browser.follow_facebook()
                    elif 'Telegram Channel' in job_text:
                        open_btn = chrome_browser.wait_and_get_element("//span[text() = 'Open in Web']")
                        chrome_browser.scroll_into_view(open_btn)
                        open_btn.click()
                        sleep(10)
                        follow_success: Follow = chrome_browser.join_telegram()
                    elif 'Retweet' in job_text:
                        follow_success = chrome_browser.retweet(account["twitter"]["link"])
                    elif 'YouTube Account' in job_text:
                        follow_success: Follow = chrome_browser.subscribe_youtube()

                    driver.close()
                    chrome_browser.switch_to_window(0)
                    self._log(f"{job_text}: {follow_success.value}")
                else:
                    if 'to watchlist' in job_text.lower():
                        btn.click()
                        self._log(f"{job_text}: ok")
                    else:
                        btn.click()
                        self._input(f"{job_text} ok ? ")

        self.bypass_captcha(chrome_browser)
        self._input(f"{gmail}: OK ?")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Cheat coinmarketcap.com')
    parser.add_argument('--link', type=str, required=True, help='coinmarketcap.com link')
    parser.add_argument('--start', type=int, required=False, default=0, help='idx start account')
    args = parser.parse_args()

    proxies = fetch_proxies()
    accounts = read_accounts()
    src_profile_path = Path("src_profiles")
    profile_path = Path("profiles")
    
    CoinMarketCap(accounts, proxies, src_profile_path, profile_path).run(**args.__dict__)
