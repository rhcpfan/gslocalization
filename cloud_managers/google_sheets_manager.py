import pygsheets
from typing import List


class GoogleSheetsManager(object):
    def __init__(self, service_account_file_path, user_email):
        # type: (str, str) -> GoogleSheetsManager
        self.google_client = pygsheets.authorize(service_account_file=service_account_file_path)
        self.user_email = user_email

    def create_spreadsheet(self, platform, language, header_values, overwrite=False):

        sh_name = '{}_localizations'.format(language)

        # Delete all spreadsheets with the same name if overwrite = True
        if overwrite:
            all_sh = self.google_client.open_all()
            sh_to_delete = [sh for sh in all_sh if sh.title == sh_name]

            for sh in sh_to_delete:
                try:
                    sh.delete()
                except Exception as api_exception:
                    print('Failed to delete spreadsheet {} - {}'.format(sh.title, sh.id))
                    print(api_exception)

        lang_sh = self.google_client.create(sh_name)
        platform_worksheet_name = '{}_strings'.format(platform)
        platform_worksheet = lang_sh.add_worksheet(title=platform_worksheet_name, rows=1, cols=len(header_values))
        lang_sh.del_worksheet(lang_sh.sheet1)
        lang_sh.share(self.user_email, type='user', role='writer')

        self.update_worksheet_header(worksheet=platform_worksheet,
                                     header_values=header_values)

        return lang_sh

    def get_worksheet(self, platform, language, header_values):
        # type: (str, str, List[str]) -> pygsheets.Worksheet
        spreadsheet_name = '{}_localizations'.format(language)
        worksheet_name = '{}_strings'.format(platform)

        try:
            language_spreadsheet = self.google_client.open(spreadsheet_name)
        except pygsheets.exceptions.SpreadsheetNotFound:
            language_spreadsheet = self.create_spreadsheet(platform=platform,
                                                           language=language,
                                                           header_values=header_values)
        language_spreadsheet.default_parse = False

        try:
            platform_worksheet = language_spreadsheet.worksheet('title', worksheet_name)  # type: pygsheets.Worksheet
        except pygsheets.exceptions.WorksheetNotFound:
            platform_worksheet = language_spreadsheet.add_worksheet(title=worksheet_name, rows=1, cols=len(header_values))

        self.update_worksheet_header(platform_worksheet, header_values)
        return platform_worksheet

    def update_worksheet_header(self, worksheet, header_values):
        # type: (pygsheets.Worksheet, List[str]) -> None

        current_header = worksheet.get_row(row=1)
        if current_header != header_values:
            worksheet.insert_rows(row=0, number=1, values=header_values)

        pass
