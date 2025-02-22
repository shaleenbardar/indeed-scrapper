# import time
# import json
# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# import undetected_chromedriver as uc
# from selenium.webdriver.support import expected_conditions as EC
# from bs4 import BeautifulSoup
# import random

# # Configure Chrome options
# # chrome_options = Options()
# # chrome_options.add_argument("--headless")  # Run in headless mode
# # chrome_options.add_argument("--disable-software-rasterizer")
# # chrome_options.add_argument("--disable-webgl")
# # chrome_options.add_argument("--disable-gpu")
# # chrome_options.add_argument("--window-size=1920,1080")
# # chrome_options.add_argument("--disable-extensions")
# # chrome_options.add_argument("--no-sandbox")
# # chrome_options.add_argument("--disable-dev-shm-usage")
# # chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

# # # Initialize the WebDriver
# # driver = webdriver.Chrome(options=chrome_options)

# # def extract_resume_data(url):
# #     """
# #     Extracts candidate names and resume URLs from the given Indeed resume search page.
# #     """
# #     driver.get(url)
# #     time.sleep(5)  # Wait for the page to load

# #     # Wait for the resume list to load
# #     try:
# #         WebDriverWait(driver, 10).until(
# #             EC.presence_of_element_located((By.CLASS_NAME, "rezemp-ResumeSearchCard"))
# #         )
# #     except Exception as e:
# #         print(f"Error waiting for page to load: {e}")
# #         return []

# #     # Parse the page source with BeautifulSoup
# #     soup = BeautifulSoup(driver.page_source, "html.parser")
# #     resume_cards = soup.find_all("div", class_="rezemp-ResumeSearchCard")

# #     resumes = []

# #     for card in resume_cards:
# #         try:
# #             # Extract candidate name
# #             name = card.find("span", class_="rezemp-ResumeSearchCard-name").text.strip()
            
# #             # Extract resume URL
# #             resume_url = "https://resumes.indeed.com" + card.find("a", class_="icl-TextLink")["href"]
            
# #             # Append to the list
# #             resumes.append({
# #                 "name": name,
# #                 "resume_url": resume_url
# #             })
# #         except Exception as e:
# #             print(f"Error parsing resume card: {e}")
# #             continue

# #     return resumes

# # def save_to_json(data, filename="resumes.json"):
# #     """
# #     Saves the extracted data to a JSON file.
# #     """
# #     with open(filename, "w") as f:
# #         json.dump(data, f, indent=4)
# #     print(f"Data saved to {filename}")

# # def main():
# #     # URL of the Indeed resume search page
# #     url = "https://resumes.indeed.com/search?from=as&q=data+engineer&backUrl=https%3A%2F%2Fbilling.indeed.com%2Fo%2Fsingle-page%3FlinkSource%3Dnull%26continue%3Dhttps%253A%252F%252Fresumes.indeed.com%252Fsearch%253Ffrom%253Das%2526q%253Ddata%252520engineer%26registrationSessionRef%3Da8439fcf-26ac-4edd-b103-795249bc815b"

# #     # Extract resume data
# #     resumes = extract_resume_data(url)

# #     # Save the data to a JSON file
# #     save_to_json(resumes)

# #     # Close the WebDriver
# #     driver.quit()

# # if __name__ == "__main__":
# #     main()

# chrome_options = Options()
# chrome_options.add_argument("--headless")
# chrome_options.add_argument("--disable-gpu")
# chrome_options.add_argument("--disable-webgl")
# chrome_options.add_argument("--disable-software-rasterizer")
# chrome_options.add_argument("--disable-extensions")
# chrome_options.add_argument("--disable-features=VizDisplayCompositor")

# import random

# headers = {
#     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
#     "Accept-Language": "en-US,en;q=0.9",
#     "Referer": "https://www.google.com"
# }

# # Random delay before extracting data
# time.sleep(random.randint(3, 8))

# # Initialize WebDriver
# # driver = webdriver.Chrome(options=chrome_options)
# driver = uc.Chrome(options=chrome_options)


# driver.execute_cdp_cmd("Network.setExtraHTTPHeaders", {"headers": headers})

