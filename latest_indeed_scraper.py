# import time
# import os
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC

# # Configure Chrome to download files automatically
# download_dir = os.path.abspath("./downloads")  # Set your download directory
# os.makedirs(download_dir, exist_ok=True)

# chrome_options = webdriver.ChromeOptions()
# prefs = {
#     "download.default_directory": download_dir,
#     "download.prompt_for_download": False,
#     "download.directory_upgrade": True,
#     "plugins.always_open_pdf_externally": True  # Auto-open PDFs
# }
# chrome_options.add_experimental_option("prefs", prefs)
# # chrome_options.add_argument("--headless")  # Run in headless mode
# chrome_options.add_argument("--disable-gpu")
# chrome_options.add_argument("--disable-webgl")
# chrome_options.add_argument("--disable-software-rasterizer")
# chrome_options.add_argument("--disable-extensions")
# chrome_options.add_argument("--disable-features=VizDisplayCompositor")

# driver = webdriver.Chrome(options=chrome_options)

# headers = {
#     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
#     "Accept-Language": "en-US,en;q=0.9",
#     "Referer": "https://www.google.com"
# }


# driver.execute_cdp_cmd("Network.setExtraHTTPHeaders", {"headers": headers})

# def download_resume(url):
#     try:
#         driver.get(url)
#         print(f"Navigated to: {url}")

#         # Wait for the download button to appear (adjust timeout as needed)
#         download_button = WebDriverWait(driver, 10).until(
#             EC.presence_of_element_located((By.XPATH, '/html/body/div[7]/div[1]/div[2]/div/div[2]/div/div/div[2]/div[2]/button[3]'))
#         )
#         print("Found download button.")

#         # Click the button to trigger the download
#         download_button.click()
#         print("Download initiated. Waiting 5 seconds...")
#         time.sleep(5)  # Allow time for the download to complete

#     except Exception as e:
#         print(f"Error: {e}")

# def main():
#     # Example URL (replace with a test page for educational purposes)
#     # test_url = "https://example.com/resume-page"
#     url = url = "https://resumes.indeed.com/search?from=as&q=data+engineer&backUrl=https%3A%2F%2Fbilling.indeed.com%2Fo%2Fsingle-page%3FlinkSource%3Dnull%26continue%3Dhttps%253A%252F%252Fresumes.indeed.com%252Fsearch%253Ffrom%253Das%2526q%253Ddata%252520engineer%26registrationSessionRef%3Da8439fcf-26ac-4edd-b103-795249bc815b"  # Do not use Indeed's URL
#     download_resume(url)
#     driver.quit()

# if __name__ == "__main__":
#     main()




import time
import os
import pandas as pd  # Import pandas for DataFrame handling
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configure Chrome to download files automatically
download_dir = os.path.abspath("./downloads")  # Set your download directory
os.makedirs(download_dir, exist_ok=True)

chrome_options = webdriver.ChromeOptions()
prefs = {
    "download.default_directory": download_dir,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "plugins.always_open_pdf_externally": True  # Auto-open PDFs
}
chrome_options.add_experimental_option("prefs", prefs)
# chrome_options.add_argument("--headless")  # Run in headless mode if needed
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--disable-webgl")
chrome_options.add_argument("--disable-software-rasterizer")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--disable-features=VizDisplayCompositor")

driver = webdriver.Chrome(options=chrome_options)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com"
}

driver.execute_cdp_cmd("Network.setExtraHTTPHeaders", {"headers": headers})

def fetch_name(url):
    """
    Fetches candidate names from the given URL and saves the results to a CSV.
    """
    try:
        driver.get(url)

        # Wait for candidate rows to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, '//*[@class="css-1nqxi4r e1wnkr790"]'))
        )

        # Find all candidate names
        candidate_elements = driver.find_elements(By.XPATH, '//*[@class="css-1nqxi4r e1wnkr790"]')

        # Extract the text from each candidate element
        candidate_names = [element.text.strip() for element in candidate_elements if element.text.strip()]

        # Create a DataFrame from the extracted names
        df = pd.DataFrame(candidate_names, columns=["Candidate Name"])

        # Save the DataFrame to a CSV file
        output_file = "candidate_names.csv"
        df.to_csv(output_file, index=False, encoding="utf-8")

        print(f"Data saved to {output_file} with {len(candidate_names)} candidates.")
    
    except Exception as e:
        print(f"Error: {e}")

def main():
    # Example URL (replace with a test page for educational purposes)
    url = "https://resumes.indeed.com/search?from=as&q=data+engineer&backUrl=https%3A%2F%2Fbilling.indeed.com%2Fo%2Fsingle-page%3FlinkSource%3Dnull%26continue%3Dhttps%253A%252F%252Fresumes.indeed.com%252Fsearch%253Ffrom%253Das%2526q%253Ddata%252520engineer%26registrationSessionRef%3Da8439fcf-26ac-4edd-b103-795249bc815b"  # Do not use Indeed's URL
    fetch_name(url)
    driver.quit()

if __name__ == "__main__":
    main()
