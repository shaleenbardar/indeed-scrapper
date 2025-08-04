import pandas as pd

# 1) Read your data (choose the appropriate reader)
# If it’s a CSV:
df = pd.read_csv("Master_Indeed.xlsx - Master_Indeed_991.csv", dtype=str)

# If it’s an Excel file:
# df = pd.read_excel("your_input.xlsx", sheet_name="Sheet1", dtype=str)

# 2) (Recommended) Strip any extra whitespace in the “Resume_parsed” column
df["Resume_Parsed"] = df["Resume_Parsed"].str.strip()

# 3) Filter to only those rows where Resume_parsed == "X"
df_x = df[df["Resume_Parsed"] == "X"]

# 4) Write the filtered rows out to a new file
df_x.to_csv("resumes_parsed_X.csv", index=False)