import pandas as pd
import re
import rocketreach
import time

# Step 1: Load and prep CSV
df = pd.read_csv("candidates_with_emails_marketing_analyst.csv")
df = df.dropna(how="all")
# df["email_1"] = None
# df["email_2"] = None

# Step 2: Init RocketReach
rr = rocketreach.Gateway(api_key="1889a7bk58a9aaf2b58a444d18890d9a9336e4d5")

# compile keywords for matching against person.current_title
KEYWORDS = re.compile(
    r"\b(data analyst|analyst|data analysis|data scientist|data engineer|data|analysis|business|marketing|market|consultant)\b",
    re.IGNORECASE,
)

# explicit priority order for tiebreakers
PRIORITY = [
    "data analyst",
    "analyst",
    "data analysis",
    "data scientist",  
    "data engineer",
    "business analyst",
    "business",
    "marketing",
    "market",
    "data",
    "analysis",
    "consultant",
]

def normalize(text: str) -> str:
    # If it's not a string (e.g. NaN → float), treat it as empty
    if not isinstance(text, str):
        return ""
    # Lowercase, strip digits & punctuation (except spaces), collapse whitespace.
    s = re.sub(r"[^a-z\s]", " ", (text or "").lower())
    return re.sub(r"\s+", " ", s).strip()

def title_priority(title_norm: str) -> int:
    # Return index in PRIORITY for first matching term, or len(PRIORITY) if none.
    for i, term in enumerate(PRIORITY):

        if term in title_norm:
            return i
    return len(PRIORITY)

# Step 3: Looping
for idx, row in df.iloc[0:10].iterrows():
    name = row.get("name")
    print(f"\n=== Processing row {idx}: {name!r} ===")
    if not isinstance(name, str) or not name.strip():
        print("  ⏭️  Skipping: no valid name")
        continue

    # normalize CSV city
    city = row.get("city")
    city = city.strip() if isinstance(city, str) and city.upper() != "N/A" else None
    city_norm = normalize(city) if city else None
    print(f"  City filter: {city_norm!r}")

    # normalize CSV experience_text (for employer & designation matching)
    exp_norm = normalize(row.get("experience_text", ""))

    # 1) search by name only
    print("  🔍 Searching RocketReach by name...")
    results = rr.person.search().filter(name=name).execute()
    if not getattr(results, "is_success", False):
        print(f"  ❌ Search failed: {getattr(results, 'message', 'No message')}")
        continue

    people = getattr(results, "people", [])
    print(f"  ✅ Search returned {len(people)} people")
    if not people:
        continue

    exact_matches = [p for p in people if isinstance(p.name, str) and p.name.strip().lower() == name.strip().lower()]
    print(f"  🔎 Exact name matches: {len(exact_matches)}")
    if not exact_matches:
        print("  ⏭️  No exact-name candidates")
        continue


    # 2) build scored list of all keyword-matched candidates
    scored = []
    for i, person in enumerate(exact_matches):
        raw_title = person.current_title or ""
        title_norm = normalize(raw_title)
        print(f"    [{i}] {person.name} ({person.id}) – title: {person.current_title!r}")

        # 1) check if this title is literally in the CSV experience_text
        designation_in_exp = bool(title_norm) and (title_norm in exp_norm)
        if designation_in_exp:
            print("       ★ designation appears in experience_text")

        # 2) if NOT designation_in_exp, then enforce your keyword list
        if not designation_in_exp and not KEYWORDS.search(title_norm):
            print(f"       ✖ skipped: neither in experience_text nor a target role")
            continue
        print("       ✔ passed role check")

        # 3) build a combined score
        score = 0
        if designation_in_exp:
            score += 10     # big boost for exact designation-in-experience
        # optional city match
        if city_norm and city_norm in normalize(person.city):
            score += 1
            print(f"       + city match ({person.city!r})")
        # optional employer match
        emp_norm = normalize(person.current_employer)
        if emp_norm and emp_norm in exp_norm:
            score += 1
            print(f"       + employer match ({person.current_employer!r})")

        print(f"       → Total score: {score}")
        prio = title_priority(title_norm)
        scored.append((score, prio, person))

    if not scored:
        print("  ⏭️  No keyword-matched candidates")
        continue

    # sort by score desc, then priority asc
    scored.sort(key=lambda x: (-x[0], x[1]))

    # 3) attempt lookup up to 3 best candidates, stop on first email found
    email1 = email2 = None
    for attempt, (_, _, person) in enumerate(scored[:3], start=1):
        print(f"  🔄 Lookup attempt #{attempt} for ID={person.id}")
        lookup = rr.person.lookup(person_id=person.id)
        if not getattr(lookup, "is_success", False):
            print(f"    ❌ Lookup failed: {getattr(lookup, 'message', 'No message')}")
            continue

        emails = lookup.person.emails or []
        if not emails:
            print("    ⚠️ No emails returned for this candidate")
            continue

        # grab up to two emails, stop after first success
        email1 = emails[0]["email"]
        email2 = emails[1]["email"] if len(emails) > 1 else None
        print(f"    ✉️  Found: {email1!r}" + (f", {email2!r}" if email2 else ""))
        break

    # write back whatever was found (None if all attempts failed)
    df.at[idx, "email_1"] = email1
    df.at[idx, "email_2"] = email2

    time.sleep(1.5)  # throttle

# Step 4: save results
df.to_csv("candidates_with_emails_marketing_analyst.csv", index=False)
print("\n✅ Done. Results saved to candidates_with_emails_2.csv")