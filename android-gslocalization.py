import argparse

import sys
from models.android_xml_file import import_from_res_folder
from utils.utils import pwt
from cloud_managers.google_sheets_manager import GoogleSheetsManager


def parse_args():

    ap = argparse.ArgumentParser()
    ap.add_argument('-p', '--project_name', required=True, help='name of the android project (used in the spreadsheet name', metavar='\b')
    ap.add_argument('-r', '--res_folder_path', required=True, help='path to the \'res\' directory', metavar='\b')
    ap.add_argument('-a', '--auth_file_path', required=True, help='path to the Google Sheets authorization JSON file', metavar='\b')
    ap.add_argument('-e', '--email', required=True, help='email used for sharing newly created worksheets', metavar='\b')
    ap.add_argument('-l', '--dev_language', required=False, default='en', help='development language code (default=en)', metavar='\b')

    return vars(ap.parse_args())


if __name__ == "__main__":
    args = parse_args()
    res_folder_path = args['res_folder_path']
    service_account_file = args['auth_file_path']
    user_email = args['email']
    development_language = args['dev_language']
    project_name = args['project_name']

    google_sheets_manager = GoogleSheetsManager(service_account_file, user_email, project_name)
    android_files = import_from_res_folder(res_folder_path, development_language)

    development_language_file = next((f for f in android_files if f.source_language_code == development_language), None)
    if development_language_file is None:
        pwt('NO STRINGS.XML FILES FOUND IN {}'.format(res_folder_path), color='r')
        sys.exit(1)

    localized_files = [f for f in android_files if f.source_language_code != f.target_language_code]

    for l_file in localized_files:
        l_file.upload_to_google_sheets(gsheets_manager=google_sheets_manager)
        l_file.update_from_google_sheets(gsheets_manager=google_sheets_manager,
                                         dev_language_file=development_language_file)
        l_file.update_source_xml()

    development_language_file.update_source_xml()
