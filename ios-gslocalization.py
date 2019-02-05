import argparse
from os import path
from models.ios_xliff_file import export_xliff_files, load_xliff_files
from cloud_managers.google_sheets_manager import GoogleSheetsManager
from utils.utils import xcode_supports_dev_language_operations, get_input


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument('-x', '--xcodeproj_path', required=True, help='path to the Xcode project', metavar='\b')
    ap.add_argument('-a', '--auth_file_path', required=True, help='path to the Google Sheets authorization JSON file', metavar='\b')
    ap.add_argument('-e', '--email', required=True, help='email used for sharing newly created worksheets', metavar='\b')
    ap.add_argument('-d', '--dev_language', required=False, default='en', help='development language code (default=en)', metavar='\b')
    ap.add_argument('-l', '--languages', required=True, help='list of language codes used for importing/exporting '
                                                             'localizations (comma separated)', metavar='\b')
    ap.add_argument('-o', '--output_dir', required=True, help='output dir for saving the xliff files generated from Xcode', metavar='\b')

    return vars(ap.parse_args())


if __name__ == "__main__":
    args = parse_args()

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
        localization_languages = [dev_language] + localization_languages

    # Toggle this to False to use the previously exported localization files
    should_export = True

    if should_export:
        xliff_files = export_xliff_files(xcodeproj_path, localization_languages, loc_output_path)
    else:
        xliff_files = load_xliff_files(localization_languages, loc_output_path)

    op_type = get_input('Enter operation type [1=export, 2=import, 3=export&import]: ')

    if op_type == '1':
        for l_file in xliff_files:
            l_file.sync_with_google_sheets(gsheets_manager=google_sheets_manager)
    elif op_type == '2':
        for l_file in xliff_files:
            l_file.update_from_google_sheets(gsheets_manager=google_sheets_manager)
            if l_file.has_updates:
                l_file.import_in_xcode(xcodeproj_path=xcodeproj_path)
    elif op_type == '3':
        for l_file in xliff_files:
            l_file.sync_with_google_sheets(gsheets_manager=google_sheets_manager)
            l_file.update_from_google_sheets(gsheets_manager=google_sheets_manager)
            if l_file.has_updates:
                l_file.import_in_xcode(xcodeproj_path=xcodeproj_path)
