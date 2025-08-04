import hashlib
import os
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
from collections import defaultdict
from typing import List, Dict
from bs4 import Tag

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

def get_snapshot_filename(url: str, directory: str = "snapshots") -> str:
    """
    Generate a unique filename for the snapshot based on the URL hash.
    """
    os.makedirs(directory, exist_ok=True)
    return os.path.join(directory, f"{hashlib.md5(url.encode()).hexdigest()}.html")

# ─── Helpers for PDF-style spans ───────────────────────────────────────────────


_STOP_HEADERS = [
    "Professional Summary",
    "Professional Experience",
    "Work Experience",
    "Experience",
    "Technical Skills",
    "Skills",
    "Certifications",
    # "Projects"
]

# allow optional punctuation/non-word chars before the section name
_STOP_RX = re.compile(
    r'^[^\w]*(' + '|'.join(re.escape(h) for h in _STOP_HEADERS) + r')\b',
    re.IGNORECASE
)

def _merge_fragments(lines: List[str]) -> List[str]:
    merged = []
    i = 0
    while i < len(lines):
        ln = lines[i].strip()
        if len(ln) == 1 and i + 1 < len(lines):
            merged.append(ln + lines[i+1].strip())
            i += 2
        else:
            merged.append(ln)
            i += 1
    return merged

def _extract_block(lines: List[str], header_rx: re.Pattern) -> str:
    """
    Find the first line matching header_rx, then collect all subsequent lines
    until we hit any line that _STOP_RX matches.
    """
    # drop truly empty lines, then re-merge hyphens
    clean = [l for l in lines if l.strip()]
    clean = _merge_fragments(clean)

    # find where our block starts
    start = next((i for i, ln in enumerate(clean) if header_rx.match(ln)), None)
    if start is None:
        return ""

    out = []
    for ln in clean[start+1:]:
        if _STOP_RX.match(ln):
            break
        out.append(ln)
    return " ".join(out).strip()

def extract_skills_text(lines: List[str]) -> str:
    """
    Extract everything under "Skills" or "Technical Skills", stopping
    once a new section header appears (even if it's on the same line).
    """
    header_rx = re.compile(r'^[^\w]*(?:Skills|Technical Skills)\b', re.IGNORECASE)
    return _extract_block(lines, header_rx)

def extract_experience_text(lines: List[str]) -> str:
    """
    Extract everything under Experience / Work Experience / Professional Experience,
    stopping at the next section header (even if it's punctuated).
    """
    header_rx = re.compile(
        r'^[^\w]*(?:Professional Experience|PROFESSIONAL EXPERIENCE|ROFESSIONAL EXPERIENCE|Work Experience|EXPERIENCE|Experience|PROFESSIONAL EXPERIENCE|WORK EXPERIENCE|Experien)\b',
        re.IGNORECASE
    )
    return _extract_block(lines, header_rx)

# _STOP_HEADERS = [
#     "Professional Summary", "EXPERIENCE", "PROFESSIONAL EXPERIENCE",
#     "Professional Experience", "Work Experience", "Experience", "Technical Skills", "Skills", "Certifications"
# ]
# _STOP_RX = re.compile(
#     r'^(?:' + r'|'.join(map(re.escape, _STOP_HEADERS)) + r')\:?\s*$',
#     re.IGNORECASE
# )

# def _merge_fragments(lines: List[str]) -> List[str]:
#     merged, i = [], 0
#     while i < len(lines):
#         ln = lines[i].strip()
#         if len(ln) == 1 and i+1 < len(lines):
#             merged.append(ln + lines[i+1].strip())
#             i += 2
#         else:
#             merged.append(ln)
#             i += 1
#     return merged

# def _extract_block(lines: List[str], header_rx: re.Pattern) -> str:
#     lines = _merge_fragments([l for l in lines if l.strip()])
#     idx = next((i for i,l in enumerate(lines) if header_rx.match(l)), None)
#     if idx is None:
#         return ""
#     out = []
#     for ln in lines[idx+1:]:
#         if _STOP_RX.match(ln):
#             break
#         out.append(ln)
#     return " ".join(out).strip()

