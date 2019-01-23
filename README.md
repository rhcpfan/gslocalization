![gs-localization-logo](https://user-images.githubusercontent.com/3796970/51634838-e7a0b780-1f5d-11e9-8105-283540eb5b7d.png)

# iOS and Android localization using Google Sheets

## Basic idea

1. **Export** your localization files **to Google Sheets**.
2. **Translate** the missing localizations or update the existing ones **in Google Spreadsheets**.
3. Run the script again to **import the localizations** from the spreadsheet **into your project**.

## Installation

Python 2.7 or preferably Python 3 must be installed on your machine with the `pip` command also available.

Clone the repository and run `pip install -r requirements.txt`.

## Authorizing `gslocalization` with Google Sheets

1. Obtain a `service account key` JSON file from your Google Developer Console
	- Login to [https://console.developers.google.com](https://console.developers.google.com)
	- Select your project (or create a new one)
	- Make sure that the `Google Drive API` and `Google Sheets API` are enabled
	- Go to `Credentials` and from the `Create credentials` menu, select `Service account key`
	- Select your service account (or create a new one with the `App Engine Admin` role)
	- Make sure that `JSON` is selected in the `Key type` options.
	- Click `Create`
	- A `JSON` file will begin downloading. Save this file and use it later for authentication.

## ios-gslocalization.py

### Usage

```python ios-gslocalization.py -x {PATH_TO_XCODEPROJ} -o {XLIFF_OUTPUT_DIR} -a {JSON_AUTH_FILE_PATH} -e {SHARE_EMAIL_ADDRESS} -l {LOCALIZATION_LANGUAGES}```

1. `PATH_TO_XCODEPROJ` - path to your `.xcodeproj` file
	- used for calling `xcodebuild` (exporting and importing localizations)
	- the generated XLIFF files are saved to `XLIFF_OUTPUT_DIR`
2. `XLIFF_OUTPUT_DIR` - output directory for the generated XLIFF files
3. `JSON_AUTH_FILE_PATH` - path to the Google Sheets `Service account key`
4. `SHARE_EMAIL_ADDRESS` - the email address to share the created spreadsheets
	- since we are using a `Service account key`, all the spreadsheets are created and owned by the service account (ex. localizations@gslocalization.iam.gserviceaccount.com)
	- after the service account creates the spreadsheets, it shares them with the provided email address
	- provide your email address to be able to visualise the results in [Google Spreadsheets](https://docs.google.com/spreadsheets/)
5. `LOCALIZATION_LANGUAGES` - a string containing multiple language codes used for localization 
	- ex: "es,ru,ja" for Spanish, Russian and Japanese
	- this does not enable localization for a new language in your Xcode project
	- provide languages that already exist in your project
	
### Notes

- This script exports the current localizations for your project using `xcodebuild`. 

- It parses the obtained XLIFF files and uploads them to Google Sheets. 

- There is one spreadsheet for every language, with the following name format: `{LANGUAGE_NAME}_localizations` (ex. `Spanish_localizations`, `Russian_localizations`, etc.). Inside each spreadsheet, there is one worksheet per platform (ex. `ios_strings`, `android_strings`).

- All the strings are added to their corresponding spreadsheet, with the following header:

  `SOURCE_LANGUAGE | TARGET_LANGUAGE | Example | Notes | Element ID | Path`
  
  - `SOURCE_LANGUAGE` = text in the source language
  - `TARGET_LANGUAGE` = text translated in the target language
  - `Example` = empty if the string contains placeholders (`%@, %d, etc.`). This is a place to provide an example for translators.
  - `Notes` = `NSLocalisedString` comments
  - `Element ID` = the ID of the string
  - `Path` = relative path to the source file of the string (`.strings` file or `.storyboard`)

- After updating the translation in Google Sheets, run the same script again to import the new strings into your XCode project.

## android-gslocalization.py

### Usage

```python android-gslocalization.py -r {PATH_TO_RES_FOLDER} -a {JSON_AUTH_FILE_PATH} -e {SHARE_EMAIL_ADDRESS} -l {DEVELOPMENT_LANGUAGE}```

1. `PATH_TO_RES_FOLDER ` - path to your Android `res` folder
	- looks into this folder for all `strings.xml` files
	- for any `strings.xml` file, the target language is detected by the parrent folder name (ex. `values-es` for Spanish)
2. `JSON_AUTH_FILE_PATH` - path to the Google Sheets `Service account key`
3. `SHARE_EMAIL_ADDRESS` - the email address to share the created spreadsheets
	- since we are using a `Service account key`, all the spreadsheets are created and owned by the service account (ex. localizations@gslocalization.iam.gserviceaccount.com)
	- after the service account creates the spreadsheets, it shares them with the provided email address
	- provide your email address to be able to visualise the results in [Google Spreadsheets](https://docs.google.com/spreadsheets/)
4. `DEVELOPMENT_LANGUAGE ` - the language code of your development language (default = `en`)
	
### Notes

- This script loads all the `strings.xml` files inside `PATH_TO_RES_FOLDER`. 

- It parses the obtained XML files and uploads them to Google Sheets. 

- There is one spreadsheet for every language, with the following name format: `{LANGUAGE_NAME}_localizations` (ex. `Spanish_localizations`, `Russian_localizations`, etc.). Inside each spreadsheet, there is one worksheet per platform (ex. `ios_strings`, `android_strings`).

- All the strings are added to their corresponding spreadsheet, with the following header:

  `SOURCE_LANGUAGE | TARGET_LANGUAGE | Element ID`
  
  - `SOURCE_LANGUAGE` = text in the source language
  - `TARGET_LANGUAGE` = text translated in the target language
  - `Element ID` = the ID of the string

- After updating the translation in Google Sheets, run the same script again to overwrite the `strings.xml` files in your resources folder.


### Dependencies

```
# parsing command line arguments
argparse

# provides access to Google Sheets API
pygsheets

# for parsing XML/XLIFF files
lxml

# type hinting
typing

# colored output in consolde
colorama

# conversion between language code and language name
langcodes; python_version>'3'
langcodes-py2; python_version<'3'

```

