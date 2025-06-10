import glob
import os
from pathlib import Path

import pandas as pd

# This script helps gets a global votant list and split it into small per-departement lists in subfolders, as expected by the script
# creating the elections on balotilo


def extract_emails_from_votants(folder_path):
    """
    Extract emails from votants_xxx.csv file in a given folder
    and save them to voters.txt
    """
    # Find votants_*.csv file in the folder
    votants_pattern = os.path.join(folder_path, "votants_*.csv")
    votants_files = glob.glob(votants_pattern)

    if not votants_files:
        print(f"  No votants_*.csv file found in {folder_path}")
        return False

    if len(votants_files) > 1:
        print(
            f"  Warning: Multiple votants files found in {folder_path}, using first one"
        )

    votants_file = votants_files[0]
    print(f"  Processing: {os.path.basename(votants_file)}")

    try:
        # Read the CSV file
        df = pd.read_csv(votants_file, encoding="utf-8")

        # Check if Email column exists
        if "Email" not in df.columns:
            print(f"  Error: No 'Email' column found in {votants_file}")
            return False

        # Extract emails (remove NaN values and empty strings)
        emails = df["Email"].dropna()
        emails = emails[emails.str.strip() != ""]

        # Save to voters.txt
        voters_file = os.path.join(folder_path, "voters.txt")
        with open(voters_file, "w", encoding="utf-8") as f:
            for email in emails:
                f.write(f"{email.strip()}\n")

        print(f"  Created voters.txt with {len(emails)} emails")
        return True

    except Exception as e:
        print(f"  Error processing {votants_file}: {str(e)}")
        return False


def process_all_subfolders():
    """
    Process all subfolders in the current directory
    """
    current_dir = Path(".")
    processed_count = 0
    error_count = 0

    # Get all subdirectories
    subfolders = [
        f for f in current_dir.iterdir() if f.is_dir() and not f.name.startswith(".")
    ]

    print(f"Found {len(subfolders)} subfolders to process\n")

    for folder in sorted(subfolders):
        print(f"Processing folder: {folder.name}")

        if extract_emails_from_votants(folder):
            processed_count += 1
        else:
            error_count += 1

        print()  # Empty line for readability

    print(f"\nSummary:")
    print(f"Successfully processed: {processed_count} folders")
    print(f"Errors encountered: {error_count} folders")
    print(f"Total folders: {len(subfolders)}")


def main():
    """
    Main function to run the script
    """
    print("Email Extraction Script")
    print("=" * 50)
    print("This script will extract emails from votants_*.csv files")
    print("and save them as voters.txt in each subfolder.\n")

    # Process all subfolders
    process_all_subfolders()

    print("\nDone!")


if __name__ == "__main__":
    main()
