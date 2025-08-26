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

def fetch_name(url, search_keyword, target_count=1000):
    try:
        global driver
        try:
            driver.get(url)
        except Exception as e:
            print(f"Error loading page: {e}")
            restart_browser()
            driver.get(url)
            
        candidate_data = []
        retry_count = 0
        max_retries = 20  # Increased retry count
        candidates_per_page = 0
        last_save_count = 0
        page_number = 1
        browser_restart_count = 0
        max_browser_restarts = 5

        # Check if file already exists and load data if it does
        output_file = search_keyword.replace(" ", "_") + "_scraped.csv"  # Changed filename format
        try:
            if os.path.exists(output_file):
                existing_df = pd.read_csv(output_file)
                candidate_data = existing_df.to_dict('records')
                print(f"📂 Loaded {len(candidate_data)} records from existing file.")
                last_save_count = len(candidate_data)
        except Exception as e:
            print(f"Error loading existing file: {e}")

        while retry_count < max_retries and len(candidate_data) < target_count and browser_restart_count < max_browser_restarts:
            # hCaptcha detection logic (more accurate)
            def check_for_hcaptcha():
                # Check only for clear hCaptcha indicators
                
                # Check if URL explicitly contains hcaptcha
                if "hcaptcha" in driver.current_url.lower():
                    return True
                
                # Check for hCaptcha iframe (most reliable method)
                try:
                    iframes = driver.find_elements(By.TAG_NAME, "iframe")
                    for iframe in iframes:
                        iframe_src = iframe.get_attribute("src")
                        if iframe_src and "hcaptcha" in iframe_src:
                            return True
                except:
                    pass
                
                # Check for hCaptcha-related elements
                try:
                    hcaptcha_elements = driver.find_elements(By.XPATH, "//*[contains(@class, 'h-captcha')]")
                    if hcaptcha_elements:
                        return True
                except:
                    pass
                
                return False
            
            # Skip captcha detection at the start of scraping and begin immediately
            
            # ✅ [Modified] Wait before collecting data from each page
            time.sleep(random.uniform(3.0, 5.0))

            try:
                # Set longer wait time
                WebDriverWait(driver, 30).until(
                    EC.presence_of_all_elements_located((By.XPATH, '//span[contains(@class, "e1wnkr790")]'))
                )
            except Exception as e:
                print(f"❌ Candidate name wait timeout: {e}. Skipping this round.")
                retry_count += 1
                time.sleep(3)
                
                # Check if we need to save data before retrying
                if candidate_data and len(candidate_data) > last_save_count:
                    try:
                        df = pd.DataFrame(candidate_data)
                        df['search_keyword'] = search_keyword
                        df.to_csv(output_file, index=False)
                        print(f"💾 Timeout recovery save: {len(candidate_data)} candidate records saved to {output_file}.")
                        last_save_count = len(candidate_data)
                    except Exception as save_error:
                        print(f"Error saving data during timeout recovery: {save_error}")
                
                # Try refreshing the page
                try:
                    driver.refresh()
                    time.sleep(5)
                except:
                    pass
                
                # If multiple failures, restart browser
                if retry_count >= 5:
                    print("⚠️ Multiple element detection failures. Restarting browser...")
                    restart_browser()
                    driver.get(url)
                    browser_restart_count += 1
                    retry_count = 0
                    time.sleep(5)
                
                continue

            try:
                candidate_rows = WebDriverWait(driver, 20).until(
                    EC.presence_of_all_elements_located((By.XPATH, '//div[@data-cauto-id="candidate-row"]'))
                )
                print(f"Found {len(candidate_rows)} potential candidate rows on the page.")
            except Exception as e:
                print(f"❌ Candidate row search timeout: {e}. Skipping this round.")
                retry_count += 1
                time.sleep(3)
                
                # Check if we need to save data before retrying
                if candidate_data and len(candidate_data) > last_save_count:
                    try:
                        df = pd.DataFrame(candidate_data)
                        df['search_keyword'] = search_keyword
                        df.to_csv(output_file, index=False)
                        print(f"💾 Row search timeout recovery save: {len(candidate_data)} candidate records saved to {output_file}.")
                        last_save_count = len(candidate_data)
                    except Exception as save_error:
                        print(f"Error saving data during row search timeout recovery: {save_error}")
                
                # Try refreshing the page
                try:
                    driver.refresh()
                    time.sleep(5)
                except:
                    pass
                
                # If multiple failures, restart browser
                if retry_count >= 5:
                    print("⚠️ Multiple candidate row detection failures. Restarting browser...")
                    restart_browser()
                    driver.get(url)
                    browser_restart_count += 1
                    retry_count = 0
                    time.sleep(5)
                
                continue

            new_data = []

            for row in candidate_rows:
                try:
                    # Add explicit wait (using lambda function)
                    WebDriverWait(driver, 10).until(
                        lambda x: not EC.staleness_of(row)(x)
                    )
                    
                    candidate_id = row.get_attribute("id")
                    
                    try:
                        name_element = WebDriverWait(row, 10).until(
                            EC.presence_of_element_located((By.XPATH, './/span[contains(@class, "e1wnkr790")]'))
                        )
                        name = normalize_text(name_element.text.strip())
                    except:
                        print(f"⚠️ Cannot find name for candidate ID {row.get_attribute('id')}. Skipping.")
                        continue
                    
                    # Extract location information (newly added)
                    location = ""
                    try:
                        # Find location element (using class-based selector)
                        location_elements = row.find_elements(By.CSS_SELECTOR, 'span.css-14usd60.e1wnkr790')
                        if location_elements and len(location_elements) > 0:
                            location = normalize_text(location_elements[0].text.strip())
                        else:
                            # Try alternative XPath
                            location_element = row.find_element(By.XPATH, './/div[contains(@class, "css-1t6yw8")]/div[contains(@class, "css-1g97vp8")]/div/div[contains(@class, "css-opjyil")]/span')
                            if location_element:
                                location = normalize_text(location_element.text.strip())
                    except Exception as e:
                        print(f"⚠️ Cannot find location for candidate {name}: {e}")
                    
                    # Extract education information (newly added)
                    education = ""
                    try:
                        # Find education element (using class-based selector)
                        education_elements = row.find_elements(By.CSS_SELECTOR, 'div[data-cauto-id="qualifications-section-column"] div:nth-child(1) span.css-8vni6v.e1wnkr790')
                        if education_elements and len(education_elements) > 0:
                            education = normalize_text(education_elements[0].text.strip())
                        else:
                            # Try alternative XPath
                            education_element = row.find_element(By.XPATH, './/div[@data-cauto-id="qualifications-section-column"]//div[1]/span[2]')
                            if education_element:
                                education = normalize_text(education_element.text.strip())
                    except Exception as e:
                        print(f"⚠️ Cannot find education for candidate {name}: {e}")
                    
                    # Extract skills information (newly added)
                    skills = []
                    try:
                        # Find skill elements (using class-based selector)
                        skill_elements = row.find_elements(By.CSS_SELECTOR, 'div.css-1f1q1js.ecydgvn1')
                        for skill_element in skill_elements:
                            skill = normalize_text(skill_element.text.strip())
                            if skill:
                                skills.append(skill)
                    except Exception as e:
                        print(f"⚠️ Cannot find skills for candidate {name}: {e}")
                    
                    # Extract job title (newly added)
                    job_title = ""
                    try:
                        # Find job title element (using class-based selector)
                        job_title_elements = row.find_elements(By.CSS_SELECTOR, 'span.css-vc4n5s.e1wnkr790')
                        if job_title_elements and len(job_title_elements) > 0:
                            job_title = normalize_text(job_title_elements[0].text.strip())
                        else:
                            # Try alternative XPath
                            job_title_element = row.find_element(By.XPATH, './/div[contains(@class, "css-d641o9")]/div/ul/li[1]/div/span[1]')
                            if job_title_element:
                                job_title = normalize_text(job_title_element.text.strip())
                    except Exception as e:
                        print(f"⚠️ Cannot find job title for candidate {name}: {e}")
                    
                    # Extract company name and tenure (newly added)
                    company_text = ""
                    company_name = ""
                    tenure = ""
                    try:
                        # Find company element (using class-based selector)
                        company_elements = row.find_elements(By.CSS_SELECTOR, 'span.css-8vni6v.e1wnkr790')
                        if company_elements and len(company_elements) > 0:
                            company_text = normalize_text(company_elements[0].text.strip())
                        else:
                            # Try alternative XPath
                            company_element = row.find_element(By.XPATH, './/div[contains(@class, "css-d641o9")]/div/ul/li[1]/div/span[2]')
                            if company_element:
                                company_text = normalize_text(company_element.text.strip())
                        
                        # Separate company name and tenure
                        if company_text:
                            company_name, tenure = separate_company_tenure(company_text)
                    except Exception as e:
                        print(f"⚠️ Cannot find company name for candidate {name}: {e}")

                    if name and name not in [d['name'] for d in candidate_data]:
                        uri = f"http://www.indeed.com/r/{name.replace(' ', '+')}/{candidate_id}"
                        # Add job title, company name, tenure, location, education, skills
                        new_data.append({
                            'name': name, 
                            'indeed_id': candidate_id, 
                            'uri': uri,
                            'location': location,
                            'education': education,
                            'skills': ', '.join(skills) if skills else '',  # Add skills (comma separated)
                            'job_title': job_title,
                            'company_name': company_name,
                            'tenure': tenure
                        })
                        candidates_per_page += 1

                        # ✅ [Modified] Wait after collecting each name
                        time.sleep(random.uniform(0.5, 1.0))

                except Exception as e:
                    print(f"⚠️ Error extracting candidate information: {e}. Skipping.")
                    continue

            if not new_data:
                retry_count += 1
                time.sleep(2)
                continue

            candidate_data.extend(new_data)
            print(f"✅ Found {len(new_data)} new candidates. Total: {len(candidate_data)}")
            retry_count = 0

            # Periodically save data (every 20 candidates)
            if len(candidate_data) - last_save_count >= 20:
                try:
                    df = pd.DataFrame(candidate_data)
                    df['search_keyword'] = search_keyword
                    df.to_csv(output_file, index=False)
                    print(f"💾 Interim save: {len(candidate_data)} candidate records saved to {output_file}.")
                    last_save_count = len(candidate_data)
                except Exception as e:
                    print(f"Error saving data: {e}")

            # ✅ [Modified] Wait after scrolling
            try:
                # Check if the last element is still valid before scrolling
                if len(candidate_rows) > 0:
                    last_element = candidate_rows[-1]
                    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", last_element)
                    time.sleep(random.uniform(2.0, 3.0))
            except Exception as e:
                print(f"Error during scrolling: {e}")
                # Try refreshing the page if error occurs
                try:
                    driver.refresh()
                    time.sleep(5)
                    retry_count += 1
                    continue
                except:
                    pass

            if candidates_per_page >= 45:  # More flexible condition
                try:
                    # Add explicit wait with multiple selectors to find the Next button
                    try:
                        # Try the exact CSS selector provided by the user
                        next_button = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, "#app-root > div.css-1gorjcl.e37uo190 > div.css-lamjma.e37uo190 > div.css-13jgm14.e37uo190 > div.css-1yai4xz.eu4oa1w0 > div > main > div > div.css-1we8n3j.e37uo190 > div.css-wje6xa.eu4oa1w0 > div.css-1ghiswo.e37uo190 > div.css-wje6xa.eu4oa1w0 > div > div.css-1poky25.e37uo190 > div > div > button.css-1lmld4d.e8ju0x50"))
                        )
                        print("Found Next button using CSS selector")
                    except:
                        try:
                            # Try the exact XPath provided by the user
                            next_button = WebDriverWait(driver, 10).until(
                                EC.element_to_be_clickable((By.XPATH, "//*[@id='app-root']/div[3]/div[2]/div[2]/div[4]/div/main/div/div[4]/div[1]/div[2]/div[2]/div/div[3]/div/div/button[2]"))
                            )
                            print("Found Next button using XPath")
                        except:
                            # Try more generic selectors as fallback
                            try:
                                # Try to find by button text
                                next_button = WebDriverWait(driver, 10).until(
                                    EC.element_to_be_clickable((By.XPATH, "//button[span[text()='Next']]"))
                                )
                                print("Found Next button using text content")
                            except:
                                # Try to find by class name
                                next_button = WebDriverWait(driver, 10).until(
                                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button.css-1lmld4d.e8ju0x50"))
                                )
                                print("Found Next button using class name")
                    
                    if next_button:
                        print(f"➡️ Moving from page {page_number} to page {page_number+1}...")
                        
                        # Save current data before page transition (safety measure)
                        if candidate_data:
                            try:
                                df = pd.DataFrame(candidate_data)
                                df['search_keyword'] = search_keyword
                                df.to_csv(output_file, index=False)
                                print(f"💾 Pre-transition save: {len(candidate_data)} candidate records saved to {output_file}.")
                                last_save_count = len(candidate_data)
                            except Exception as e:
                                print(f"Error saving data: {e}")
                        
                        # Navigate to next page
                        next_button.click()
                        candidates_per_page = 0
                        page_number += 1

                        # ✅ [Modified] Increase wait time after page transition (to allow hCaptcha to appear)
                        time.sleep(random.uniform(6.0, 8.0))
                        retry_count = 0
                        
                        # Check for hCaptcha after page transition (commonly occurs during transitions)
                        print("Checking for hCaptcha after page transition...")
                        if check_for_hcaptcha():
                            print("\n" + "="*50)
                            print("🚨 hCaptcha detected after page transition! Please solve it manually in the browser window.")
                            print("⏰ Take your time. Press Enter when you're done.")
                            print("="*50 + "\n")
                            
                            # Give user time to solve the captcha
                            input("✅ Press Enter after solving the hCaptcha...")
                            
                            # After user presses Enter, assume hCaptcha is solved and continue
                            print("✅ Continuing after hCaptcha resolution...")
                            
                            # Force refresh the page to ensure hCaptcha is cleared
                            driver.refresh()
                            time.sleep(5)
                            
                            # Additional wait after captcha resolution
                            time.sleep(5)
                        else:
                            print("✅ No hCaptcha detected after page transition.")
                    else:
                        break
                except Exception as e:
                    print(f"Error clicking next page: {e}")
                    # Try refreshing the page if error occurs
                    try:
                        print("⚠️ Error navigating to next page. Refreshing and trying again...")
                        driver.refresh()
                        time.sleep(5)
                        retry_count += 1
                        
                        # Save current data before attempting to continue
                        if candidate_data:
                            try:
                                df = pd.DataFrame(candidate_data)
                                df['search_keyword'] = search_keyword
                                df.to_csv(output_file, index=False)
                                print(f"💾 Error recovery save: {len(candidate_data)} candidate records saved to {output_file}.")
                                last_save_count = len(candidate_data)
                            except Exception as save_error:
                                print(f"Error saving data during recovery: {save_error}")
                        
                        # If multiple failures, restart browser
                        if retry_count >= 3:
                            print("⚠️ Multiple navigation failures. Restarting browser...")
                            restart_browser()
                            driver.get(url)
                            browser_restart_count += 1
                            time.sleep(5)
                        
                        continue
                    except Exception as refresh_error:
                        print(f"Error during page refresh: {refresh_error}")
                        # Try restarting browser as last resort
                        restart_browser()
                        driver.get(url)
                        browser_restart_count += 1
                        time.sleep(5)
                        continue

        # Final data save
        if candidate_data:
            df = pd.DataFrame(candidate_data)
            df['search_keyword'] = search_keyword
            df.to_csv(output_file, index=False)
            print(f"✅ Final data saved to {output_file}. Total candidates: {len(candidate_data)}.")
        else:
            print("❌ No candidate data collected.")

        return candidate_data

    except Exception as e:
        print(f"Error: {e}")
        driver.save_screenshot("timeout_error.png")
        print("Screenshot saved to timeout_error.png.")
        
        # Save data collected before error occurred
        if len(candidate_data) > 0:
            try:
                df = pd.DataFrame(candidate_data)
                df['search_keyword'] = search_keyword
                output_file = search_keyword.replace(" ", "_") + "_scraped.csv"
                df.to_csv(output_file, index=False)
                print(f"⚠️ {len(candidate_data)} candidate records collected before error saved to {output_file}.")
            except Exception as save_error:
                print(f"Additional error while saving data after main error: {save_error}")
        
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

    save_cookies()
    # Provide search keyword selection options to the user
    print("\n===== Indeed Resume Scraping =====")
    print("Select a search keyword or enter your own:")
    print("1. Data Analyst")
    print("2. Business Analyst")
    print("3. Marketing Analyst")
    print("4. Custom Input")
    
    # Ask for target count
    print("\nHow many candidates do you want to scrape?")
    print("1. 100 candidates")
    print("2. 200 candidates")
    print("3. 500 candidates")
    print("4. 1000 candidates")
    print("5. Custom number")
    
    keyword_choice = input("\nEnter option number (1-4) for keyword: ")
    
    if keyword_choice == '1':
        search_keyword = "data analyst"
    elif keyword_choice == '2':
        search_keyword = "business analyst"
    elif keyword_choice == '3':
        search_keyword = "marketing analyst"
    elif keyword_choice == '4':
        search_keyword = input("Enter search keyword: ")
    else:
        print("Invalid selection. Using default 'business analyst'.")
        search_keyword = "business analyst"
    
    # Get target count from user
    count_choice = input("\nEnter option number (1-5) for number of candidates: ")
    
    if count_choice == '1':
        target_count = 100
    elif count_choice == '2':
        target_count = 200
    elif count_choice == '3':
        target_count = 500
    elif count_choice == '4':
        target_count = 1000
    elif count_choice == '5':
        try:
            target_count = int(input("Enter custom number of candidates to scrape: "))
            if target_count <= 0:
                print("Invalid number. Using default 200 candidates.")
                target_count = 200
        except ValueError:
            print("Invalid input. Using default 200 candidates.")
            target_count = 200
    else:
        print("Invalid selection. Using default 200 candidates.")
        target_count = 200
    
    print(f"\nSelected keyword: '{search_keyword}'")
    print(f"Target number of candidates: {target_count}")
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