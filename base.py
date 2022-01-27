import os
from pathlib import Path
from time import sleep
import shutil

from utils import log, inputlog
from browsers.chrome import ChromeBrowser

class Base:
    def __init__(self, accounts: list, proxies: list, src_profile_path: Path, profile_path: Path):
        self.accounts = accounts
        self.proxies = proxies
        self.src_profile_path = src_profile_path
        self.profile_path = profile_path
        
    def run(self, **kwargs):
        start_idx = kwargs.get('start', 0)
        for idx, account in enumerate(self.accounts):
            if idx == len(self.proxies):
                self._log("Out of proxies")
                break

            if idx < start_idx:
                continue

            gmail = account["gmail"]["user"]
            proxy = self.proxies[idx]
            
            src_profile_folder = self.src_profile_path / gmail
            des_profile_folder = self.profile_path / gmail

            self._log("="*60)
            self._log(f"{gmail}: proxy => {proxy}")

            if des_profile_folder.exists() and des_profile_folder.is_dir():
                self._log(f"{gmail}: Delete old profile: {des_profile_folder}")
                shutil.rmtree(des_profile_folder)

            shutil.copytree(src_profile_folder, des_profile_folder)

            try:
                for key, value in account.items():
                    for k2 in ["link", "addr"]:
                        if k2 in value:
                            self._log(f"{gmail}: {key} => {value[k2]}")

                chrome = ChromeBrowser(profile_path=des_profile_folder, proxy=proxy)
                chrome._clear_old_session()
                chrome.run_browser(debug=True)
                chrome.stealth(platform=None, languages=[])
                self.run_script(chrome, account, **kwargs)
                self._log(f"{gmail}: done")
            except Exception as err:
                self._log(f"{gmail}: Err => {err}", True)
            finally:
                chrome.quit_browser()
                sleep(5)
                shutil.rmtree(des_profile_folder)
                self._log("="*60)
                
    def _log(self, log_:str, err=False):
        log(self.__class__.__name__, log_, err)
    
    def _input(self, log_:str):
        inputlog(self.__class__.__name__, log_)

    def run_script(self, chrome_browser: ChromeBrowser, account: dict, **kwargs):
        raise NotImplementedError
