import argparse
from sys import exit
from os import path

from typing import List

from utils.utils import pwt
from models.ios_xliff_file import export_xliff_files, load_xliff_files
from cloud_managers.google_sheets_manager import GoogleSheetsManager
from utils.utils import xcode_supports_dev_language_operations, get_input


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument('-x', '--xcodeproj_path', required=True, help='path to the Xcode project', metavar='\b')
    ap.add_argument('-a', '--auth_file_path', required=True, help='path to the Google Sheets authorization JSON file',
                    metavar='\b')
    ap.add_argument('-e', '--email', required=True, help='email used for sharing newly created worksheets',
                    metavar='\b')
    ap.add_argument('-d', '--dev_language', required=False, default='en', help='development language code (default=en)',
                    metavar='\b')
    ap.add_argument('-l', '--languages', required=False, help='list of language codes used for importing/exporting '
                                                              'localizations (comma separated)', metavar='\b')
    ap.add_argument('-o', '--output_dir', required=True, help='output dir for saving the xliff files generated '
                                                              'from Xcode', metavar='\b')

    return vars(ap.parse_args())


if __name__ == "__main__":
    args = parse_args()

    op_type = get_input('Export XCLOC files? [0=no, 1=yes]: ')
    should_export = op_type == '1'

    op_values = ['1', '2', '3', '4', '5']
    op_type = get_input('Enter operation type [1=export, 2=import, 3=export&import, '
                        '4=remove unused, 5=translation memory]: ')

    if op_type not in op_values:
        pwt('INVALID OPERATION', color='r')
        exit(1)

    xcodeproj_path = args['xcodeproj_path'].rstrip('/')
    project_name = path.splitext(path.basename(xcodeproj_path))[0]
    loc_output_path = args['output_dir']
    service_account_file = args['auth_file_path']
    user_email = args['email']
    localization_languages = args['languages'].split(',')  # type: List[str]
    dev_language = args['dev_language']

    google_sheets_manager = GoogleSheetsManager(service_account_file, user_email, project_name)

    # Starting with XCode 10.2, operations with the development languages (import/export) are supported
    if xcode_supports_dev_language_operations():
        localization_languages = [dev_language] + lang_codes

    if should_export:
        xliff_files = export_xliff_files(xcodeproj_path, lang_codes, loc_output_path)
    else:
        xliff_files = load_xliff_files(lang_codes, loc_output_path)

    if op_type == '1':
        for l_file in xliff_files:
            l_file.sync_with_google_sheets(gsheets_manager=google_sheets_manager, remove_unused_strings=False)
    elif op_type == '2':
        for l_file in xliff_files:
            l_file.update_from_google_sheets(gsheets_manager=google_sheets_manager)
            if l_file.has_updates:
                l_file.import_in_xcode(xcodeproj_path=xcodeproj_path)
    elif op_type == '3':
        for l_file in xliff_files:
            l_file.sync_with_google_sheets(gsheets_manager=google_sheets_manager, remove_unused_strings=False)
            l_file.update_from_google_sheets(gsheets_manager=google_sheets_manager)
            if l_file.has_updates:
                l_file.import_in_xcode(xcodeproj_path=xcodeproj_path)
    elif op_type == '4':
        for l_file in xliff_files:
            l_file.sync_with_google_sheets(gsheets_manager=google_sheets_manager, remove_unused_strings=True)
    elif op_type == '5':
        for l_file in xliff_files:
            l_file.update_from_google_sheets_memory(gsheets_manager=google_sheets_manager)
