import time
from selenium import webdriver
import os
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
import pickle  # For saving/loading cookies
# from selenium.webdriver.chrome.options import Options
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

# def fetch_name(url):
#     """
#     Fetches candidate names from the given URL and saves the results to a CSV.
#     """
#     try:
#         # driver.get(url)

#         # Wait for candidate rows to load
#         # WebDriverWait(driver, 50).until(
#         #     EC.presence_of_all_elements_located((By.XPATH, '//*[@class="css-1nqxi4r e1wnkr790"]'))
#         # )

#         # Keep scrolling until no new candidates are detected
#         # previous_count = 0
#         # while True:
#         #     # Scroll to the bottom of the page
#         #     driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
#         #     time.sleep(5)  # Wait for new content to load

#         #     # Get all candidate names
#         #     candidate_elements = driver.find_elements(By.XPATH, '//*[@data-cauto-id="candidate-name"]')
#         #     if len(candidate_elements) == previous_count:
#         #         # If no new candidates are loaded, break the loop
#         #         break
#         #     previous_count = len(candidate_elements)

#         # # Find all candidate names
#         # candidate_elements = driver.find_elements(By.XPATH, '//*[@class="css-1nqxi4r e1wnkr790"]')
#         # print(len(candidate_elements))

#         time.sleep(5)

#         # Get the full page source
#         page_source = driver.page_source

#         # Parse the page source with BeautifulSoup
#         soup = BeautifulSoup(page_source, "html.parser")

#         # Extract all candidate names using the appropriate selector
#         candidate_elements = soup.select('[data-cauto-id="candidate-name"]')

#         # Extract the text from each candidate element
#         candidate_names = [element.text.strip() for element in candidate_elements if element.text.strip()]

#         # Create a DataFrame from the extracted names
#         df = pd.DataFrame(candidate_names, columns=["Candidate Name"])
#         print(df)

#         # Save the DataFrame to a CSV file
#         output_file = "candidate_names.csv"
#         df.to_csv(output_file, index=False, encoding="utf-8")

#         print(f"Data saved to {output_file} with {len(candidate_names)} candidates.")
#         # return candidate_names
    
#     except Exception as e:
#         print(f"Error: {e}")

def fetch_name(url):
    """
    Fetches candidate names with incremental scrolling to trigger lazy loading
    """
    try:
        driver.get(url)
        candidate_names = []
        retry_count = 0
        max_retries = 5  # Stop after 5 failed attempts to find new candidates

        while retry_count < max_retries:
            # Wait for candidate elements to load
            WebDriverWait(driver, 15).until(
                EC.presence_of_all_elements_located((By.XPATH, '//*[@class="css-1nqxi4r e1wnkr790"]'))
            )

            # Get current batch of candidates
            current_elements = driver.find_elements(By.XPATH, '//*[@class="css-1nqxi4r e1wnkr790"]')
            new_names = [el.text.strip() for el in current_elements if el.text.strip() and el.text not in candidate_names]

            if not new_names:
                retry_count += 1
                time.sleep(1)
                continue

            # Add new names to list
            candidate_names.extend(new_names)
            print(f"Found {len(new_names)} new candidates. Total: {len(candidate_names)}")
            
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
            time.sleep(1.5)  # Adjust based on observed load times

        # Save results
        df = pd.DataFrame(candidate_names, columns=["Candidate Name"])
        df['search_keyword'] = "data engineer"
        output_file = "candidate_names.csv"
        df.to_csv(output_file, index=False)
        print(f"Data saved to {output_file} with {len(candidate_names)} candidates.")
        return candidate_names

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

def load_cookies_and_access_page():
    """ Load saved cookies and access a protected page. """
    driver.get("https://resumes.indeed.com/")  # Open Indeed homepage

    # Load cookies from file
    # try:
    with open(cookie_file, "rb") as file:
        cookies = pickle.load(file)
        for cookie in cookies:
            driver.add_cookie(cookie)
    print("Cookies loaded successfully!")

    driver.get("https://resumes.indeed.com/search?co=US&hl=en&q=data+engineer&l=&jk=&ek=&ts=1740199741480&start=0")

    # Wait to observe the loaded session
    time.sleep(5)
    print("Page loaded with cookies applied.")

