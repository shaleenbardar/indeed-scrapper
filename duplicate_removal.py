import pandas as pd

# 1) Read both CSVs (make sure these paths are correct):
df1 = pd.read_csv("master_original_update_hana_deduplicated.xlsx - Sheet1.csv", dtype=str)
df2 = pd.read_csv("Masterfile_With_Emails - Sheet1.csv", dtype=str)

# 2) (Optional but recommended) Strip whitespace around your ID columns:
df1["indeed_unique_id"] = df1["indeed_unique_id"].str.strip()
df2["indeed_id"] = df2["indeed_id"].str.strip()

# 3) Remove rows in df1 whose indeed_unique_id is present in df2["indeed_id"]:
mask_not_in_df2 = ~df1["indeed_unique_id"].isin(df2["indeed_id"])
df_filtered = df1[mask_not_in_df2]

# 4) Now keep only those rows where workflow_pipeline == "resume":
df_out = df_filtered[df_filtered["workflow_pipeline"] == "resume"]

# 5) Write the final result to a new CSV:
df_out.to_csv("candidates_with_emails.csv", index=False)