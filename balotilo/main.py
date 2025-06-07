import argparse
import json
import logging
import os
import time

import requests
import yaml
from bs4 import BeautifulSoup

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
print(ROOT_DIR)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("balotilo_automation.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class BalotiloAutomation:
    def __init__(self, username, password, base_url="https://www.balotilo.org"):
        self.username = username
        self.password = password
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        )

    def login(self):
        """Login to Balotilo with the provided credentials."""
        try:
            # First visit the home page to get initial cookies and CSRF token
            logger.info(f"Visiting home page to get initial cookies and CSRF token")
            home_response = self.session.get(self.base_url)
            home_response.raise_for_status()

            # Parse home page to get CSRF token
            home_soup = BeautifulSoup(home_response.text, "html.parser")
            csrf_token = home_soup.find("meta", {"name": "csrf-token"})["content"]
            logger.debug(f"CSRF token from home page: {csrf_token}")
            logger.debug(f"Cookies after home page: {dict(self.session.cookies)}")

            # Set locale to English
            logger.info("Setting locale to English")
            locale_data = {
                "_method": "patch",
                "authenticity_token": csrf_token,
                "locale": "en",
            }

            locale_headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
                "Origin": self.base_url,
                "Referer": self.base_url,
            }

            locale_response = self.session.post(
                f"{self.base_url}/locale",
                data=locale_data,
                headers=locale_headers,
                allow_redirects=True,
            )

            logger.debug(f"Locale response status: {locale_response.status_code}")
            logger.debug(f"Locale response URL: {locale_response.url}")
            logger.debug(f"Cookies after locale setting: {dict(self.session.cookies)}")

            # Now get the login page (which should be in English)
            login_url = f"{self.base_url}/login"
            logger.info(f"Getting login page: {login_url}")
            response = self.session.get(login_url)
            response.raise_for_status()

            # Verify we got an English page
            if "Log in" in response.text:
                logger.info("Successfully got English login page")
            else:
                logger.warning("Login page might not be in English")

            # Dump response details
            logger.debug(f"Login page status code: {response.status_code}")
            logger.debug(f"Login page URL: {response.url}")
            logger.debug(f"First 200 chars of login page: {response.text[:200]}")

            # Parse the login page to extract the form
            soup = BeautifulSoup(response.text, "html.parser")

            # Find the login form
            login_form = soup.find("form", {"class": "new_user_session"})
            if not login_form:
                logger.error("Could not find the login form")
                logger.debug(f"Page content: {response.text}")
                return False

            # Extract the form action URL
            form_action = login_form.get("action")
            if not form_action:
                form_action = "/user_session"  # Default if not found

            logger.debug(f"Form action URL: {form_action}")

            # Make sure form_action is a full URL
            if not form_action.startswith("http"):
                form_action = f"{self.base_url}{form_action}"

            # Extract authenticity token from the form
            auth_token_input = login_form.find("input", {"name": "authenticity_token"})
            if not auth_token_input:
                logger.error("Could not find authenticity token in the form")
                return False

            auth_token = auth_token_input.get("value")
            logger.debug(f"Authenticity token: {auth_token}")

            # Extract all form inputs to make sure we're not missing anything
            form_data = []
            for input_tag in login_form.find_all("input"):
                name = input_tag.get("name")
                value = input_tag.get("value", "")

                if name:
                    logger.debug(f"Form input: {name}={value}")

                    # Skip the password field as we'll add it manually
                    if name == "user_session[password]":
                        continue

                    # Skip the email field as we'll add it manually
                    if name == "user_session[email]":
                        continue

                    form_data.append((name, value))

            # Add our username and password
            form_data.append(("user_session[email]", self.username))
            form_data.append(("user_session[password]", self.password))

            # Find the submit button value
            submit_btn = login_form.find("input", {"type": "submit"})
            if submit_btn and submit_btn.get("name") and submit_btn.get("value"):
                form_data.append((submit_btn.get("name"), submit_btn.get("value")))

            # Set necessary headers
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
                "Origin": self.base_url,
                "Referer": login_url,
            }

            logger.debug(f"Request headers: {headers}")

            # Create properly encoded form data
            import urllib.parse

            encoded_data = urllib.parse.urlencode(form_data)

            # Submit login form
            logger.info(f"Submitting login form to: {form_action}")
            logger.debug(f"Form data: {form_data}")

            response = self.session.post(
                form_action, data=encoded_data, headers=headers, allow_redirects=True
            )

            # Detailed logging of the response
            logger.debug(f"Login response status: {response.status_code}")
            logger.debug(f"Login response URL: {response.url}")
            logger.debug(f"First 500 chars of response: {response.text[:500]}")

            # Check if login was successful
            if "My elections" in response.text or "Create an election" in response.text:
                logger.info("Login successful!")
                return True
            else:
                # Try to get the consultations page to see if we're actually logged in
                consult_response = self.session.get(f"{self.base_url}/consultations")
                logger.debug(
                    f"Consultation page status: {consult_response.status_code}"
                )
                logger.debug(f"Consultation page URL: {consult_response.url}")
                logger.debug(
                    f"First 500 chars of consultations page: {consult_response.text[:500]}"
                )

                if (
                    "My elections" in consult_response.text
                    or "Create an election" in consult_response.text
                ):
                    logger.info("Login was actually successful!")
                    return True

                logger.error("Login failed. Please check your credentials.")
                return False
        except Exception as e:
            logger.error(f"Login failed with error: {str(e)}")
            logger.exception("Exception details:")
            return False

    def create_election(self, config, voters_file, candidates_file):
        """Create a new election on Balotilo with candidates lists."""
        try:
            # Navigate to the create election page
            create_url = f"{self.base_url}/consultations/new"
            logger.info(f"Navigating to create election page: {create_url}")
            response = self.session.get(create_url)
            response.raise_for_status()

            # First, verify we're on the create page
            if "New election" not in response.text:
                logger.error("Not on the create election page")
                logger.debug(
                    f"Page title: {BeautifulSoup(response.text, 'html.parser').find('title').text if BeautifulSoup(response.text, 'html.parser').find('title') else 'No title found'}"
                )
                # Try to re-login if needed
                if "Log in" in response.text:
                    logger.info("Need to log in again")
                    if not self.login():
                        return None
                    response = self.session.get(create_url)
                    response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            create_form = soup.find("form", {"id": "new_consultation"})
            if not create_form:
                logger.error("Could not find the new_consultation form")
                return None

            # Extract all form inputs to ensure we're not missing any required fields
            all_inputs = create_form.find_all(["input", "select", "textarea"])
            logger.debug("Form inputs found:")
            for inp in all_inputs:
                name = inp.get("name")
                if name:
                    logger.debug(
                        f"Input name: {name}, type: {inp.get('type', 'N/A')}, required: {inp.get('required', 'N/A')}"
                    )

            # Extract CSRF token from the form specifically
            csrf_token = create_form.find("input", {"name": "authenticity_token"})[
                "value"
            ]
            logger.info(f"Using CSRF token from form: {csrf_token[:10]}...")

            # Load candidates from YAML file
            with open(candidates_file, "r") as f:
                candidates_data = yaml.safe_load(f)

            # Make a request to add a list voting question and get the question ID
            logger.info("Requesting list voting question template")
            headers = {
                "Turbo-Method": "GET",
                "Turbo-Stream": "true",
                "Accept": "text/vnd.turbo-stream.html, text/html, application/xhtml+xml",
                "X-CSRF-Token": csrf_token,
            }
            question_response = self.session.get(
                f"{self.base_url}/consultations/add_question?question_type=ListVoting",
                headers=headers,
            )
            question_response.raise_for_status()

            # Debug the question response
            logger.debug(f"Question response status: {question_response.status_code}")
            logger.debug(
                f"Question response first 100 chars: {question_response.text[:100]}"
            )

            # Parse the response to extract the question ID
            question_soup = BeautifulSoup(question_response.text, "html.parser")

            # Find the question ID from the form fields
            question_id = None
            input_fields = question_soup.find_all("input")
            for field in input_fields:
                name = field.get("name", "")
                if "questions_attributes" in name and "_destroy" in name:
                    # Extract the ID from the name attribute
                    question_id = name.split("[")[2].split("]")[0]
                    logger.info(f"Extracted vote question ID: {question_id}")
                    break

            if not question_id:
                logger.error("Could not extract question ID from response")
                logger.debug(f"Full question response: {question_response.text}")
                return None

            # Find the lists container by looking for a div with class "lists"
            lists_id = None
            lists_container = question_soup.find("div", class_="lists")
            if lists_container:
                lists_id = lists_container.get(
                    "id"
                )  # Get the full ID attribute (lists_cDPACuACYqM4Ou6U)
                logger.info(f"Extracted lists container ID: {lists_id}")
            else:
                logger.error("Could not find lists container in the response")
                return None

            # For each list, request a list template and extract the list ID
            list_ids = []
            for list_title in candidates_data.keys():
                logger.info(f"Requesting template for list: {list_title}")
                list_response = self.session.get(
                    f"{self.base_url}/consultations/add_list?lists_id={lists_id}&question_index={question_id}",
                    headers=headers,
                )
                list_response.raise_for_status()

                list_soup = BeautifulSoup(list_response.text, "html.parser")

                # Find the list ID from the form fields
                list_id = None
                input_fields = list_soup.find_all("input")
                for field in input_fields:
                    name = field.get("name", "")
                    if "list_voting_new_lists" in name and "_destroy" in name:
                        # Extract the ID from the name attribute
                        list_id = name.split("[")[4].split("]")[0]
                        logger.info(f"Extracted list ID: {list_id}")
                        list_ids.append(list_id)
                        break

                if not list_id:
                    logger.warning(f"Could not extract list ID for list: {list_title}")

            # Prepare form data very carefully to match exactly what the browser would send
            # Start with empty data and add each field individually
            form_data = {}

            # Add authenticity token
            form_data["authenticity_token"] = csrf_token

            # Add basic fields
            form_data["consultation[title]"] = config["title"]
            form_data["consultation[community]"] = config.get("community", "")

            # Only add description if it's provided (avoid empty fields when possible)
            if config.get("description"):
                form_data["consultation[description]"] = config.get("description")

            form_data["consultation[voting_method]"] = config.get(
                "voting_method", "secret_ballot"
            )
            form_data["consultation[starting_method]"] = config.get(
                "starting_method", "scheduled"
            )
            form_data["consultation[starting_picker]"] = config.get(
                "starting_picker", "06/07/2025 7:00 AM"
            )
            form_data["consultation[starting]"] = config.get(
                "starting", "2025-06-07T07:00:00+02:00"
            )

            # Add event start only if ending method is manual_during_event
            if config.get("ending_method") == "manual_during_event":
                form_data["consultation[event_start]"] = config.get(
                    "starting", "2025-04-24T20:00:00+02:00"
                )
                form_data["event_start_picker"] = config.get(
                    "starting_picker", "04/24/2025 8:00 PM"
                )

            form_data["consultation[ending_method]"] = config.get(
                "ending_method", "scheduled"
            )

            # Add ending date only if ending method is scheduled
            if form_data["consultation[ending_method]"] == "scheduled":
                form_data["consultation[ending]"] = config.get(
                    "ending", "2025-06-08:20:00+02:00"
                )
                form_data["ending_picker"] = config.get(
                    "ending_picker", "06/08/2025 8:00 PM"
                )

            form_data["consultation[locale]"] = config.get("locale", "fr")
            form_data["consultation[tally_method]"] = config.get(
                "tally_method", "automatic"
            )

            # Add the question with precisely the right field names
            form_data[
                f"consultation[questions_attributes][{question_id}][_destroy]"
            ] = "false"
            form_data[f"consultation[questions_attributes][{question_id}][content]"] = (
                config.get("question_content", "<p>Votez pour une liste</p>")
            )
            form_data[
                f"consultation[questions_attributes][{question_id}][type_helper]"
            ] = "ListVoting"
            form_data[
                f"consultation[questions_attributes][{question_id}][position]"
            ] = ""
            form_data[
                f"consultation[questions_attributes][{question_id}][list_voting_strikethrough]"
            ] = "0"

            # After getting the list IDs, add them to the form data
            # Add candidate lists from YAML file
            for i, (list_title, candidates) in enumerate(candidates_data.items()):
                if i < len(list_ids):
                    list_id = list_ids[i]

                    # Format candidates as a single string with HTML line breaks
                    joined_candidates = "<p>" + "<br>".join(candidates) + "</p>"

                    # Add list title and candidates to form data - THESE WERE MISSING!
                    form_data[
                        f"consultation[questions_attributes][{question_id}][list_voting_new_lists][{list_id}][_destroy]"
                    ] = ""
                    form_data[
                        f"consultation[questions_attributes][{question_id}][list_voting_new_lists][{list_id}][title]"
                    ] = f"<p>{list_title}</p>"
                    form_data[
                        f"consultation[questions_attributes][{question_id}][list_voting_new_lists][{list_id}][joined_candidates]"
                    ] = joined_candidates

                    logger.debug(
                        f"Added list {list_title} with ID {list_id} and {len(candidates)} candidates"
                    )
                else:
                    logger.warning(f"Skipping list {list_title} - no ID available")

            # Add submit button
            form_data["commit"] = "Submit"

            # Log the form data for debugging
            logger.debug("Form data being submitted:")
            for key, value in form_data.items():
                logger.debug(
                    f"{key}: {value[:30] if isinstance(value, str) and len(value) > 30 else value}"
                )

            # Set proper headers for the form submission
            post_headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
                "Origin": self.base_url,
                "Referer": create_url,
                "X-CSRF-Token": csrf_token,
            }

            # Submit the form with debug mode - DON'T follow redirects so we can see the response
            logger.info("Submitting election creation form")
            response = self.session.post(
                f"{self.base_url}/consultations",
                data=form_data,
                headers=post_headers,
                allow_redirects=False,  # Important! Don't follow redirects to see the response
            )

            # Log the immediate response
            logger.debug(f"Form submission status code: {response.status_code}")
            logger.debug(f"Form submission headers: {dict(response.headers)}")

            # If we got a redirect, that's probably good
            if response.status_code in (301, 302, 303):
                redirect_url = response.headers.get("Location")
                logger.info(f"Got redirect to: {redirect_url}")

                # Follow the redirect manually to debug
                redirect_response = self.session.get(
                    redirect_url
                    if redirect_url.startswith("http")
                    else f"{self.base_url}{redirect_url}"
                )

                logger.debug(
                    f"Redirect response status: {redirect_response.status_code}"
                )
                logger.debug(
                    f"Redirect page title: {BeautifulSoup(redirect_response.text, 'html.parser').find('title').text if BeautifulSoup(redirect_response.text, 'html.parser').find('title') else 'No title'}"
                )

                # Check if we got redirected to an edit_new_voters page
                if "/edit_new_voters" in redirect_url:
                    # Success! The election was created
                    election_id = (
                        redirect_url.split("/")[2]
                        if redirect_url.startswith("/")
                        else redirect_url.split("/")[4]
                    )
                    logger.info(f"Election created with ID: {election_id}")

                    # Add voters
                    self._add_voters(election_id, voters_file)
                    return election_id

            # If we're here, something went wrong
            # Check for error messages in the response
            error_soup = BeautifulSoup(response.text, "html.parser")
            error_messages = error_soup.find_all(class_="error")
            if error_messages:
                logger.error("Form validation errors found:")
                for error in error_messages:
                    logger.error(f"Error: {error.text}")

            flash_div = error_soup.find("div", {"id": "flash"})
            if flash_div and flash_div.text.strip():
                logger.error(f"Flash message: {flash_div.text.strip()}")

            logger.error("Election creation failed")
            logger.debug(f"Response content: {response.text[:2000]}...")
            return None

        except Exception as e:
            logger.error(f"Election creation failed with error: {str(e)}")
            logger.exception("Traceback:")
            return None

    def _add_voters(self, election_id, voters_file):
        """Add voters to the election from a file."""
        try:
            # First get a CSRF token from the consultations page
            logger.info(f"Getting CSRF token for election {election_id}")
            response = self.session.get(f"{self.base_url}/consultations/{election_id}")
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            csrf_token = soup.find("meta", {"name": "csrf-token"})["content"]

            # Read the voters emails from the file
            with open(voters_file, "r") as f:
                voters_emails = f.read().strip()

            # Count how many voters we're importing
            email_count = voters_emails.count("@")
            logger.info(f"Importing {email_count} voters")

            # Prepare the import data
            import_data = {
                "_method": "patch",
                "authenticity_token": csrf_token,
                "consultation[new_voters_emails]": voters_emails,
                "button": "",  # This seems to be empty in the example payload
            }

            # Set headers for the request
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
                "Origin": self.base_url,
                "Referer": f"{self.base_url}/consultations/{election_id}",
            }

            # Make the import request
            logger.info(f"Importing voters for election {election_id}")
            import_url = (
                f"{self.base_url}/consultations/{election_id}/import_new_voters"
            )

            response = self.session.post(
                import_url, data=import_data, headers=headers, allow_redirects=False
            )
            response.raise_for_status()

            print(response.status_code)
            print(response.url)

            # Check if we were redirected to the consultations page (success)
            if "/consultations" in response.url and not response.url.endswith(
                f"{election_id}/edit_new_voters"
            ):
                logger.info(f"Successfully imported {email_count} voters")
                return True

            # If we're still on the import page, something went wrong
            logger.error(f"Failed to import voters. Final URL: {response.url}")
            logger.debug(f"Response content: {response.text[:500]}...")
            return False

        except Exception as e:
            logger.error(f"Error importing voters: {str(e)}")
            logger.exception("Traceback:")
            return False

    def process_all_elections(self, elections_dir="elections/"):
        """Process all elections in the specified directory."""
        elections_dir = os.path.join(ROOT_DIR, elections_dir)
        if not os.path.exists(elections_dir):
            logger.error(f"Directory '{elections_dir}' does not exist.")
            return

        # Login first
        if not self.login():
            return

        # Load the common YAML config
        config_file = os.path.join(elections_dir, "config.yaml")
        if not os.path.exists(config_file):
            logger.error(
                f"Directory '{elections_dir}' does not contain yaml configuration file."
            )
            return

        with open(config_file, "r") as f:
            config = yaml.safe_load(f)

        # Process each subdirectory
        for dir_name in sorted(os.listdir(elections_dir)):
            dir_path = os.path.join(elections_dir, dir_name)

            if not os.path.isdir(dir_path):
                continue

            logger.info(f"\nProcessing election in directory: {dir_name}")

            # Find the YAML, voters, and candidates files
            voters_file = None
            candidates_file = None

            for file_name in os.listdir(dir_path):
                file_path = os.path.join(dir_path, file_name)

                if file_name.endswith(".yaml") or file_name.endswith(".yml"):
                    candidates_file = file_path
                elif "voters" in file_name.lower() and file_name.endswith(".txt"):
                    voters_file = file_path

            if not voters_file or not candidates_file:
                logger.error(f"Missing required files in directory: {dir_name}")
                continue

            # Create custom title from directory name
            custom_title = f"PPD 2025 - {dir_name.replace('_', ' ')}"
            logger.info(f"Creating election with title: {custom_title}")

            # Create a copy of config with the custom title
            election_config = config.copy()
            election_config["title"] = custom_title

            # Create the election
            election_id = self.create_election(
                election_config, voters_file, candidates_file
            )

            if election_id:
                logger.info(f"Election created with ID: {election_id}")

            # Wait a bit before processing the next election to avoid rate limiting
            time.sleep(2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Automate election creation on Balotilo.org"
    )
    parser.add_argument("username", help="Your Balotilo username (email)")
    parser.add_argument("password", help="Your Balotilo password")
    parser.add_argument(
        "--elections-dir",
        default="elections/",
        help="Directory containing election data (default: elections/)",
    )

    args = parser.parse_args()

    automation = BalotiloAutomation(args.username, args.password)
    automation.process_all_elections(args.elections_dir)
