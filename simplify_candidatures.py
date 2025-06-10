import re

import pandas as pd

# Script to simplify the first name last name field for candidates


def clean_candidate_info(text):
    """
    Clean candidate information by removing emails, phone numbers, and unwanted symbols
    while keeping hyphens for composed names and apostrophes for particle names
    """
    if pd.isna(text):
        return text

    # Convert to string
    text = str(text)

    # Remove email addresses (pattern: word@word.word)
    text = re.sub(r"\S+@\S+\.\S+", "", text)

    # Remove phone numbers (patterns: various formats of 10 digits)
    # Handles formats like 0688914976, 06 88 91 49 76, 06.88.91.49.76, etc.
    text = re.sub(r"(?:(?:\+|00)33[\s.-]?)?(?:0)?[1-9](?:[\s.-]?\d{2}){4}", "", text)

    # Remove forward slashes and commas
    text = text.replace("/", " ").replace(",", " ")

    # Clean up multiple spaces
    text = re.sub(r"\s+", " ", text)

    # Strip leading/trailing whitespace
    text = text.strip()

    return text


def pad_department_number(num):
    """
    Left pad department number with '0' if it's a single digit
    """
    if pd.isna(num):
        return num

    # Convert to string and pad
    num_str = str(int(num))
    return num_str.zfill(2)


# Read the CSV file
input_file = "candidatures.csv"
output_file = "candidatures_cleaned.csv"

# Read the CSV
df = pd.read_csv(input_file)

# Display original column names for reference
print("Original columns:")
for i, col in enumerate(df.columns):
    print(f"Column {i}: {col}")

# Pad department numbers (column index 1)
df.iloc[:, 1] = df.iloc[:, 1].apply(pad_department_number)

# Clean candidate information (columns 2 to 7, which are indices 2-7)
for i in range(2, 8):
    if i < len(df.columns):
        df.iloc[:, i] = df.iloc[:, i].apply(clean_candidate_info)

# Save the cleaned CSV
df.to_csv(output_file, index=False)

print(f"\nCleaning complete! Cleaned file saved as: {output_file}")

# Display a sample of the cleaned data
print("\nSample of cleaned data (first 5 rows):")
print(df.head())

# Show some examples of the cleaning
print("\nExamples of cleaned names:")
for i in range(2, min(8, len(df.columns))):
    col_name = df.columns[i]
    # Get first non-null value from the column
    sample_values = df.iloc[:, i].dropna().head(3)
    if not sample_values.empty:
        print(f"\nColumn {i} samples:")
        for val in sample_values:
            print(f"  - {val}")
