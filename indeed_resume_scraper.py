import time
from selenium import webdriver
import os
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
import pickle
from selenium.webdriver.support.ui import WebDriverWait
import pandas as pd
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException



# Configure Chrome to download files automatically
download_dir = os.path.abspath("./downloads")  # Set your download directory
os.makedirs(download_dir, exist_ok=True)
# Configure Chrome (headless mode)
chrome_options = webdriver.ChromeOptions()
# chrome_options.add_argument("--headless")
prefs = {
    "download.default_directory": download_dir,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "plugins.always_open_pdf_externally": True  # Auto-open PDFs
}


chrome_options.add_experimental_option("prefs", prefs)
# chrome_options.add_argument("--headless")  # Run in headless mode
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--disable-webgl")
chrome_options.add_argument("--disable-webrtc")
chrome_options.add_argument("--disable-software-rasterizer")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
)
chrome_options.add_argument("--disable-features=VizDisplayCompositor")
# chrome_options.add_argument("--remote-debugging-port=9222")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://resumes.indeed.com/"
}
# driver = webdriver.Chrome(options=chrome_options)
driver = uc.Chrome()

driver.execute_cdp_cmd("Network.setExtraHTTPHeaders", {"headers": headers})

# Path to store the cookies
cookie_file = "cookies_indeed.pkl"

def fetch_name():
    xpath = "//div[@id='basic_info_cell']//h1[@id='resume-contact']"
    try:
        # for el in driver.find_elements(By.TAG_NAME, "h1"):
        #     print("H1:", el.get_attribute("id"), "-", el.text)

        # xpath = "//div[@data-shield-id='basic_info_cell']//h1[@data-shield-id='resume-contact']"
        # element = WebDriverWait(driver, 30).until(
        #     EC.visibility_of_element_located((By.XPATH, xpath))
        # )

        # # scroll into view just in case it’s off-screen
        # driver.execute_script("arguments[0].scrollIntoView(true);", element)

        # name = element.text.strip()
        # print("Extracted name:", name)
        # print("FOUND" if "aaron goad" in name.lower() else "NOT FOUND")
        xpath = "//h1[contains(@class,'fn')]"
        el = WebDriverWait(driver, 30).until(
            EC.visibility_of_element_located((By.XPATH, xpath))
        )
        print("Extracted resume name:", el.text.strip())
        return found

    except TimeoutException:
        # fallback to raw HTML search
        page = driver.page_source.lower()
        found = "Work Experience" in page
        print(f"Fallback HTML search -> {'FOUND' if found else 'NOT FOUND'}")
        return found
    # try:
    #     # Wait until the h1#resume-contact inside #basic_info_cell is visible
    #     xpath = "//div[@id='basic_info_cell']//h1[@id='resume-contact']"
    #     element = WebDriverWait(driver, 20).until(
    #         EC.visibility_of_element_located((By.XPATH, xpath))
    #     )
    #     name_text = element.text.strip()
    #     val = "aaron goad" in name_text.lower()
    #     print(val)
    #     return val

    # except Exception as e:
    #     print(f"Error locating name element: {e}")
    #     return False

    finally:
        driver.quit()

def save_cookies():
    """ Save cookies to a file after manual login. """
    driver.get("https://resumes.indeed.com")  # Navigate to login page

    # Wait for manual login (you can adjust this time as needed)
    print("Please log in manually within 30 seconds...")
    time.sleep(60)  # Allow time for manual login

    # Save cookies to a file
    with open(cookie_file, "wb") as file:
        pickle.dump(driver.get_cookies(), file)
    print("Cookies saved successfully!")

def load_cookies_and_access_page(url):
    """ Load saved cookies and access a protected page. """
    driver.get("https://resumes.indeed.com/")  # Open Indeed homepage

    # Load cookies from file
    # try:
    with open(cookie_file, "rb") as file:
        cookies = pickle.load(file)
        for cookie in cookies:
            driver.add_cookie(cookie)
    print("Cookies loaded successfully!")

    driver.get(url)

    # Wait to observe the loaded session
    time.sleep(5)
    print("Page loaded with cookies applied.")

def extract_candidate_pages(url):
    # Save cookies if not already saved

    load_cookies_and_access_page(url)
    fetch_name()

def main():
        
    url = f"https://resumes.indeed.com/resume/2c31c7d97635dce1"
    
    #save_cookies()

    extract_candidate_pages(url)


if __name__ == "__main__":
    main()