def extract_summary_text(lines: List[str]) -> str:
    return _extract_block(lines, re.compile(r'^(?:Professional Summary|SUMMARY|Summary|Personal Summary)\:?\s*$', re.I))

# def extract_experience_text(lines: List[str]) -> str:
#     return _extract_block(
#         lines,
#         re.compile(r'^(?:Professional Experience|PROFESSIONAL EXPERIENCE|ROFESSIONAL EXPERIENCE|Work Experience|EXPERIENCE|Experience|PROFESSIONAL EXPERIENCE|WORK EXPERIENCE|Experien)\:?\s*$', re.I)
#     )

# def extract_skills_text(lines: List[str]) -> str:
#     return _extract_block(
#         lines,
#         re.compile(r'^(?:Skills|Technical Skills)\:?\s*$', re.I)
#     )
    # lines = _merge_fragments([l for l in lines if l.strip()])
    # rx = re.compile(r'^(?:Skills|Technical Skills)\:?\s*$', re.I)
    # idx = next((i for i,l in enumerate(lines) if rx.match(l)), None)
    # if idx is None:
    #     return ""
    # out = []
    # for ln in lines[idx+1:]:
    #     if _STOP_RX.match(ln) and not rx.match(ln):
    #         break
    #     out.append(ln)
    # return ", ".join(out).strip()

def extract_certifications_text(lines: List[str]) -> str:
    return _extract_block(
        lines,
        re.compile(r'^(?:Certifications|Certifications and Licenses)\:?\s*$', re.I)
    )

def extract_education_text(lines: List[str]) -> str:
    """
    Extracts the Education section from a list of text lines (from PDF-style spans).

    Args:
        lines: List of strings, each one a line of text extracted from spans.

    Returns:
        A single string containing all lines under the Education heading, joined by spaces.
        Returns an empty string if no Education header is found.
    """
    # same underlying block extractor you used for summary/experience/etc.
    return _extract_block(
        lines,
        re.compile(r'^Education\:?\s*$', re.I)
    )

# ─── Helper for div-based layout ──────────────────────────────────────────────

def extract_div_section(soup: BeautifulSoup, *hdrs: str) -> str:
    rx = re.compile(r'^(?:' + r'|'.join(map(re.escape, hdrs)) + r')\s*$', re.I)
    h2 = soup.find("h2", string=rx)
    if not h2:
        return ""
    wrapper = h2.find_parent("div", class_="section_title")
    if not wrapper or not wrapper.parent:
        return ""
    out = []
    for sib in wrapper.parent.find_next_siblings():
        if sib.find("h2", class_="section_header_title"):
            break
        txt = sib.get_text(" ", strip=True)
        if txt:
            out.append(txt)
    return "\n".join(out).strip()

# ─── Main extractor ──────────────────────────────────────────────────────────

