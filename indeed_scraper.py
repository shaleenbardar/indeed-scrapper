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
cookie_file = "cookies.pkl"

def fetch_name(url, search_keyword):
    """
    Fetches candidate names with incremental scrolling to trigger lazy loading
    """
    try:
        driver.get(url)
        candidate_data = []
        retry_count = 0
        max_retries = 5  # Stop after 5 failed attempts to find new candidates
        candidates_per_page = 0

        while retry_count < max_retries and len(candidate_data) < 200:
            # Wait for candidate elements to load
            WebDriverWait(driver, 15).until(
                EC.presence_of_all_elements_located((By.XPATH, '//*[@class="css-1nqxi4r e1wnkr790"]'))
            )

            current_elements = driver.find_elements(By.XPATH, '//*[@class="css-1nqxi4r e1wnkr790"]')
            new_data = []
            for el in current_elements:
                name = el.text.strip()
                if name and name not in [data['name'] for data in candidate_data]:
                    # Find the div and extract the id attribute
                    parent_div = el.find_element(By.XPATH, './ancestor::div[@data-cauto-id="candidate-row"]')
                    candidate_id = parent_div.get_attribute("id")
                    new_data.append({'name': name, 'indeed_id': candidate_id, 'uri': 'http://www.indeed.com/r/'+ name.replace(" ", "+") +'/' + candidate_id})
                    candidates_per_page += 1

            if not new_data:
                retry_count += 1
                time.sleep(1)
                continue

            # Add new names to list
            candidate_data.extend(new_data)
            print(f"Found {len(new_data)} new candidates. Total: {len(candidate_data)}")
            
            # Reset retry counter
            retry_count = 0

            # Scroll to last found element
            try:
                last_element = current_elements[-1]
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", last_element)
            except Exception as e:
                print(f"Error scrolling: {e}")
                break

            # Wait for potential new elements to load
            time.sleep(1)  # Adjust based on observed load times

            print(candidates_per_page)
            if candidates_per_page in {47,48,49,50}:
                try:
                    next_button = driver.find_element(By.XPATH, "//button[span[text()='Next']]")
                    if next_button:
                        next_button.click()
                        candidates_per_page = 0
                        time.sleep(2)  # Wait for the next page to load
                        retry_count = 0  # Reset retry count after clicking "Next"
                    else:
                        break  # No more pages
                except Exception as e:
                    print(f"Error clicking next button: {e}")
                    break
    
        df = pd.DataFrame(candidate_data)
        df['search_keyword'] = search_keyword
        output_file = search_keyword.replace(" ", "_") + ".csv"
        df.to_csv(output_file, index=False)
        print(f"Data saved to {output_file} with {len(candidate_data)} candidates.")
        return candidate_data

    except Exception as e:
        print(f"Error: {e}")
        return []


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

def extract_candidate_pages(url, search_keyword):
    # Save cookies if not already saved

    load_cookies_and_access_page(url)
    fetch_name(url, search_keyword)

def main():
    # URL of the job candidates page
    search_keyword = "data analysis"
        
    url = f"https://resumes.indeed.com/search?from=as&q={search_keyword}&backUrl=https%3A%2F%2Fbilling.indeed.com%2Fo%2Fsingle-page%3FlinkSource%3Dnull%26continue%3Dhttps%253A%252F%252Fresumes.indeed.com%252Fsearch%253Ffrom%253Das%2526q%253D{search_keyword.replace(' ', '%252520')}%26registrationSessionRef%3Da8439fcf-26ac-4edd-b103-795249bc815b"
    
    #save_cookies()

    extract_candidate_pages(url, search_keyword)

    driver.quit()

if __name__ == "__main__":
    main()