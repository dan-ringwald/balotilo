# Automatizing poll creation on Balotilo

## Step 1

Ensure you have python3.12 and poetry installed.
Then install dependencies with `poetry install`

## Step 2

Gather data and parametrize the vote in a folder. Default is `elections/`

Look into `elections/` folder to see the required data formats

## Step 3

Create a Balotilo account or use an existing one.

## Step 4

```bash
poetry run python balotilo/main.py \
    your_balotilo_email your_balotilo_password \
    --elections_dir folder_with_data_and_conf`
```

The --elections_dir param is optionnal and defaults to `elections/`

## Maintainance of this script

<dan.ringwald12@gmail.com>
