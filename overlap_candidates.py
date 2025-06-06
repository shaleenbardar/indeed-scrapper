import pandas as pd

def compare_files(file1, file2):
    df1 = pd.read_csv(file1)
    df2 = pd.read_csv(file2)

    if 'Candidate Name' not in df1.columns or 'Candidate Name' not in df2.columns:
        print("Both files must contain a 'Candidate Name' column.")
        return

    names1 = set(df1['Candidate Name'])
    names2 = set(df2['Candidate Name'])

    overlap = names1.intersection(names2)

    total_names = len(names1.union(names2))
    overlap_percentage = (len(overlap) / total_names) * 100 if total_names > 0 else 0

    print(f"Overlap percentage: {overlap_percentage:.2f}%")
    print(f"Number of overlapping names: {len(overlap)}")
    print(f"Total unique names: {total_names}")

    return overlap_percentage, overlap

file1 = 'market_analysis.csv'
file2 = 'data_analysis.csv'
compare_files(file1, file2)