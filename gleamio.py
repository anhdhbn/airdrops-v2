import argparse
from pathlib import Path
from enum import Enum
from time import sleep

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from browsers.chrome import ChromeBrowser
from utils import fetch_proxies, read_accounts
from base import Base

class GleamIoEnum(Enum):
    BSC_Wallet_Address = "BSC Wallet Address"
    BEP20_Wallet_Address = "BEP20 wallet address"
    Twitter = "Enter using Twitter"
    Retweet_xxx_on_Twitter = "Retweet"
    Join_Telegram_Chat = "Join Telegram Chat"
    Join_Telegram_Announcement = "Join Telegram Announcement"
    Refer_More_People = "Refer"
    Share_Your_Friends = "Your Friends"
    Click_For = "Click For"

class GleamIo(Base):
    def __init__(self, accounts: list, proxies: list, src_profile_path: Path, profile_path: Path):
        super().__init__(accounts, proxies, src_profile_path, profile_path)

    def run_script(self, chrome_browser: ChromeBrowser, account: dict, link: str = None, **kwargs):
        gmail = account["gmail"]["user"]
        driver = chrome_browser.browser
        driver.get(link)
        
        entry_methods = driver.find_elements(by=By.CSS_SELECTOR, value=".entry-method")
        for entry_method in entry_methods:
            try:
                chrome_browser.scroll_into_view(entry_method)
                entry_text: WebElement = entry_method.find_element(by=By.CSS_SELECTOR, value=".text.ng-scope")
                status: WebElement = entry_method.find_element(by=By.CSS_SELECTOR, value="span.tally")
                if "Done! You got" in status.get_attribute("uib-tooltip") or \
                    "You can enter again" in status.get_attribute("uib-tooltip"):
                    self._log(f"{gmail}: Skipping: {entry_text.text}")
                    continue
                else:
                    self._log(f"{gmail}: Solving: {entry_text.text} {status.get_attribute('uib-tooltip')}")

                if GleamIoEnum.Refer_More_People.value.lower() in entry_text.text.lower() or \
                    GleamIoEnum.Share_Your_Friends.value.lower() in entry_text.text.lower():
                    self._log(f"{gmail}: Skipping: {entry_text.text}")
                    continue
                
                if GleamIoEnum.Click_For.value.lower() in entry_text.text.lower():
                    entry_method.click()
                    sleep(2)
                    continue
                
                if GleamIoEnum.BSC_Wallet_Address.value.lower() in entry_text.text.lower() or \
                    GleamIoEnum.BEP20_Wallet_Address.value.lower() in entry_text.text.lower():
                    entry_method.click()
                    textarea: WebElement = entry_method.find_element(by=By.TAG_NAME, value="textarea")
                    textarea.send_keys(account["metamask"]["addr"])
                    sleep(2)
                    submit_btn: WebElement = entry_method.find_element(by=By.XPATH, value="//span[contains(text(),'Continue')]")
                    submit_btn.click()

                if GleamIoEnum.Twitter.value.lower() in entry_text.text.lower():
                    entry_method.click()

                entry_method.click()
                self._input(f"{gmail}: {entry_text.text}: ")

                captcha_box = chrome_browser.wait_and_get_element(xpath="//h2[contains(text(), 'Prove that you are human')]", timeout=5, raise_exception=False, print_log=False)
                if captcha_box is not None:
                    g_response = chrome_browser.bypass_captcha(site_key="2df90a06-8aca-45ee-8ba2-51e9a9113e82", website_url="https://gleam.io/")
                    if g_response is not None:
                        self.bypass_captcha(chrome_browser, g_response)
                        
            except Exception as err:
                self._log(f"{gmail}: run_script err: {err}", err=True)
                self._input(f"{gmail}: Please solve exception manually: ")
        self._input(f"{gmail}: OK ?")

    def bypass_captcha(self, chrome_browser: ChromeBrowser, g_response: str):
        chrome_browser.browser.execute_script(f"document.getElementById('anycaptchaSolveButton').onclick('{g_response}');")        

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Cheat gleam.io')
    parser.add_argument('--link', type=str, required=True, help='gleam.io link')
    parser.add_argument('--start', type=int, required=False, default=0, help='idx start account')
    args = parser.parse_args()

    proxies = fetch_proxies()
    accounts = read_accounts()
    src_profile_path = Path("src_profiles")
    profile_path = Path("profiles")
    
    GleamIo(accounts, proxies, src_profile_path, profile_path).run(**args.__dict__)
