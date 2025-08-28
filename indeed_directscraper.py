import time
from selenium import webdriver
import os
import ssl
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
import pickle
from selenium.webdriver.support.ui import WebDriverWait
import pandas as pd
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import re
from html import unescape

# Disable SSL certificate verification (not recommended for security, but used for testing purposes)
ssl._create_default_https_context = ssl._create_unverified_context


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
cookie_file = "cookies_direct.pkl"

#####################################################################################
#####################################################################################
#####################################################################################
#####################################################################################
import random

def restart_browser():
    """Restart the browser."""
    global driver
    try:
        driver.quit()
    except:
        pass
    
    # Create a new browser instance
    driver = uc.Chrome()
    driver.execute_cdp_cmd("Network.setExtraHTTPHeaders", {"headers": headers})
    print("🔄 Browser has been restarted.")
    time.sleep(3)

# Function to normalize text and remove non-ASCII characters
def normalize_text(text):
    if not text:
        return ""
    
    # HTML entity decoding
    text = unescape(text)
    
    # Remove or replace non-ASCII characters
    import re
    text = re.sub(r'[^\x00-\x7F]+', '', text)  # Remove non-ASCII characters
    
    return text.strip()

# Function to separate company name and tenure (direct separation during scraping)
def separate_company_tenure(text):
    if not text:
        return None, None
    
    # Regular expression pattern: Find year(YYYY) format
    # Find pattern where company name is followed by years
    pattern = r'(.*?)(?:,\s*|\s+)(\d{4}\s*-\s*(?:\d{4}|Present))'
    match = re.search(pattern, text, re.IGNORECASE)
    
    if match:
        company_name = match.group(1).strip()
        tenure = match.group(2).strip()
        return company_name, tenure
    else:
        # If pattern doesn't match, return original text as company name and None for tenure
        return text, None

