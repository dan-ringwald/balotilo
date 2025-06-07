import csv
import os
from pathlib import Path

import yaml


def find_department_folder(department_num):
    """
    Find the folder that starts with the department number
    """
    # Format department number with leading zeros
    dept_str = str(department_num).zfill(2)
    if len(str(department_num)) == 3:  # For overseas departments
        dept_str = str(department_num)

    # Look for folders starting with the department number
    current_dir = Path(".")
    for folder in current_dir.iterdir():
        if folder.is_dir() and folder.name.startswith(f"{dept_str}_"):
            return folder

    print(f"Warning: No folder found for department {dept_str}")
    return None


def process_csv_to_yaml(input_csv):
    """
    Process CSV file and convert to YAML format in appropriate folders
    """
    # Track processed departments
    processed = []

    with open(input_csv, "r", encoding="utf-8") as csvfile:
        # Use csv.reader to handle quoted fields properly
        reader = csv.reader(csvfile)

        for row in reader:
            if len(row) < 3:  # Skip empty or incomplete rows
                continue

            # Extract data from row
            list_title = row[0].strip()
            department = row[1].strip()
            candidates = [name.strip() for name in row[2:] if name.strip()]

            # Find the appropriate folder
            folder = find_department_folder(department)
            if not folder:
                continue

            # Prepare YAML data
            yaml_data = {list_title: candidates}

            # Path to candidates.yaml file
            yaml_file = folder / "candidates.yaml"

            # Check if file exists
            if yaml_file.exists():
                # Read existing content
                with open(yaml_file, "r", encoding="utf-8") as f:
                    existing_content = f.read()

                # Append new content
                with open(yaml_file, "a", encoding="utf-8") as f:
                    # Add a newline if file doesn't end with one
                    if existing_content and not existing_content.endswith("\n"):
                        f.write("\n")
                    # Write the new YAML data
                    yaml.dump(
                        yaml_data,
                        f,
                        default_flow_style=False,
                        allow_unicode=True,
                        sort_keys=False,
                    )

                print(f"Appended to {yaml_file}")
            else:
                # Create new file
                with open(yaml_file, "w", encoding="utf-8") as f:
                    yaml.dump(
                        yaml_data,
                        f,
                        default_flow_style=False,
                        allow_unicode=True,
                        sort_keys=False,
                    )

                print(f"Created {yaml_file}")

            processed.append(department)

    print(f"\nProcessed {len(processed)} departments: {', '.join(processed)}")


# Example usage
if __name__ == "__main__":
    # Input CSV file name
    input_file = "candidatures_cleaned.csv"  # Change this to your actual CSV filename

    # Check if file exists
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found!")
        print("Please make sure the CSV file is in the current directory.")
    else:
        print(f"Processing {input_file}...")
        process_csv_to_yaml(input_file)
        print("\nConversion complete!")

    # Show example of what was created
    print("\nExample YAML output format:")
    example_yaml = {
        "Place Publique 93 : pour une gauche de terrain, sociale, écologique,  et européenne": [
            "PRIGENT Olivier",
            "MATHIEU Nathalie",
            "LAVON Sigalit",
            "BENOIT Etienne",
            "MARTY Laurence",
            "CEDRIC Emmanuel",
        ]
    }
    print(yaml.dump(example_yaml, default_flow_style=False, allow_unicode=True))
