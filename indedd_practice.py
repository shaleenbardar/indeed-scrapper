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

# Configure Chrome options
chrome_options = webdriver.ChromeOptions()
prefs = {
    "download.default_directory": download_dir,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "plugins.always_open_pdf_externally": True
}
chrome_options.add_experimental_option("prefs", prefs)
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--disable-webgl")
chrome_options.add_argument("--disable-webrtc")
chrome_options.add_argument("--disable-software-rasterizer")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
)
chrome_options.add_argument("--disable-features=VizDisplayCompositor")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://resumes.indeed.com/"
}

driver = uc.Chrome()
driver.execute_cdp_cmd("Network.setExtraHTTPHeaders", {"headers": headers})

cookie_file = "cookies_indeed.pkl"

def save_cookies():
    """ Save cookies to a file after manual login. """
    driver.get("https://resumes.indeed.com")
    print("Please log in manually within 30 seconds...")
    time.sleep(60)
    with open(cookie_file, "wb") as file:
        pickle.dump(driver.get_cookies(), file)
    print("Cookies saved successfully!")

def load_cookies_and_access_page(url):
    """ Load saved cookies and access a protected page. """
    driver.get("https://resumes.indeed.com/")
    with open(cookie_file, "rb") as file:
        for cookie in pickle.load(file):
            driver.add_cookie(cookie)
    print("Cookies loaded successfully!")

    driver.get(url)
    time.sleep(5)
    print("Page loaded with cookies applied.")

   # instead wait for the resume iframe to show up
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[name='resume_frame']"))
    )

def scrape_experience(driver) -> str:
    try:
        container = driver.find_element(By.ID, "work-experience-items")
        items = container.find_elements(By.CSS_SELECTOR, "div.section-entry")
        blocks = []
        for item in items:
            title   = item.find_element(By.CSS_SELECTOR, "h3[data-shield-id='workExperience_work_title']").text
            company = item.find_element(By.CSS_SELECTOR, "span[data-shield-id='workExperience_work_experience_company']").text
            loc     = item.find_element(By.CSS_SELECTOR, "span[data-shield-id='workExperience_location_span']").text
            dates   = item.find_element(By.CSS_SELECTOR, "div[data-shield-id='workExperience_work_dates']").text
            desc    = item.find_element(By.CSS_SELECTOR, "p[data-shield-id='workExperience_work_description']").text
            blocks.append(f"{title} at {company}, {loc} ({dates})\n{desc}")
        return "\n\n".join(blocks)
    except Exception:
        return ""

def extract_resume_data(url):
    load_cookies_and_access_page(url)

    # —— ONLY CHANGED: switch into the iframe that holds the resume content ——
    iframe = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[name='resume_frame']"))
    )
    driver.switch_to.frame(iframe)

    # now wait for the resume container inside the iframe
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "#basic_info_cell"))
    )

    data = {}
    # 1) Name: the <h1> inside #basic_info_cell with class 'fn'
    name_el = driver.find_element(By.CSS_SELECTOR, "#basic_info_cell h1.fn")
    data["Name"] = name_el.text.strip()

    # 2) Experience inside that same iframe
    data["Experience"] = scrape_experience(driver)

    # —— Back out to the main page so driver.quit() etc. still works —— 
    driver.switch_to.default_content()

    return data

def main():
    # save_cookies()  # uncomment to generate cookies file first time

    urls = [
        "https://resumes.indeed.com/resume/2c31c7d97635dce1",
        # add more URLs here…
    ]

    all_rows = []
    for url in urls:
        try:
            row = extract_resume_data(url)
            all_rows.append(row)
        except TimeoutException as e:
            print(f"Timeout loading {url}: {e}")
        except Exception as e:
            print(f"Failed to scrape {url}: {e}")

    df = pd.DataFrame(all_rows)
    df.to_csv("resumes.csv", index=False, encoding="utf-8")
    print(f"Written {len(all_rows)} rows to resumes.csv")

    driver.quit()

if __name__ == "__main__":
    main()