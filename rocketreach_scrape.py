import time
from selenium import webdriver
import os
import re
import requests
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
import pickle
from selenium.webdriver.support.ui import WebDriverWait
import pandas as pd
from selenium.webdriver.support import expected_conditions as EC


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
    "Referer": "https://rocketreach.co/"
}
# driver = webdriver.Chrome(options=chrome_options)
driver = uc.Chrome(version_main=134)

driver.execute_cdp_cmd("Network.setExtraHTTPHeaders", {"headers": headers})

# Path to store the cookies
cookie_file = "cookies.pkl"

def save_cookies():
    """ Save cookies to a file after manual login. """
    driver.get("https://rocketreach.co/")  # Navigate to login page

    # Wait for manual login (you can adjust this time as needed)
    print("Please log in manually within 60 seconds...")
    time.sleep(60)  # Allow time for manual login

    # Save cookies to a file
    with open(cookie_file, "wb") as file:
        pickle.dump(driver.get_cookies(), file)
    print("Cookies saved successfully!")

def load_cookies_and_access_page(url):
    """ Load saved cookies and access a protected page. """
    driver.get("https://rocketreach.co/")  # Open Indeed homepage

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


def build_search_url(name, location=None):
    base_url = "https://rocketreach.co/person?start=1&pageSize=10"
    name = name.replace(" ", "%20")

    titles = []
    titles += ["data%20analyst", "data%20analysis", "data%20scientist"]

    url = f"{base_url}&name={name}"
    if location and isinstance(location, str):  # ✅ check it's a valid string
        url += f"&geo%5B%5D={location.replace(' ', '%20')}"

    for title in titles:
        url += f"&current_title%5B%5D={title}"

    return url

def check_no_results():
    """Check if 'No Results Found' is present on the page."""
    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located(
                (By.XPATH, "//h3[contains(text(), 'No Results Found')]")
            )
        )
        return True
    except:
        return False

def search_candidate(name, location, search_keyword):
    """Attempt search with fallback logic: full → drop location"""
    attempts = [
        (name, location),
        (name, None)
    ]

    for attempt_name, attempt_location in attempts:
        url = build_search_url(attempt_name, attempt_location)
        print(f"Trying URL: {url}")
        load_cookies_and_access_page(url)

        time.sleep(3)  # allow time for page to load
        if not check_no_results():
            emails = extract_contact_info(url)
            return emails  # contact extracted
        else:
            print("No results found. Trying fallback...")

    print(f"Skipping candidate: {name}")
    return []  # all fallbacks failed

def extract_contact_info(url):
    """
    Extracts contact information from the candidate's page
    """
    try:
        shadow_host = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "svelte-component[type='ProfileCard']"))
        )
        shadow_root = driver.execute_script("return arguments[0].shadowRoot", shadow_host)

        # ✅ Click the "Get Contact Info" button inside shadow root
        buttons = shadow_root.find_elements(By.CSS_SELECTOR, "button")
        for btn in buttons:
            if "Get Contact Info" in btn.text:
                driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(30)  # wait for contact details to load
                break

        # ✅ Extract profile name
        profile_name_element = shadow_root.find_element(By.CSS_SELECTOR, '#profile-name')
        print("Profile Name:", profile_name_element.text.strip())

        # ✅ Extract email or phone (after button click)
        elements = shadow_root.find_elements(By.CSS_SELECTOR, "a[data-testid='email-phone-text-mobile']")
        if elements:
            emails = []
            for i, elem in enumerate(elements, start=1):
                email = elem.get_attribute("innerText").strip()
                print(f"Email {i}:", email)
                emails.append(email)
            return emails
        else:
            print("No contact information found after clicking 'Get Contact Info'.")
            return []

    except Exception as e:
        print(f"Error extracting contact info: {e}")
        return {}
    
API_KEY = '1889a7bkb7f30903f4bb253e7dd9b2e50e21b28e'
BASE_URL = 'https://api.rocketreach.co/v1/api'

def search_person(name, location):
    url = f"{BASE_URL}/person/search"
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    params = {
        'name': name,
        'location': location
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        for person in data.get('profiles', []):
            print(f"Name: {person.get('name')}")
            print(f"Email: {person.get('email')}")
            print(f"Location: {person.get('location')}")
            print('---')
    else:
        print(f"Error: {response.status_code} - {response.text}")



def main():
    #df = pd.read_csv("candidates.csv")

    #df = df[df['name'].notna()].reset_index(drop=True)
    search_person('Sean Madkins', 'Norfolk')
    #email_cols = ["email_1", "email_2"]
    # for col in email_cols:
    #     df[col] = ""

    # for index, row in df.iterrows():
    #     name = row["name"]
    #     location = row.get("city", None)
    #     print(f"\nSearching: {name}, {location}")
    #     emails = search_candidate(name, location, "data analysis")
    #     for i, email in enumerate(emails[:len(email_cols)]):
    #         df.at[index, email_cols[i]] = email

    # # Save the updated dataframe
    # df.to_csv("candidates_updated.csv", index=False)
    # print("Finished. Updated CSV saved as 'candidates_updated.csv'")
    # driver.quit()

if __name__ == "__main__":
    main()