def extract_candidate_pages(url):
    # Load the page
    # driver.get(url)  # Open Indeed homepage

    # Load cookies from file
    
    # with open(cookie_file, "rb") as file:
    #     cookies = pickle.load(file)
    #     for cookie in cookies:
    #         driver.add_cookie(cookie)
    # print("Cookies loaded successfully!")
    # driver.get(url)
    load_cookies_and_access_page()
    fetch_name(url)
    # return candidate_names

    # # # Allow the page to load
    # # WebDriverWait(driver, 10).until(
    # #     EC.presence_of_all_elements_located((By.XPATH, '//*[@data-cauto-id="candidate-row"]'))
    # # )

    # # # data-cauto-id="download_resume_action"
    # # # Find all candidate rows
    # # candidate_rows = driver.find_elements(By.XPATH, '//*[@data-cauto-id="candidate-row"]')

    # # candidate_pages_html = []

    # # # Iterate through each candidate row
    # # for index, row in enumerate(candidate_rows):
    # #     try:
    # #         # Click the row
    # #         row.click()

    # #         # Wait for the new content to load (adjust timing as necessary)
    # #         time.sleep(10)

    # #         # Get the new page source
    # #         page_source = driver.page_source

    # #         # Parse with BeautifulSoup
    # #         soup = BeautifulSoup(page_source, "html.parser")
            
    # #         # Store the HTML for further use
    # #         candidate_pages_html.append(soup.prettify())

    # #         close_button = WebDriverWait(driver, 10).until(
    # #         EC.presence_of_element_located((By.XPATH, '//*[@aria-label="Close Resume Preview"]'))
    # #         )

    # #         print("Close button found.")
        
    # #         # Simulate download (do not execute on real websites)
    # #         close_button.click()
    # #         break

    #         # # Optionally, navigate back if needed
    #         # driver.back()

    #         # Re-locate the rows again after navigating back (Selenium elements become stale)
    #         candidate_rows = driver.find_elements(By.XPATH, '//*[@data-cauto-id="candidate-row"]')
    #     except Exception as e:
    #         print(f"Error processing candidate {index + 1}: {e}")
    #         continue

    # return candidate_pages_html

def main():
    # URL of the job candidates page
    url = "https://resumes.indeed.com/search?co=US&hl=en&q=data+engineer&l=&jk=&ek=&ts=1740199741480&start=0"

    # Extract candidate page data
    # save_cookies()
    candidate_pages = extract_candidate_pages(url)

    # Save or process the extracted pages
    # for i, html in enumerate(candidate_pages):
    #     with open(f"candidate_{i + 1}.html", "w", encoding="utf-8") as file:
    #         file.write(html)

    if candidate_pages:
        print(f"Extracted {len(candidate_pages)} candidate pages")
    else:
        print("No candidates extracted.")

    # Close the WebDriver
    driver.quit()

if __name__ == "__main__":
    main()

# def interact_with_mock_website():
#     try:
#         # Navigate to a mock website (replace with your test URL)
#         driver.get("https://resumes.indeed.com/search?from=as&q=data+engineer&backUrl=https%3A%2F%2Fbilling.indeed.com%2Fo%2Fsingle-page%3FlinkSource%3Dnull%26continue%3Dhttps%253A%252F%252Fresumes.indeed.com%252Fsearch%253Ffrom%253Das%2526q%253Ddata%252520engineer%26registrationSessionRef%3Da8439fcf-26ac-4edd-b103-795249bc815b")
        
#         # table_data = driver.find_element(By.XPATH, '//*[@data-cauto-id="candidate-row"]')
#         # for data in table_data:
#         #     print(data.text)
#         # Wait for candidate row to load (example XPath)
#         candidate_row = WebDriverWait(driver, 10).until(
#             EC.presence_of_element_located((By.XPATH, '//*[@data-cauto-id="candidate-row"]'))
#         )
#         print("Candidate row found. Clicking...")
#         candidate_row.click()
        
#         # Wait for download button to appear after click
#         time.sleep(2)  # Simulate delay for UI to update
#         download_button = WebDriverWait(driver, 10).until(
#             EC.presence_of_element_located((By.XPATH, '//button[@aria-label="Download resume"]'))
#         )
#         print("Download button found.")
        
#         # Simulate download (do not execute on real websites)
#         download_button.click()
        
#     except Exception as e:
#         print(f"Error: {e}")
#     finally:
#         driver.quit()

# if __name__ == "__main__":
#     interact_with_mock_website()