def extract_resume_data(url: str, driver) -> Dict[str, str]:
    # 1) Define the exact columns we want, in order
    columns = [
        "Name", "Location",
        "Professional Summary", "Skills", "Certifications",
        "Education", "Professional Experience", "Links", "Projects"
    ]
    data = {col: "" for col in columns}

    # 2) Load or cache snapshot
    snap = get_snapshot_filename(url)
    if os.path.exists(snap):
        with open(snap, encoding="utf-8") as f:
            html = f.read()
    else:
        load_cookies_and_access_page(url)
        wait_for_resume_load(driver)
        html = driver.page_source
        with open(snap, "w", encoding="utf-8") as f:
            f.write(html)

    soup = BeautifulSoup(html, "html.parser")

    banner = soup.select_one("span.css-18tk8px.e1wnkr790")
    if banner and "this resume is unavailable" in banner.get_text(" ", strip=True).lower():
        print(f"Skipping unavailable resume {url}")
        return None  # no data for this URL

    # tiny helper
    def safe(sel: str) -> str:
        el = soup.select_one(sel)
        return el.get_text(" ", strip=True) if el else ""

    # ── 3) Iframe path ────────────────────────────────────────────────────────
    iframe = soup.select_one("iframe[name='resume_frame']")
    if iframe and iframe.has_attr("srcdoc"):
        inner = BeautifulSoup(iframe["srcdoc"], "html.parser")
        # now reset soup/selectors to inner
        soup = inner

        data["Name"] = safe("#basic_info_cell h1.fn")
        # data["Headline"] = safe("h2#headline")
        # data["Location"] = safe("div.locality")
        data["Professional Summary"] = safe("p#res_summary")

        # experience
        exp_items = []
        for it in soup.select("#work-experience-items div.work-experience-section"):
            t = it.select_one("h3[data-shield-id='workExperience_work_title']")
            d = it.select_one("div[data-shield-id='workExperience_work_dates']")
            p = it.select_one("p[data-shield-id='workExperience_work_description']")
            if t and d:
                txt = f"{t.get_text(strip=True)} ({d.get_text(strip=True)})"
                if p:
                    txt += "\n" + p.get_text(" ", strip=True)
                exp_items.append(txt)
        data["Professional Experience"] = ". ".join(exp_items)

        # skills, certs, education, links, projects from the same iframe HTML
        data["Skills"] = ", ".join(
            [s.get_text(strip=True) for s in soup.select("span.skill-text")]
        )
        certs = []
        for c in soup.select("div.certification-section"):
            t = c.select_one("div.certification_title")
            d = c.select_one("div.certification_date")
            x = c.select_one("p.certification_description")
            certs.append(" | ".join(p.strip() for p in (
                t.get_text(strip=True) if t else "",
                d.get_text(strip=True) if d else "",
                x.get_text(" ", strip=True) if x else ""
            ) if p))
        data["Certifications"] = ". ".join(certs)

        edus = []
        for e in soup.select("div.education-section"):
            t = e.select_one("h3.edu_title")
            sch = e.select_one("span[data-shield-id='education_edu_school_span']")
            loc = e.select_one("span[data-shield-id='education_edu_location_span']")
            dt = e.select_one("div[data-shield-id='education_edu_dates']")
            edus.append(" | ".join(p.strip() for p in (
                t.get_text(strip=True) if t else "",
                sch.get_text(strip=True) if sch else "",
                loc.get_text(strip=True) if loc else "",
                dt.get_text(strip=True) if dt else ""
            ) if p))
        data["Education"] = ". ".join(edus)

        link = soup.select_one("div.link_url a[href]")
        data["Links"] = link["href"] if link else ""

        # projects if any
        data["Projects"] = "\n".join(
            [pr.get_text(" ", strip=True) for pr in soup.select("div.project-section")]
        )

        return data

    # ── 4) PDF spans fallback ────────────────────────────────────────────────
    spans = soup.select("div.react-pdf__Page__textContent span[role='presentation']")
    if spans:
        raw = [s.text for s in spans if s.text.strip()]
        data["Name"] = next((l for l in raw if l.isupper() and len(l.split()) > 1), "")

        data["Professional Summary"]    = extract_summary_text(raw)
        data["Professional Experience"] = extract_experience_text(raw)
        data["Skills"]                  = extract_skills_text(raw)
        data["Certifications"]          = extract_certifications_text(raw)
        data["Education"]               = extract_education_text(raw)
        # PDF layout typically has no Headline, Location, Education, Links, Projects
        return data

    # ── 5) Div‐based layout fallback ─────────────────────────────────────────
    data["Name"]     = safe("h1#resume-contact")
    # data["Headline"] = safe("h2#headline")
    data["Location"] = safe("div.locality")

    # summary
    val = safe("p#res_summary")
    if not val:
        val = extract_div_section(soup, "Professional Summary")
    data["Professional Summary"] = val

    # skills
    val = extract_div_section(soup, "Technical Skills")
    if not val:
        val = extract_div_section(soup, "Skills")
        if not val:
            val = ", ".join([s.get_text(strip=True) for s in soup.select("span.skill-text")])
    data["Skills"] = val

    data["Certifications"] = extract_div_section(
        soup, "Certifications and Licenses", "Certifications"
    )
    data["Links"]          = safe("div.link_url a[href]")
    data["Education"]      = extract_div_section(soup, "Education")

    data["Professional Experience"] = (
        extract_div_section(soup, "Work Experience")
        or extract_div_section(soup, "Professional Experience")
    )

    data["Projects"] = extract_div_section(soup, "Projects")
    return data

