import re
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
    time.sleep(120)
    with open(cookie_file, "wb") as file:
        pickle.dump(driver.get_cookies(), file)
    print("Cookies saved successfully!")

def load_cookies_and_access_page(url):
    driver.get("https://resumes.indeed.com/")
    with open(cookie_file, "rb") as file:
        for cookie in pickle.load(file):
            driver.add_cookie(cookie)
    print("Cookies loaded successfully!")
    driver.get(url)
    time.sleep(5)
    print("Page loaded with cookies applied.")

def extract_experience_text(lines):
    import re
    header_rx = re.compile(r'^(?:professional\s+experience|work\s+experience|experience)\:?\s*$', re.I)
    # find the Experience header
    start = next((i for i, ln in enumerate(lines) if header_rx.match(ln.strip())), None)
    if start is None:
        return ""
    exp = []
    for ln in lines[start+1:]:
        ln = ln.strip()
        if not ln: continue
        # stop at next section header like "Education:" or "Skills:"
        if re.match(r'^[A-Za-z &]+:\s*$', ln):
            break
        exp.append(ln)
    # merge hyphenated words and continuations
    cleaned = []
    for ln in exp:
        if cleaned and cleaned[-1].endswith('-'):
            cleaned[-1] = cleaned[-1][:-1] + ln
        elif cleaned and not ln[0].isupper() and not ln.startswith('•'):
            cleaned[-1] += ' ' + ln
        else:
            cleaned.append(ln)
    return "\n".join(cleaned)

def wait_for_resume_load(driver, timeout=30):
    """
    Block until the resume is rendered either as:
     - an HTML iframe[name="resume_frame"], or
     - a PDF-style text layer div.react-pdf__Page__textContent
    """
    WebDriverWait(driver, timeout).until(
        lambda d: d.find_elements(By.CSS_SELECTOR, "iframe[name='resume_frame']") 
                  or d.find_elements(By.CSS_SELECTOR, "div.react-pdf__Page__textContent")
    )


def extract_resume_data(url: str) -> dict:
    load_cookies_and_access_page(url)

    # hold until *either* HTML iframe or PDF text layer shows up
    wait_for_resume_load(driver)

    data = {}

    # — HTML iframe path —
    frames = driver.find_elements(By.CSS_SELECTOR, "iframe[name='resume_frame']")
    if frames:
        # grab the finished resume HTML
        html = frames[0].get_attribute("srcdoc")
        soup = BeautifulSoup(html, "html.parser")
        # print("Found HTML resume content")
        # print("HTML content:", soup.prettify()[:1000])  # debug output

        # Name
        el = soup.select_one("#basic_info_cell h1.fn")
        data["Name"] = el.get_text(strip=True) if el else ""

        # Experience
        cont = soup.find("div", id="work-experience-items")
        print("Found work experience section:", cont is not None)
        if cont:
            parts = []
            for item in cont.select("div.work-experience-section"):
                title = item.select_one(
                    "h3[data-shield-id='workExperience_work_title']"
                ).get_text(strip=True)
                dates = item.select_one(
                    "div[data-shield-id='workExperience_work_dates']"
                ).get_text(strip=True)
                desc = item.select_one(
                    "p[data-shield-id='workExperience_work_description']"
                ).get_text("\n", strip=True)
                parts.append(f"{title} ({dates})\n{desc}")
            data["Experience"] = "\n\n".join(parts)
        else:
            data["Experience"] = ""

        return data

    # — PDF‐style fallback: collect rendered text spans —
    spans = driver.find_elements(
        By.CSS_SELECTOR,
        "div.react-pdf__Page__textContent span[role='presentation']"
    )
    lines = [s.text.strip() for s in spans if s.text.strip()]

    # Name: first multi‐word ALL‐CAPS line
    data["Name"] = next(
        (l for l in lines if l.isupper() and len(l.split()) > 1),
        ""
    )

    # Experience: flexible header + collect until next header
    data["Experience"] = extract_experience_text(lines)
    if not data["Experience"]:
        print("No experience section found in resume.")
    return data

def main():
    #save_cookies()  # uncomment to generate cookies file first time

    urls = [
        "https://resumes.indeed.com/resume/cb459e5ab31ac6de",
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