def fetch_name(url, search_keyword, target_count, seen_ids_csv="indeed_seen_ids.csv"):
    """
    Visit an Indeed Resume search URL, extract candidate cards from the grid,
    and save results to <keyword>_scraped.csv.

    NEW:
    - Skip any candidate whose cleaned id (without 'MATCH_CARD_BASE-') is in seen_ids_csv.
    - Append newly scraped ids to seen_ids_csv so they won't be scraped next time.

    DOM (per your sample):
      - Grid: <ul data-cauto-id="candidate-collection-grid">
      - Card: <div data-cauto-id="MATCH_CARD_BASE-...">
      - Name: <span data-cauto-id="candidate-name">
      - Location: <span class="css-1wagcux ...">
      - Recent job + company/tenure: first <li> under "Relevant Work Experience"
      - Education value: sibling span within the "Education" block
      - Skills: items under ul.css-axcxxt -> div.ecydgvn1
    """
    import random
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    import pandas as pd
    import os
    import time

    global driver

    GRID_XPATH = "//ul[@data-cauto-id='candidate-collection-grid']"
    ROW_XPATH = "//ul[@data-cauto-id='candidate-collection-grid']//div[starts-with(@data-cauto-id,'MATCH_CARD_BASE-')]"

    def clean_card_id(raw: str) -> str:
        if not raw:
            return ""
        return raw.replace("MATCH_CARD_BASE-", "", 1) if raw.startswith("MATCH_CARD_BASE-") else raw

    def load_seen_ids(path: str) -> set:
        ids = set()
        if os.path.exists(path):
            try:
                df = pd.read_csv(path)
                col = None
                for c in df.columns:
                    if c.lower() in ("indeed_id", "id", "candidate_id"):
                        col = c
                        break
                if col is None and df.shape[1] > 0:
                    col = df.columns[0]
                if col is not None:
                    ids = {str(x).strip() for x in df[col].dropna().astype(str).tolist()}
            except Exception:
                # Fallback: one id per line text file
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        for line in f:
                            t = line.strip()
                            if t:
                                ids.add(t)
                except Exception:
                    pass
        return ids

    def save_seen_ids(path: str, ids: set):
        # Write as CSV with header indeed_id
        try:
            pd.DataFrame({"indeed_id": sorted(ids)}).to_csv(path, index=False)
        except Exception as e:
            print(f"⚠️ Could not save seen ids CSV: {e}")

    # Navigate
    try:
        driver.get(url)
    except Exception as e:
        print(f"Error loading page: {e}")
        try:
            restart_browser()
            driver.get(url)
        except Exception as e2:
            print(f"Retry failed: {e2}")
            return []

    # Files
    output_file = f"{search_keyword.replace(' ', '_')}_scraped.csv"

    # Load previously scraped rows (for continuity of your main CSV)
    candidate_data = []
    if os.path.exists(output_file):
        try:
            existing_df = pd.read_csv(output_file)
            candidate_data = existing_df.to_dict("records")
            print(f"📂 Loaded {len(candidate_data)} existing rows from {output_file}.")
        except Exception as e:
            print(f"Error loading existing file: {e}")

    # Load seen ids from the provided file (authoritative skip list)
    seen_ids = load_seen_ids(seen_ids_csv)
    print(f"🔎 Loaded {len(seen_ids)} previously seen ids from {seen_ids_csv}.")

    retry_count = 0
    max_retries = 20
    last_save_count = len(candidate_data)
    page_number = 1

    while retry_count < max_retries and len(candidate_data) < target_count:
        # Wait for the grid
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, GRID_XPATH))
            )
        except TimeoutException:
            retry_count += 1
            print("❌ Grid not found; retrying...")
            try:
                driver.save_screenshot("no_grid.png")
                with open("no_grid.html", "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
            except Exception:
                pass
            time.sleep(min(10, 1 + retry_count))
            continue

        # Find cards
        try:
            candidate_rows = WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located((By.XPATH, ROW_XPATH))
            )
        except TimeoutException:
            retry_count += 1
            print("❌ Candidate cards not found; retrying...")
            try:
                driver.save_screenshot("no_candidate_rows.png")
                with open("no_candidate_rows.html", "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
            except Exception:
                pass
            time.sleep(min(10, 1 + retry_count))
            continue

        if not candidate_rows:
            retry_count += 1
            print("❌ Candidate cards list empty; retrying...")
            time.sleep(min(10, 1 + retry_count))
            continue

        print(f"📄 Page {page_number}: found {len(candidate_rows)} candidate cards.")
        retry_count = 0

        new_data = []
        new_seen_ids = set()  # collect newly encountered ids this pass (to append to the file)

        for row in candidate_rows:
            try:
                WebDriverWait(driver, 10).until(lambda d: row.is_displayed())

                raw_id = row.get_attribute("data-cauto-id") or ""
                card_id = clean_card_id(raw_id)
                if not card_id:
                    # fallback: try @id (less ideal)
                    card_id = clean_card_id(row.get_attribute("id") or "")

                # Skip if already seen
                if card_id and card_id in seen_ids:
                    # print(f"↩️ Skipping already-seen id: {card_id}")
                    continue

                # Name
                try:
                    name_el = row.find_element(By.XPATH, ".//span[@data-cauto-id='candidate-name']")
                    name = normalize_text(name_el.text)
                except NoSuchElementException:
                    continue  # no name, skip

                # Location
                try:
                    loc_el = row.find_element(By.XPATH, ".//span[contains(@class,'css-1wagcux')]")
                    location = normalize_text(loc_el.text)
                except NoSuchElementException:
                    location = ""

                # Job title (most recent)
                try:
                    job_el = row.find_element(
                        By.XPATH,
                        ".//div[contains(@class,'css-f5ofyr')]//ul/li[1]//span[contains(@class,'css-mlbsyu')]"
                    )
                    job_title = normalize_text(job_el.text)
                except NoSuchElementException:
                    job_title = ""

                # Company + tenure
                try:
                    comp_ten_el = row.find_element(
                        By.XPATH,
                        ".//div[contains(@class,'css-f5ofyr')]//ul/li[1]//span[contains(@class,'css-vnnk8q')]"
                    )
                    company_text = normalize_text(comp_ten_el.text)
                    company_name, tenure = separate_company_tenure(company_text)
                except NoSuchElementException:
                    company_name, tenure = "", ""

                # Education
                try:
                    edu_el = row.find_element(
                        By.XPATH,
                        ".//div[.//span[normalize-space()='Education']]//span[contains(@class,'css-vnnk8q')]"
                    )
                    education = normalize_text(edu_el.text)
                except NoSuchElementException:
                    education = ""

                # Skills
                skills = []
                for s in row.find_elements(By.XPATH, ".//ul[contains(@class,'css-axcxxt')]//div[contains(@class,'ecydgvn1')]"):
                    t = normalize_text(s.text)
                    if t:
                        skills.append(t)
                skills_csv = ", ".join(skills)

                # Record
                unique_id = card_id if card_id else f"{name}::{location}"
                uri = f"http://www.indeed.com/r/{name.replace(' ', '+')}/{unique_id}"

                new_data.append({
                    "name": name,
                    "indeed_id": unique_id,
                    "uri": uri,
                    "location": location,
                    "education": education,
                    "skills": skills_csv,
                    "job_title": job_title,
                    "company_name": company_name,
                    "tenure": tenure,
                })

                # Track as seen so we never scrape this id again
                if card_id:
                    new_seen_ids.add(card_id)

                time.sleep(random.uniform(0.15, 0.4))

            except Exception as e:
                print(f"⚠️ Error parsing a card: {e}")

        if not new_data:
            retry_count += 1
            time.sleep(min(8, 1 + retry_count))
        else:
            candidate_data.extend(new_data)
            print(f"✅ Added {len(new_data)} new candidates. Total: {len(candidate_data)}")
            retry_count = 0

            # Update seen ids set in memory
            if new_seen_ids:
                seen_ids.update(new_seen_ids)

        # Save every 20 rows — both main CSV and seen-ids CSV
        if len(candidate_data) - last_save_count >= 20:
            try:
                pd.DataFrame(candidate_data).assign(search_keyword=search_keyword).to_csv(output_file, index=False)
                print(f"💾 Saved {len(candidate_data)} rows to {output_file}.")
                last_save_count = len(candidate_data)
            except Exception as e:
                print(f"Save error: {e}")
            # Persist the seen ids too
            save_seen_ids(seen_ids_csv, seen_ids)
            print(f"🧾 Seen ids updated: {len(seen_ids)} total.")

        # Trigger lazy-load
        try:
            if candidate_rows:
                driver.execute_script(
                    "arguments[0].scrollIntoView({behavior:'smooth', block:'center'});",
                    candidate_rows[-1]
                )
                time.sleep(random.uniform(0.8, 1.4))
        except Exception as e:
            print(f"Scroll error: {e}")

        if len(candidate_data) >= target_count:
            break

        # Pagination (Next button by text)
        next_button = None
        for xp in [
            "//button[.//span[normalize-space()='Next'] and not(@disabled)]",
            "//button[normalize-space()='Next' and not(@disabled)]"
        ]:
            try:
                next_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, xp))
                )
                break
            except TimeoutException:
                pass

        if next_button:
            try:
                # Save safety before changing page
                if len(candidate_data) > last_save_count:
                    pd.DataFrame(candidate_data).assign(search_keyword=search_keyword).to_csv(output_file, index=False)
                    print(f"💾 Pre-pagination save: {len(candidate_data)} rows.")
                    last_save_count = len(candidate_data)
                    save_seen_ids(seen_ids_csv, seen_ids)
                    print(f"🧾 Seen ids updated: {len(seen_ids)} total.")

                next_button.click()
                page_number += 1
                time.sleep(random.uniform(2.5, 4.0))
            except Exception as e:
                print(f"Pagination click failed: {e}")
                try:
                    driver.refresh()
                    time.sleep(3)
                except Exception:
                    pass
        else:
            print("ℹ️ No Next button detected; ending pagination.")
            break

    # Final saves
    if candidate_data:
        try:
            pd.DataFrame(candidate_data).assign(search_keyword=search_keyword).to_csv(output_file, index=False)
            print(f"✅ Final save: {len(candidate_data)} rows to {output_file}.")
        except Exception as e:
            print(f"Final save error: {e}")
    else:
        print("❌ No candidate data collected.")

    # Persist the seen ids one last time
    save_seen_ids(seen_ids_csv, seen_ids)
    print(f"✅ Seen ids saved to {seen_ids_csv} ({len(seen_ids)} total).")

    return candidate_data


