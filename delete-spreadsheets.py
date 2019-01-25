import argparse

from utils.utils import print_with_timestamp, is_python_2
from cloud_managers.google_sheets_manager import GoogleSheetsManager

ap = argparse.ArgumentParser()
ap.add_argument('-a', '--auth_file_path', required=True, help='path to the Google Sheets authorization JSON file', metavar='\b')
args = vars(ap.parse_args())

service_account_file_path = args['auth_file_path']

google_sheets_manager = GoogleSheetsManager(service_account_file_path)

all_spreadsheets = google_sheets_manager.google_client.open_all()

for spreadsheet in all_spreadsheets:
    spreadsheet_name = spreadsheet.title
    prompt_message = u'Do you want to delete {}? [y/n]: '.format(spreadsheet_name)
    if is_python_2():
        should_delete = raw_input(prompt_message)
    else:
        should_delete = input(prompt_message)

    if should_delete.lower() == 'y':
        spreadsheet.delete()
        print_with_timestamp(u'Deleted {}'.format(spreadsheet_name), color='r')
