# Automatizing poll creation on Balotilo

## Step 1

Ensure you have python3.12 and poetry installed.
Then install dependencies with `poetry install`

## Step 2

Gather data and parametrize the vote in a folder. Default is `elections/`

Look into `elections/` folder to see the required data formats:

- .txt files with one voter email per line
- .yaml file with list of "candidate\_list\_title: list of candidates in the list"

The export should be made for 3 months+ members, allowing for a gap in membership

## Step 3

Create a Balotilo account or use an existing one.

## Step 4

```bash
poetry run python balotilo/main.py \
    your_balotilo_email your_balotilo_password \
    --elections_dir folder_with_data_and_conf`
```

The --elections_dir param is optionnal and defaults to `elections/`

## Organisation

- List registration can be made through a Notion form feeding a Notion DB.
  Be sure to make a distinct field for first name and family name to have clean data
- When getting support request during the election:
    * Check membership on Balotilo (beware of duplicate accounts, where the "old" account with 3 months of membership is not the one checked)
    * Check if the email is in the voter list on Balotilo
    * If not and eligible, add the voter
    * If present, sometimes reuploading it as a proxy voter for himself works
    * You can also ask for an alternative email address to be added instead
    * There were cases of couples of members sharing the same email address, therefor receiving only one vote link.
      A neat trick is to use "+" in the email address: original@gmail.com and original+bis@gmail.com (caracters after "+" are ignored, emails are considered separate but end up on the same inbox)
      You just add original+bis@gmail.com to the voters list on Balotilo so that they get 2 vote links on the same email address.
    * There were cases of new members with 2 months 25 days of membership asking to vote. These can get added to the ballot only if they request so themselves

## Maintainance of this script

<dan.ringwald12@gmail.com>