# def extract_resume_data(url):
#     driver.get(url)
#     time.sleep(random.randint(3, 8))  # Random delay

#     try:
#         WebDriverWait(driver, 20).until(
#             EC.visibility_of_element_located((By.CLASS_NAME, "rezemp-ResumeSearchCard"))
#         )
#     except Exception as e:
#         print(f"Error waiting for page to load: {e}")
#         return []

#     soup = BeautifulSoup(driver.page_source, "html.parser")
#     resume_cards = soup.find_all("div", class_="rezemp-ResumeSearchCard")

#     resumes = []
#     for card in resume_cards:
#         try:
#             name = card.find("span", class_="rezemp-ResumeSearchCard-name").text.strip()
#             resume_url = "https://resumes.indeed.com" + card.find("a", class_="icl-TextLink")["href"]
#             resumes.append({"name": name, "resume_url": resume_url})
#         except Exception as e:
#             print(f"Error parsing resume card: {e}")
#             continue

#     return resumes

# def save_to_json(data, filename="resumes.json"):
#     with open(filename, "w") as f:
#         json.dump(data, f, indent=4)
#     print(f"Data saved to {filename}")

# def main():
#     url = "https://resumes.indeed.com/search?from=as&q=data+engineer"
#     resumes = extract_resume_data(url)
#     save_to_json(resumes)
#     driver.quit()

# if __name__ == "__main__":
#     main()




import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

# Configure Chrome options
chrome_options = Options()
# chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--disable-webgl")
chrome_options.add_argument("--disable-software-rasterizer")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--disable-features=VizDisplayCompositor")
# Initialize the WebDriver
driver = webdriver.Chrome(options=chrome_options)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com"
}


driver.execute_cdp_cmd("Network.setExtraHTTPHeaders", {"headers": headers})

def extract_resume_data(url):
    """
    Extracts candidate names and resume URLs from the given Indeed resume search page.
    """
    print(f"Navigating to URL: {url}")
    driver.get(url)
    time.sleep(5)  # Wait for the page to load

    # Debug: Save the page source to a file for inspection
    with open("page_source.html", "w", encoding="utf-8") as f:
        f.write(driver.page_source)

    # # Wait for the resume list to load
    # try:
    #     print("Waiting for resume cards to load...")
    #     WebDriverWait(driver, 10).until(
    #         EC.presence_of_element_located((By.CLASS_NAME, "rezemp-ResumeSearchCard"))
    #     )
    # except Exception as e:
    #     print(f"Error waiting for page to load: {e}")
    #     return []

    # Parse the page source with BeautifulSoup
    soup = BeautifulSoup(driver.page_source, "html.parser")
    resume_cards = soup.find_all("div", class_="rezemp-ResumeSearchCard")

    resumes = []

    for card in resume_cards:
        try:
            # Extract candidate name
            name = card.find("span", class_="rezemp-ResumeSearchCard-name").text.strip()
            
            # Extract resume URL
            resume_url = "https://resumes.indeed.com" + card.find("a", class_="icl-TextLink")["href"]
            
            # Append to the list
            resumes.append({
                "name": name,
                "resume_url": resume_url
            })
            print(f"Extracted: {name} - {resume_url}")
        except Exception as e:
            print(f"Error parsing resume card: {e}")
            continue

    return resumes

def save_to_json(data, filename="resumes.json"):
    """
    Saves the extracted data to a JSON file.
    """
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)
    print(f"Data saved to {filename}")

def main():
    # URL of the Indeed resume search page
    url = "https://resumes.indeed.com/search?from=as&q=data+engineer&backUrl=https%3A%2F%2Fbilling.indeed.com%2Fo%2Fsingle-page%3FlinkSource%3Dnull%26continue%3Dhttps%253A%252F%252Fresumes.indeed.com%252Fsearch%253Ffrom%253Das%2526q%253Ddata%252520engineer%26registrationSessionRef%3Da8439fcf-26ac-4edd-b103-795249bc815b"

    # Extract resume data
    resumes = extract_resume_data(url)

    # Save the data to a JSON file
    save_to_json(resumes)

    # Close the WebDriver
    driver.quit()

if __name__ == "__main__":
    main()