def main():
    # uncomment to generate cookies file first time
    #save_cookies()
    # urls = [
    #     "https://resumes.indeed.com/resume/cb459e5ab31ac6de",
    #     "https://resumes.indeed.com/resume/b4e1db87188298c3",
    #     "https://resumes.indeed.com/resume/f36ea98f57095137",
    #     "https://resumes.indeed.com/resume/7ff20f7be9e91432",
    #     "http://www.indeed.com/r/AISHWARYA+NARAYAN/1e703856a93abfd6",
    #     "http://www.indeed.com/r/Aishvarya+Konda/e3df3e393d2bae62",
    #     "http://www.indeed.com/r/Ajay+More/330425801877e902",
    #     "http://www.indeed.com/r/Adwaith+Thampi/3e582328bb534464",
    #     "http://www.indeed.com/r/ADITI+GHANATHE/ed2c4473dccbf092",
    #     "http://www.indeed.com/r/ADITHYA+BURRA/75ba29209b251b3b"
    # ]
    # all_rows = []
    # for url in urls:
    #     try:
    #         row = extract_resume_data(url, driver)  # ✅ Pass `driver` here
    #         row["URL"] = url
    #         all_rows.append(row)
    #     except TimeoutException as e:
    #         print(f"Timeout loading {url}: {e}")
    #     except Exception as e:
    #         print(f"Failed to scrape {url}: {e}")
    # df = pd.DataFrame(all_rows)
    # df.to_csv("resumes.csv", index=False, encoding="utf-8")
    # print(f"Written {len(all_rows)} rows to resumes.csv")
    # driver.quit()

    
    # 1) Read original CSV with the columns we need
    df_orig = pd.read_csv("resumes_parsed_X.csv", dtype=str)
    # Strip whitespace & drop rows without a URI
    df_orig["indeed_uri"] = df_orig["indeed_uri"].str.strip()
    df_orig = df_orig.dropna(subset=["indeed_uri"])

    # 2) Only process the first 10 URIs
    df_slice = df_orig.iloc[40:50].copy()

    all_rows = []
    for _, orig in df_slice.iterrows():
        url = orig["indeed_uri"]
        try:
            scraped = extract_resume_data(url, driver)
            time.sleep(5)
        except TimeoutException as e:
            print(f"Timeout loading {url}: {e}")
            continue
        except Exception as e:
            print(f"Failed to scrape {url}: {e}")
            continue

        # 3) Combine original columns + computed names + scraped fields
        name = orig.get("name", "").strip()
        parts = name.split()
        row = {
            "resume_pdf_filename": orig.get("resume_pdf_filename", ""),
            "search_keyword":        orig.get("search_keyword", ""),
            "indeed_id":             orig.get("indeed_id", ""),
            "indeed_uri":            url,
            "name":                  name,
            "first_name":            parts[0] if parts else "",
            "last_name":             parts[-1] if parts else "",
            "resume_name":           name,
            "city":                  orig.get("city", ""),
            "state":                 orig.get("state", ""),
            "professional experience": scraped.get("Professional Experience", ""),
            "education":               scraped.get("Education", ""),
            "professional summary":    scraped.get("Professional Summary", ""),
            "skills":                  scraped.get("Skills", ""),
            "links":                   scraped.get("Links", ""),
        }

        all_rows.append(row)

    # 4) Build output DataFrame in the exact column order required
    out_cols = [
        "resume_pdf_filename",
        "search_keyword",
        "indeed_id",
        "indeed_uri",
        "name",
        "first_name",
        "last_name",
        "resume_name",
        "city",
        "state",
        "professional experience",
        "education",
        "professional summary",
        "skills",
        "links",
    ]
    df_out = pd.DataFrame(all_rows, columns=out_cols)

    # 5) Write to new CSV
    df_out.to_csv("candidates_without_emails.csv", mode='a', header=False, index=False, encoding="utf-8")
    print(f"Written {len(df_out)} rows to candidates_without_emails.csv")

    driver.quit()

if __name__ == "__main__":
    main()