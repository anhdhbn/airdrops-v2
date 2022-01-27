import os
from time import sleep
from typing import Tuple
from urllib.parse import urlparse

import undetected_chromedriver as uc
from selenium_stealth import stealth
from user_agent import generate_user_agent
from anticaptchaofficial.hcaptchaproxyon import *

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.action_chains import ActionChains

from browsers.utils import run_command
from utils import log

class ChromeBrowser():
    def __init__(self,
        profile_path: str = None,
        proxy: str = None
    ):
        self.profile_path = profile_path
        self.proxy = urlparse(proxy)
        self._browser: uc.Chrome = None

        self.user_agent = generate_user_agent(device_type=["desktop"])
        self.captcha_key = os.getenv("CAPTCHA_API", "dae6ac0c51d63b55a0f6fb15e7ef661f")
        self.timeout_wait = 60

    def run_browser(self, **kwargs):
        self._clear_old_session()
        self._browser = uc.Chrome(user_data_dir=self.profile_path, options=self._options(), **kwargs)

    def stealth(
        self, 
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
        draw_mouse=True,
        **kwargs
    ):
        stealth(self._browser, languages=languages, vendor=vendor, platform=platform, webgl_vendor=webgl_vendor, renderer=renderer, fix_hairline=fix_hairline, draw_mouse=draw_mouse, **kwargs)

    def _clear_old_session(self):
        run_command(f"find {self.profile_path} -name 'Singleton*' -delete")

    def _options(self):
        options = uc.ChromeOptions()
        options.add_argument('--no-first-run')
        options.add_argument('--no-service-autorun')
        # options.add_argument('--password-store=basic')
        # options.add_argument('--start-maximized')
        options.add_argument('--disable-gpu') # applicable to windows os only
        options.add_argument('--disable-dev-shm-usage') # overcome limited resource problems
        options.add_argument('--disable-infobars')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--ignore-certificate-errors-skip-list')
        options.add_argument('--ignore-ssl-errors')
        options.add_argument('--disable-web-security')
        options.add_argument('--allow-running-insecure-content')
        options.add_argument('--load-extension=/home/anhdh/projects/airdrops/AnyCaptchaCallbackHooker_Unpacked')
        # options.add_experimental_option("excludeSwitches", ["enable-automation"])
        # options.add_experimental_option('useAutomationExtension', False)
        if self.profile_path is not None:
            options.add_argument(f'--user-data-dir={self.profile_path}')
        if self.proxy is not None:
            proxy = f"{self.proxy.scheme}://{self.proxy.hostname}:{self.proxy.port}"
            options.add_argument(f'--proxy-server={proxy}')
        options.add_argument(f'--user-agent={self.user_agent}')
        return options

    @property
    def browser(self) -> uc.Chrome:
        return self._browser

    def wait_and_get_element(self, xpath: str, timeout=None, raise_exception=True, print_log=True) -> WebElement:
        if raise_exception:
            wait = WebDriverWait(self.browser, self.timeout_wait if timeout is None else timeout)
            element: WebElement = wait.until(EC.visibility_of_element_located((By.XPATH, xpath)))
            return element
        else:
            try:
                wait = WebDriverWait(self.browser, self.timeout_wait if timeout is None else timeout)
                element: WebElement = wait.until(EC.visibility_of_element_located((By.XPATH, xpath)))
                return element
            except Exception as err:
                if print_log:
                    self._log(f"wait_and_get_element: {err}", True)
                return None

    def quit_browser(self):
        self._browser.quit()

    def _log(self, log_:str, err=False):
        log(self.__class__.__name__, log_, err)
    
    def switch_to_main_window(self):
        self.switch_to_window(0)

    def switch_to_window(self, idx):
        self._log(f"switch to window {idx}")
        self._browser.switch_to.window(self._browser.window_handles[idx])

    def close_all_windows_except_main(self):
        self._log("Closing all windows except main window")
        while len(self._browser.window_handles) > 1:
            windows = len(self._browser.window_handles)
            self._log(f"Remaining windows: {windows}")
            self.switch_to_window(1)
            sleep(self.timeout_wait)
            # self._browser.close()
            self._browser.execute_script("window.close()")
            WebDriverWait(self._browser, self.timeout_wait).until(EC.number_of_windows_to_be(windows-1))

    def bypass_captcha(self, site_key, website_url) -> Tuple[bool, str]:
        solver = hCaptchaProxyon()
        solver.set_verbose(1)
        solver.set_key(self.captcha_key)
        solver.set_website_url(website_url)
        solver.set_website_key(site_key)
        solver.set_proxy_address(self.proxy.hostname)
        solver.set_proxy_port(self.proxy.port)
        solver.set_proxy_login(self.proxy.username)
        solver.set_proxy_password(self.proxy.password)
        solver.set_user_agent(self.user_agent)

        g_response = solver.solve_and_return_solution()
        if g_response == 0:
            return None

        return g_response

    def scroll_into_view(self, element):
        self.browser.execute_script("arguments[0].scrollIntoView(true);", element)
