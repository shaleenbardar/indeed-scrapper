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

def extract_sections_from_spans(html: str, headings: List[str]) -> Dict[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    spans = soup.select("div.react-pdf__Page__textContent span[role='presentation']")

    lines_by_top = defaultdict(list)
    for span in spans:
        style = span.get("style", "")
        top_match = re.search(r"top:\s*([\d.]+)%", style)
        if top_match:
            top = float(top_match.group(1))
            text = span.get_text(strip=True)
            if text:
                lines_by_top[round(top, 2)].append(text)

    sorted_lines = [(top, " ".join(lines_by_top[top])) for top in sorted(lines_by_top)]

    heading_rx = re.compile(
        r"^(?:" + "|".join(re.escape(h).replace(r"\ ", r"\s*") for h in headings) + r")\s*:?\s*$",
        re.IGNORECASE
    )

    sections = {}
    current_heading = None
    current_lines = []
    name_found = None

    for _, line in sorted_lines:
        if not name_found and line.isupper() and len(line.split()) >= 2:
            name_found = line.strip()
        if heading_rx.match(line):
            if current_heading:
                sections[current_heading] = "\n".join(current_lines).strip()
                current_lines.clear()
            current_heading = line.strip()
        elif current_heading:
            current_lines.append(line)

    if current_heading and current_lines:
        sections[current_heading] = "\n".join(current_lines).strip()

    if name_found:
        sections["Name"] = name_found

    return sections


# def extract_resume_data(url: str, driver) -> Dict[str, str]:
#     """
#     Extract structured resume data from a snapshot or live Indeed resume page.
    
#     Args:
#         url (str): Resume URL.
#         driver: Selenium WebDriver instance.
    
#     Returns:
#         Dict[str, str]: Extracted resume data under various headings.
#     """
#     snapshot_file = get_snapshot_filename(url)
#     if os.path.exists(snapshot_file):
#         print(f"Loading snapshot from {snapshot_file}")
#         with open(snapshot_file, "r", encoding="utf-8") as file:
#             html = file.read()
#     else:
#         load_cookies_and_access_page(url)
#         wait_for_resume_load(driver)

#         html = driver.page_source
#         with open(snapshot_file, "w", encoding="utf-8") as file:
#             file.write(html)
#         print(f"Snapshot saved to {snapshot_file}")

#     # Extract PDF-style spans content
#     headings = [
#         "PROFESSIONAL SUMMARY",
#         "TECHNICAL SKILLS",
#         "PROFESSIONAL EXPERIENCE",
#         "WORK EXPERIENCE",
#         "CERTIFICATIONS",
#         "EDUCATION",
#         "SKILLS",
#         "PROJECTS"
#     ]
#     return extract_sections_from_spans(html, headings)

import re
from typing import List

# # All section headers we want to stop at
# STOP_HEADERS = [
#     "Professional Summary",
#     "Technical Skills",
#     "Professional Experience",
#     "Work Experience",
#     "Experience",
#     "Education",
#     "Skills",
#     "Certifications",
#     "Projects"
# ]
# STOP_SECTIONS_RX = re.compile(
#     r'^(?:' + r'|'.join(re.escape(h) for h in STOP_HEADERS) + r'):?\s*$',
#     re.IGNORECASE
# )

# def _merge_fragments(lines: List[str]) -> List[str]:
#     """
#     Merge single-letter lines with the next line, to fix broken spans like:
#       ['P', 'ROFESSIONAL SUMMARY', ...]
#     """
#     merged = []
#     i = 0
#     while i < len(lines):
#         ln = lines[i].strip()
#         if len(ln) == 1 and i + 1 < len(lines) and lines[i+1].strip():
#             # join the single letter with the next
#             merged.append(ln + lines[i+1].strip())
#             i += 2
#         else:
#             merged.append(ln)
#             i += 1
#     return merged

# def extract_summary_text(lines: List[str]) -> str:
#     """
#     Extracts everything under 'Professional Summary' until the next header.
#     """
#     lines = _merge_fragments(lines)
#     header_rx = re.compile(r'^Professional Summary:?\s*$', re.IGNORECASE)

#     # find start
#     idx = next((i for i, ln in enumerate(lines) if header_rx.match(ln)), None)
#     if idx is None:
#         return ""
#     summary = []
#     for ln in lines[idx+1:]:
#         if STOP_SECTIONS_RX.match(ln):
#             break
#         summary.append(ln)
#     return " ".join(summary).strip()

# def extract_technical_skills_text(lines: List[str]) -> str:
#     """
#     Extracts everything under 'Technical Skills' until the next header.
#     """
#     lines = _merge_fragments(lines)
#     header_rx = re.compile(r'^Technical Skills:?\s*$', re.IGNORECASE)

#     idx = next((i for i, ln in enumerate(lines) if header_rx.match(ln)), None)
#     if idx is None:
#         return ""
#     tech = []
#     for ln in lines[idx+1:]:
#         if STOP_SECTIONS_RX.match(ln):
#             break
#         tech.append(ln)
#     # join with comma
#     return ", ".join(tech).strip()

# def extract_skills_text(lines: List[str]) -> str:
#     """
#     Extracts everything under 'Skills' until the next header.
#     """
#     lines = _merge_fragments(lines)
#     header_rx = re.compile(r'^Skills:?\s*$', re.IGNORECASE)

#     idx = next((i for i, ln in enumerate(lines) if header_rx.match(ln)), None)
#     if idx is None:
#         return ""
#     skills = []
#     for ln in lines[idx+1:]:
#         if STOP_SECTIONS_RX.match(ln):
#             break
#         skills.append(ln)
#     return ", ".join(skills).strip()

# def extract_certifications_text(lines: List[str]) -> str:
#     """
#     Extracts everything under 'Certifications' until the next header.
#     """
#     lines = _merge_fragments(lines)
#     header_rx = re.compile(r'^(?:Certifications|Certifications and Licenses):?\s*$', re.IGNORECASE)

#     idx = next((i for i, ln in enumerate(lines) if header_rx.match(ln)), None)
#     if idx is None:
#         return ""
#     certs = []
#     for ln in lines[idx+1:]:
#         if STOP_SECTIONS_RX.match(ln):
#             break
#         certs.append(ln)
#     return " | ".join(certs).strip()

# def extract_experience_text(lines: List[str]) -> str:
#     """
#     Extracts the Experience section from a list of text lines (from PDF-style spans).

#     Args:
#         lines: List of strings, each one a line of text extracted from spans.

#     Returns:
#         A single string containing all lines under the Experience heading, joined by newlines.
#         Returns an empty string if no Experience header is found.
#     """
#     # Match the exact headings (case-insensitive)
#     print("Extracting experience text from lines...")
#     lines = [ln.strip() for ln in lines if ln.strip()]  # Clean up empty lines
#     print(f"Total lines to process: {lines}")
#     header_rx = re.compile(r'^(Professional Experience|ROFESSIONAL EXPERIENCE|Work Experience|Experience)\s*$', re.I)

#     # Find the index of the heading
#     start_idx = next((i for i, ln in enumerate(lines) if header_rx.match(ln.strip())), None)
#     if start_idx is None:
#         return ""

#     exp_lines = []
#     # Collect all lines until we hit a new section (e.g. "Education:" or "Skills:")
#     for ln in lines[start_idx + 1:]:
#         ln_strip = ln.strip()
#         # stop if we see a line that looks like a new section header
#         if re.match(r'^[A-Za-z &]+:$', ln_strip):
#             break
#         exp_lines.append(ln_strip)

#     return " ".join(exp_lines).strip()

#working code 
# def _merge_fragments(lines: List[str]) -> List[str]:
#     """
#     Merge single-letter fragments with the next line, e.g.:
#       ['P', 'ROFESSIONAL SUMMARY', ...] → ['PROFESSIONAL SUMMARY', ...]
#     """
#     merged = []
#     i = 0
#     while i < len(lines):
#         ln = lines[i].strip()
#         # if it's a single character and next line exists, merge them
#         if len(ln) == 1 and i + 1 < len(lines):
#             merged.append(ln + lines[i + 1].strip())
#             i += 2
#         else:
#             merged.append(ln)
#             i += 1
#     return merged


# All section headers we want to stop at
STOP_HEADERS = [
    "Professional Summary",
    "Technical Skills",
    "Professional Experience",
    "Work Experience",
    "Experience",
    "Education",
    "Skills",
    "Certifications",
    "Projects"
]
# Build a regex matching ANY of those, with or without trailing colon
STOP_SECTIONS_RX = re.compile(
    r'^(?:' + r'|'.join(re.escape(h) for h in STOP_HEADERS) + r'):?\s*$',
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

def extract_skills_text(lines: List[str]) -> str:
    """
    Extracts the Skills or Technical Skills section and stops
    as soon as *any* other known header appears (even without colon).
    """
    print("Extracting skills text (fixed stopping)...")
    lines = _merge_fragments([ln.strip() for ln in lines if ln.strip()])

    # Our own header (will not trigger stop)
    header_rx = re.compile(r'^(?:Skills|Technical Skills)\s*:?\s*$', re.IGNORECASE)

    # Find the index of Skills / Technical Skills
    start_idx = next((i for i, ln in enumerate(lines) if header_rx.match(ln)), None)
    if start_idx is None:
        return ""

    skills = []
    for ln in lines[start_idx + 1:]:
        # If this line is *any* stop‐header **other than** our own, break
        if STOP_SECTIONS_RX.match(ln) and not header_rx.match(ln):
            break
        skills.append(ln)

    return ", ".join(skills).strip()

def extract_summary_text(lines: List[str]) -> str:
    """
    Extracts the Professional Summary section from PDF-style span lines.
    """
    print("Extracting summary text...")
    # clean and merge broken fragments
    lines = _merge_fragments([ln.strip() for ln in lines if ln.strip()])

    header_rx = re.compile(r'^(Professional Summary|ROFESSIONAL SUMMARY)\s*:?\s*$', re.I)
    start_idx = next((i for i, ln in enumerate(lines) if header_rx.match(ln)), None)
    if start_idx is None:
        return ""

    summary_lines = []
    for ln in lines[start_idx + 1 :]:
        # stop at next section heading (e.g. "TECHNICAL SKILLS:")
        if re.match(r'^[A-Za-z &]+:$', ln):
            break
        summary_lines.append(ln)
    return " ".join(summary_lines).strip()

def extract_experience_text(lines: List[str]) -> str:
    """
    Extracts the Experience section from PDF-style span lines.
    """
    print("Extracting experience text...")
    lines = _merge_fragments([ln.strip() for ln in lines if ln.strip()])

    header_rx = re.compile(
        r'^(Professional Experience|ROFESSIONAL EXPERIENCE|Work Experience|Experience)\s*:?\s*$',
        re.I
    )
    start_idx = next((i for i, ln in enumerate(lines) if header_rx.match(ln)), None)
    if start_idx is None:
        return ""

    exp_lines = []
    for ln in lines[start_idx + 1 :]:
        if re.match(r'^[A-Za-z &]+:$', ln):
            break
        exp_lines.append(ln)
    return " ".join(exp_lines).strip()

# def extract_skills_text(lines: List[str]) -> str:
#     """
#     Extracts the Skills or Technical Skills section from PDF-style span lines.
#     """
#     print("Extracting skills text (including Technical Skills)...")
#     # Clean up and merge single-letter fragments
#     lines = _merge_fragments([ln.strip() for ln in lines if ln.strip()])

#     # Match either “Skills” or “Technical Skills”
#     header_rx = re.compile(r'^(?:Skills|Technical Skills)\s*:?\s*$', re.IGNORECASE)

#     # Find the index of that header
#     start_idx = next((i for i, ln in enumerate(lines) if header_rx.match(ln)), None)
#     if start_idx is None:
#         return ""

#     skills = []
#     # Collect until the next section header
#     for ln in lines[start_idx + 1:]:
#         if re.match(r'^[A-Za-z &]+:$', ln):
#             break
#         skills.append(ln)

#     # Return a comma-separated list
#     return ", ".join(skills).strip()

def extract_certifications_text(lines: List[str]) -> str:
    """
    Extracts the Certifications section from PDF-style span lines.
    """
    print("Extracting certifications text...")
    lines = _merge_fragments([ln.strip() for ln in lines if ln.strip()])

    header_rx = re.compile(r'^(Certifications|Certifications and Licenses)\s*:?\s*$', re.I)
    start_idx = next((i for i, ln in enumerate(lines) if header_rx.match(ln)), None)
    if start_idx is None:
        return ""

    certs = []
    for ln in lines[start_idx + 1 :]:
        if re.match(r'^[A-Za-z &]+:$', ln):
            break
        certs.append(ln)
    return " | ".join(certs).strip()

def extract_div_section(soup: BeautifulSoup, *hdrs: str) -> str:
    """
    Given header labels (e.g. "Skills" or "Technical Skills"), finds the first
    <h2> matching one of them, then returns all text in siblings until the next <h2>.
    """
    rx = re.compile(r'^(?:' + r'|'.join(map(re.escape, hdrs)) + r')\s*$', re.I)
    h2 = soup.find("h2", string=rx)
    if not h2:
        return ""
    # header sits inside <div class="section_title">…</div>
    title_div = h2.find_parent("div", class_="section_title")
    if not title_div or not title_div.parent:
        return ""
    out = []
    for sib in title_div.parent.find_next_siblings():
        if sib.find("h2", class_="section_header_title"):
            break
        txt = sib.get_text(" ", strip=True)
        if txt:
            out.append(txt)
    return "\n".join(out).strip()

# ─── Main extractor ───

def extract_resume_data(url: str, driver) -> Dict[str, str]:
    snapshot_file = get_snapshot_filename(url)

    if os.path.exists(snapshot_file):
        print(f"Loading snapshot from {snapshot_file}")
        with open(snapshot_file, "r", encoding="utf-8") as file:
            html = file.read()
    else:
        load_cookies_and_access_page(url)
        wait_for_resume_load(driver)
        html = driver.page_source
        with open(snapshot_file, "w", encoding="utf-8") as file:
            file.write(html)
        print(f"Snapshot saved to {snapshot_file}")

    soup = BeautifulSoup(html, "html.parser")
    data: Dict[str, str] = {}

    # ─── Try HTML iframe path ───
    iframe = soup.select_one("iframe[name='resume_frame']")
    if iframe and iframe.has_attr("srcdoc"):
        # re‐parse the embedded HTML
        html = iframe["srcdoc"]
        soup = BeautifulSoup(html, "html.parser")
        data: Dict[str,str] = {}

        # small helper to grab a single selector’s text
        def safe_text(sel: str) -> str:
            el = soup.select_one(sel)
            return el.get_text(" ", strip=True) if el else ""

        # Name
        name_el = soup.select_one("#basic_info_cell h1.fn")
        data["Name"] = name_el.get_text(strip=True) if name_el else ""

        # Headline & Location (if you want them)
        data["Headline"] = safe_text("h2#headline")
        data["Location"] = safe_text("div.locality")

        # Professional Summary
        data["Professional Summary"] = safe_text("p#res_summary")

        # Experience (as you already had)
        cont = soup.select_one("#work-experience-items")
        parts = []
        if cont:
            for item in cont.select("div.work-experience-section"):
                title = item.select_one("h3[data-shield-id='workExperience_work_title']")
                dates = item.select_one("div[data-shield-id='workExperience_work_dates']")
                desc  = item.select_one("p[data-shield-id='workExperience_work_description']")
                if title and dates:
                    seg = f"{title.get_text(strip=True)} ({dates.get_text(strip=True)})"
                    if desc:
                        seg += "\n" + desc.get_text(" ", strip=True)
                    parts.append(seg)
        data["Professional Experience"] = "\n\n".join(parts)

        # Skills (span.skill-text)
        skills = [s.get_text(strip=True) for s in soup.select("span.skill-text")]
        data["Skills"] = ", ".join(skills)

        # Certifications
        certs = []
        for cert in soup.select("div.certification-section"):
            t = safe_text("div.certification_title")
            d = safe_text("div.certification_date")
            x = safe_text("p.certification_description")
            line = "; ".join(p for p in (t, d, x) if p)
            certs.append(line)
        data["Certifications"] = "\n".join(certs)

        # Education
        edus = []
        for ed in soup.select("div.education-section"):
            t = safe_text("h3.edu_title")
            s = safe_text("span[data-shield-id='education_edu_school_span']")
            l = safe_text("span[data-shield-id='education_edu_location_span']")
            d = safe_text("div[data-shield-id='education_edu_dates']")
            edus.append("; ".join(p for p in (t, s, l, d) if p))
        data["Education"] = "\n".join(edus)

        # Links
        link_el = soup.select_one("div.link_url a[href]")
        data["Links"] = link_el["href"] if link_el else ""

        # Projects (if your iframe‐HTML ever includes a Projects section)
        projs = []
        for pr in soup.select("div.project-section"):
            projs.append(pr.get_text(" ", strip=True))
        data["Projects"] = "\n".join(projs)

        return data


    # # ─── Try HTML iframe path ───
    # iframe = soup.select_one("iframe[name='resume_frame']")
    # if iframe and iframe.has_attr("srcdoc"):
    #     html = iframe["srcdoc"]
    #     soup = BeautifulSoup(html, "html.parser")

    #     # Name
    #     name_el = soup.select_one("#basic_info_cell h1.fn")
    #     data["Name"] = name_el.get_text(strip=True) if name_el else ""

    #     # Experience
    #     cont = soup.select_one("#work-experience-items")
    #     if cont:
    #         parts = []
    #         for item in cont.select("div.work-experience-section"):
    #             title = item.select_one("h3[data-shield-id='workExperience_work_title']")
    #             dates = item.select_one("div[data-shield-id='workExperience_work_dates']")
    #             desc = item.select_one("p[data-shield-id='workExperience_work_description']")
    #             if title and dates:
    #                 part = f"{title.get_text(strip=True)} ({dates.get_text(strip=True)})"
    #                 if desc:
    #                     part += f"\n{desc.get_text(strip=True)}"
    #                 parts.append(part)
    #         data["Experience"] = "\n\n".join(parts)
    #     else:
    #         data["Experience"] = ""
    #     return data

    # # ─── Try PDF spans fallback ───
    # spans = soup.select("div.react-pdf__Page__textContent span[role='presentation']")
    # if spans:
    #     lines = [s.text.strip() for s in spans if s.text.strip()]
    #     data["Name"] = next((l for l in lines if l.isupper() and len(l.split()) > 1), "")
    #     data["Professional Summary"]    = extract_summary_text(lines)
    #     data["Experience"] = extract_experience_text(lines)
    #     data["Skills"]                  = extract_skills_text(lines)
    #     data["Certifications"]          = extract_certifications_text(lines)

    #     return data

    
    spans = soup.select("div.react-pdf__Page__textContent span[role='presentation']")
    if spans:
        raw_lines = [s.text for s in spans if s.text.strip()]
        data["Name"] = next(
            (l for l in raw_lines if l.isupper() and len(l.split()) > 1),
            ""
        )
        data["PROFESSIONAL SUMMARY"]  = extract_summary_text(raw_lines)
        data["EXPERIENCE"]            = extract_experience_text(raw_lines)
        data["SKILLS"]                = extract_skills_text(raw_lines)
        data["CERTIFICATIONS"]        = extract_certifications_text(raw_lines)
        return data

    # # ─── Try Div-based layout fallback ───  # working for name and experience DIV
    # def safe_text(selector: str) -> str:
    #     el = soup.select_one(selector)
    #     return el.get_text(strip=True) if el else ""

    # # Name (first visible part of h1)
    # name_el = soup.select_one("h1#resume-contact")
    # if name_el:
    #     data["Name"] = list(name_el.stripped_strings)[0]
    # else:
    #     data["Name"] = ""

    # # Headline
    # data["Headline"] = safe_text("h2#headline")

    # # Summary
    # data["Professional Summary"] = safe_text("p#res_summary")

    # # Experience
    # work_experience = []
    # for item in soup.select("div.work-experience-section"):
    #     title = safe_text("h3[data-shield-id='workExperience_work_title']")
    #     company = safe_text("span[data-shield-id='workExperience_work_experience_company']")
    #     location = safe_text("span[data-shield-id='workExperience_location_span']")
    #     dates = safe_text("div[data-shield-id='workExperience_work_dates']")
    #     desc = safe_text("p[data-shield-id='workExperience_work_description']")
    #     parts = [
    #         f"Title: {title}",
    #         f"Company: {company}",
    #         f"Location: {location}",
    #         f"Dates: {dates}",
    #         f"Description: {desc}",
    #     ]
    #     work_experience.append("\n".join(p for p in parts if p.strip()))
    # data["Professional Experience"] = "\n\n".join(work_experience)

    # # Education
    # education = []
    # for item in soup.select("div.education-section"):
    #     title = safe_text("h3.edu_title")
    #     school = safe_text("span[data-shield-id='education_edu_school_span']")
    #     location = safe_text("span[data-shield-id='education_edu_location_span']")
    #     dates = safe_text("div[data-shield-id='education_edu_dates']")
    #     parts = [
    #         f"Title: {title}",
    #         f"School: {school}",
    #         f"Location: {location}",
    #         f"Dates: {dates}",
    #     ]
    #     education.append("\n".join(p for p in parts if p.strip()))
    # data["Education"] = "\n\n".join(education)

    # # Skills
    # skills = [el.get_text(strip=True) for el in soup.select("span.skill-text")]
    # data["Skills"] = ", ".join(skills)

    # # Certifications
    # certs = []
    # for cert in soup.select("div.certification-section"):
    #     title = safe_text("div.certification_title")
    #     date = safe_text("div.certification_date")
    #     desc = safe_text("p.certification_description")
    #     parts = [
    #         f"Title: {title}",
    #         f"Date: {date}",
    #         f"Description: {desc}",
    #     ]
    #     certs.append("\n".join(p for p in parts if p.strip()))
    # data["Certifications"] = "\n\n".join(certs)

    # # Links
    # link_el = soup.select_one("div.link_url a[href]")
    # data["Links"] = link_el["href"] if link_el else ""

    # return data # working for name and experience DIV

    # ── 4) Div‐based layout fallback ──────────────────────────────────────

    # Name + Headline
    h1 = soup.select_one("h1#resume-contact")
    data["Name"]     = list(h1.stripped_strings)[0] if h1 else ""
    hl = soup.select_one("h2#headline")
    data["Headline"] = hl.get_text(" ", strip=True) if hl else ""

    # Professional Summary
    data["Professional Summary"] = safe_text = lambda sel: (
        (soup.select_one(sel).get_text(" ", strip=True)
         if soup.select_one(sel) else "")
    )
    data["Professional Summary"] = (
        safe_text("p#res_summary")
        or extract_div_section(soup, "Professional Summary")
    )

    # Skills / Technical Skills
    skills = extract_div_section(soup, "Technical Skills")
    if not skills:
        skills = extract_div_section(soup, "Skills")
    # fallback to any <span class="skill-text">
    if not skills:
        items = [e.get_text(strip=True) for e in soup.select("span.skill-text")]
        skills = ", ".join(items)
    data["Skills"] = skills

    # Certifications
    certs = extract_div_section(soup,
        "Certifications and Licenses", "Certifications"
    )
    data["Certifications"] = certs

    # Links
    link = soup.select_one("div.link_url a[href]")
    data["Links"] = link["href"] if link else ""

    # Education
    edu = []
    for e in (soup.select_one("div.section-item.education-content")
                   or []).select("div.education-section"):
        t = e.select_one(".edu_title")
        s = e.select_one("span[data-shield-id='education_edu_school_span']")
        l = e.select_one("span[data-shield-id='education_edu_location_span']")
        d = e.select_one("div[data-shield-id='education_edu_dates']")
        parts = [x.get_text(strip=True) for x in (t,s,l,d) if x]
        edu.append(" | ".join(parts))
    data["Education"] = "\n".join(edu)

    # Work fallback (in case iframe worked but you want div fallback too)
    work = []
    for w in soup.select("div.work-experience-section"):
        t = w.select_one("h3[data-shield-id='workExperience_work_title']")
        c = w.select_one("span[data-shield-id='workExperience_work_experience_company']")
        l = w.select_one("span[data-shield-id='workExperience_location_span']")
        d = w.select_one("div[data-shield-id='workExperience_work_dates']")
        p = w.select_one("p[data-shield-id='workExperience_work_description']")
        parts = []
        if t: parts.append(t.get_text(strip=True))
        if c: parts.append(c.get_text(strip=True))
        if l: parts.append(l.get_text(strip=True))
        if d: parts.append(d.get_text(strip=True))
        if p: parts.append(p.get_text(" ", strip=True))
        work.append(" | ".join(parts))
    data["Professional Experience"] = "\n".join(work)

    return data

def main():
    #save_cookies()  # uncomment to generate cookies file first time

    urls = [
        "https://resumes.indeed.com/resume/cb459e5ab31ac6de",
        "https://resumes.indeed.com/resume/b4e1db87188298c3",
        # "https://resumes.indeed.com/resume/f36ea98f57095137",
        # "https://resumes.indeed.com/resume/7ff20f7be9e91432"
    ]

    all_rows = []
    for url in urls:
        try:
            # row = extract_resume_data(url)
            # all_rows.append(row)
            row = extract_resume_data(url, driver)  # ✅ Pass `driver` here
            row["URL"] = url
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