#####################################################################################
#####################################################################################
#####################################################################################
#####################################################################################

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
    # First navigate to the domain to set cookies
    driver.get("https://www.indeed.com/")  # Navigate to Indeed main page
    time.sleep(3)  # Wait for page to load

    # Load cookies from file
    try:
        with open(cookie_file, "rb") as file:
            cookies = pickle.load(file)
            for cookie in cookies:
                # Modify domain attribute to prevent domain-related errors
                if 'domain' in cookie:
                    if cookie['domain'].startswith('.'):
                        cookie['domain'] = cookie['domain']
                    else:
                        cookie['domain'] = '.' + cookie['domain'].lstrip('.')
                
                try:
                    driver.add_cookie(cookie)
                except Exception as e:
                    print(f"Error adding cookie: {e}")
                    continue
        print("Cookies loaded successfully!")
    except Exception as e:
        print(f"Error loading cookies: {e}")
        return False

    # Navigate to target URL
    driver.get(url)

    # Wait to observe session loading
    time.sleep(5)
    print("Page loaded with cookies applied.")
    return True

def extract_candidate_pages(url, search_keyword, target_count=1000):
    # Save cookies if not already saved

    load_cookies_and_access_page(url)
    fetch_name(url, search_keyword, target_count)

def main():

    #save_cookies()
    # Provide search keyword selection options to the user
    search_keyword = "data analyst"
    target_count = 10
    print(f"Scraping resumes from Indeed with this keyword...\n")
    
    # Add sorting option (date = sort by date)
    url = f"https://resumes.indeed.com/search?from=as&q={search_keyword.replace(' ', '+')}&sort=date&backUrl=https%3A%2F%2Fbilling.indeed.com%2Fo%2Fsingle-page%3FlinkSource%3Dnull%26continue%3Dhttps%253A%252F%252Fresumes.indeed.com%252Fsearch%253Ffrom%253Das%2526q%253D{search_keyword.replace(' ', '%252520')}%26registrationSessionRef%3Da8439fcf-26ac-4edd-b103-795249bc815b"

    candidate_pages = extract_candidate_pages(url, search_keyword, target_count)

    driver.quit()
    
    # Scraping results summary
    output_file = search_keyword.replace(" ", "_") + "_scraped.csv"
    if os.path.exists(output_file):
        try:
            df = pd.read_csv(output_file)
            print(f"\n===== Scraping Results Summary =====")
            print(f"Total candidates scraped: {len(df)}")
            print(f"Location extraction success rate: {df['location'].notna().mean()*100:.1f}%")
            print(f"Education extraction success rate: {df['education'].notna().mean()*100:.1f}%")
            print(f"Skills extraction success rate: {df['skills'].notna().mean()*100:.1f}%")
            print(f"Job title extraction success rate: {df['job_title'].notna().mean()*100:.1f}%")
            print(f"Company name extraction success rate: {df['company_name'].notna().mean()*100:.1f}%")
            print(f"Tenure extraction success rate: {df['tenure'].notna().mean()*100:.1f}%")
            print(f"\nResults saved to '{output_file}'.")
        except Exception as e:
            print(f"Error analyzing result file: {e}")

if __name__ == "__main__":
    main()