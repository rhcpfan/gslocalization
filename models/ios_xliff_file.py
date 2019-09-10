import sys

from os import path
from lxml import etree
from typing import List
from utils.gs_header_types import IosHeaderValues
from utils.utils import pwt, get_language_name, get_language_code
from models.translation_units import XliffTranslationUnit
from pygsheets.custom_types import ValueRenderOption
from pygsheets import Worksheet
from cloud_managers.google_sheets_manager import GoogleSheetsManager


class IosXliffFile(object):

    def __init__(self, file_path):
        # type: (str) -> IosXliffFile
        self.source_language = None  # type: str
        self.target_language = None  # type: str
        self.translation_units = []  # type: List[XliffTranslationUnit]
        self.original_file_path = file_path  # type: str
        self.has_updates = False  # type: bool
        self.load(file_path=file_path)

    @property
    def untranslated(self):
        """
        :return: A list of XliffTranslationUnit objects that are not translated (target_text is None or empty).
        """
        return [t_unit for t_unit in self.translation_units if t_unit.target_text is None or t_unit.target_text is '']

    @property
    def source_language_header(self):
        return IosHeaderValues.SOURCE_LANGUAGE.format(self.source_language)

    @property
    def target_language_header(self):
        return IosHeaderValues.TARGET_LANGUAGE.format(self.target_language)

    @property
    def header_values(self):
        """
        :return: A list of strings that represent the worksheet header values.
        """
        return [self.source_language_header,
                self.target_language_header,
                IosHeaderValues.EXAMPLE,
                IosHeaderValues.COMMENT,
                IosHeaderValues.KEY,
                IosHeaderValues.PATH]

    def load(self, file_path):
        """
        Updates its properties by loading and parsing an XLIFF file
        :param str file_path: The XLIFF file path
        """
        xliff_root = etree.parse(file_path).getroot()

        for file_element in xliff_root.iter('{urn:oasis:names:tc:xliff:document:1.2}file'):
            file_path = file_element.get('original')
            source_language_code = file_element.get('source-language')
            target_language_code = file_element.get('target-language')

            if target_language_code is None:
                target_language_code = source_language_code

            self.source_language = get_language_name(source_language_code)
            self.target_language = get_language_name(target_language_code)

            for trans_unit_element in file_element.iter('{urn:oasis:names:tc:xliff:document:1.2}trans-unit'):

                trans_unit_id = trans_unit_element.get('id')

                source_element = trans_unit_element.find('{urn:oasis:names:tc:xliff:document:1.2}source')
                target_element = trans_unit_element.find('{urn:oasis:names:tc:xliff:document:1.2}target')
                note_element = trans_unit_element.find('{urn:oasis:names:tc:xliff:document:1.2}note')

                source_text = source_element.text if source_element is not None else ''
                source_text = source_text if source_text is not None else ''
                target_text = target_element.text if target_element is not None else ''
                target_text = target_text if target_text is not None else ''
                note_text = note_element.text if note_element is not None else ''
                note_text = note_text if note_text is not None else ''
                example_text = '' if '%' not in source_text else 'TODO_INSERT_EXAMPLE'

                t_unit = XliffTranslationUnit(identifier=trans_unit_id,
                                              source_language=source_language_code,
                                              target_language=target_language_code,
                                              friendly_source_language=self.source_language,
                                              friendly_target_language=self.target_language,
                                              source_text=source_text,
                                              target_text=target_text,
                                              notes=note_text,
                                              example_text=example_text,
                                              file_path=file_path)

                self.translation_units.append(t_unit)

    def sync_with_google_sheets(self, gsheets_manager, remove_unused_strings):
        """
        Updates the corresponding worksheet with self.translation_units. It adds missing strings to the worksheet and
        updates any source text that has changed. This function does not remove any unused strings from Google Sheets.

        :param gsheets_manager: a GoogleSheetsManager instance that is authorized to make changes in the corresponding
                                worksheet
        :type gsheets_manager: GoogleSheetsManager

        :rtype: None
        """

        pwt("SYNCING {} WITH GOOGLE SHEETS".format(self.original_file_path), color='y')
        lang_ws = gsheets_manager.get_worksheet(platform='ios', language=self.target_language,
                                                header_values=self.header_values)  # type: Worksheet

        ws_records = lang_ws.get_all_records(numericise_data=False, value_render=ValueRenderOption.FORMULA)
        ws_records_ids = [r[IosHeaderValues.KEY] for r in ws_records]

        records_to_add = [u.record_value for u in self.translation_units if u.identifier not in ws_records_ids]
        if len(records_to_add) > 0:
            lang_ws.insert_rows(row=lang_ws.rows, number=len(records_to_add), values=records_to_add, inherit=True)

        for idx, t_unit in enumerate(ws_records):
            match = next((u for u in self.translation_units if u.identifier == t_unit[IosHeaderValues.KEY]), None)

            if match is None:
                if remove_unused_strings:
                    lang_ws.delete_rows(idx + 2)
                    pwt('DELETED {} ({}) [FROM ROW {}]'.format(t_unit[IosHeaderValues.KEY],
                                                               t_unit[self.source_language_header],
                                                               idx + 2), color='r')
                continue

            if match.source_text != t_unit[self.source_language_header]:
                source_cell_address = 'A{}'.format(idx + 2)
                target_cell_address = 'B{}'.format(idx + 2)
                lang_ws.update_value(source_cell_address, match.source_text)
                lang_ws.update_value(target_cell_address, '')
                pwt('UPDATED SOURCE TEXT FOR {} FROM {} TO {}'.format(t_unit[IosHeaderValues.KEY],
                                                                      t_unit[self.source_language_header],
                                                                      match.source_text), color='g')

        lang_ws.sort_range((2, 1), (lang_ws.rows, lang_ws.cols))

        for r_to_add in records_to_add:
            pwt("ADDED {} TO {} - {}".format(r_to_add, lang_ws.spreadsheet.title, lang_ws.title), color='g')

        pwt("ADDED {} RECORDS TO {} - {}".format(len(records_to_add), lang_ws.spreadsheet.title, lang_ws.title), color='g')

        pass

    def update_from_google_sheets(self, gsheets_manager):
        """
        Updates its own properties (translation units) from the corresponding Google worksheet
        :param GoogleSheetsManager gsheets_manager: a GoogleSheetsManager instance that is authorized to make changes in the corresponding
                                                    worksheet
        """

        pwt("UPDATING {}".format(self.original_file_path), color='y')
        online_translation_units = self.__get_google_sheets_translation_units(gsheets_manager=gsheets_manager)
        self.has_updates = False

        mismatched_records = []
        for offline_t_unit in self.translation_units:
            online_t_units = [u for u in online_translation_units if u.identifier == offline_t_unit.identifier]

            if len(online_t_units) == 0:
                mismatched_records.append(offline_t_unit)
            elif online_t_units[0].target_text != offline_t_unit.target_text:
                offline_t_unit.target_text = online_t_units[0].target_text
                mismatched_records.append(offline_t_unit)

        for t_unit in mismatched_records:
            matched_units = [online_unit for online_unit in online_translation_units if
                             online_unit.identifier == t_unit.identifier]
            if len(matched_units) > 0 and matched_units[0].is_translated():
                pwt(u"TRANSLATED: {}".format(matched_units[0]), color='g')
                t_unit.target_text = matched_units[0].target_text
                self.has_updates = True

        self.update_source_xml()

    def __get_google_sheets_translation_units(self, gsheets_manager):
        """

        :param GoogleSheetsManager gsheets_manager: a GoogleSheetsManager instance that is authorized to make changes in the corresponding
                                                    worksheet
        :return: All the strings in the Google worksheet, converted to XliffTranslationUnit objects
        :rtype: List[XliffTranslationUnit]
        """
        lang_ws = gsheets_manager.get_worksheet(platform='ios',
                                                language=self.target_language,
                                                header_values=self.header_values)
        ws_records = lang_ws.get_all_records(numericise_data=False, value_render=ValueRenderOption.UNFORMATTED_VALUE)

        xliff_translation_units = []

        if len(ws_records) == 0:
            return xliff_translation_units

        source_language_code = get_language_code(self.source_language)
        target_language_code = get_language_code(self.target_language)

        for record in ws_records:

            xliff_translation_unit = XliffTranslationUnit(source_text=record[self.source_language_header],
                                                          target_text=record[self.target_language_header],
                                                          example_text=record[IosHeaderValues.EXAMPLE],
                                                          notes=record[IosHeaderValues.COMMENT],
                                                          identifier=record[IosHeaderValues.KEY],
                                                          file_path=record[IosHeaderValues.PATH],
                                                          source_language=source_language_code,
                                                          target_language=target_language_code,
                                                          friendly_source_language=self.source_language,
                                                          friendly_target_language=self.target_language)
            xliff_translation_units.append(xliff_translation_unit)

        return xliff_translation_units

    def update_source_xml(self):
        """
        Overwrites the source XLIFF file to match the current state of the model
        """

        xliff_tree = etree.parse(self.original_file_path)
        xliff_root = xliff_tree.getroot()

        for t_unit in self.translation_units:
            t_unit_id = t_unit.identifier.replace('\"', '&quot;').replace('\n', '&#10;')

            xml_search_query = u'.//{{urn:oasis:names:tc:xliff:document:1.2}}trans-unit[@id=\"{}\"]'.format(t_unit_id)
            xml_t_unit_node = xliff_root.find(xml_search_query)

            if xml_t_unit_node is None:
                continue

            target_node = xml_t_unit_node.find('{urn:oasis:names:tc:xliff:document:1.2}target')

            if target_node is None and t_unit.is_translated():
                target_node = etree.Element('target')
                target_node.text = unicode(t_unit.target_text)
                xml_t_unit_node.append(target_node)
            elif target_node is not None and target_node.text is not None and target_node.text != t_unit.target_text:
                if t_unit.is_translated():
                    target_node.text = unicode(t_unit.target_text)
                else:
                    target_node.getparent().remove(target_node)

        xliff_tree.write(self.original_file_path,
                         encoding='utf-8',
                         pretty_print=True,
                         xml_declaration=True)

    def import_in_xcode(self, xcodeproj_path):
        """
        Runs 'xcodebuild' to import the XLIFF file to the provided Xcode project
        :param str xcodeproj_path:
        """

        import subprocess

        xcb_params = ['-importLocalizations', '-localizationPath', self.original_file_path,
                      '-project', xcodeproj_path]

        pwt("IMPORTING {} INTO {}".format(self.original_file_path, path.basename(path.normpath(xcodeproj_path))), color='y')
        xcb = subprocess.Popen(['xcodebuild'] + xcb_params, stdout=subprocess.PIPE)
        xcb.wait()


def export_xliff_files(xcodeproj_path, languages, output_dir):
    """
    Runs 'xcodebuild' to export localizations from the source Xcode project
    :param str xcodeproj_path: the path of the 'xcodeproj' file of the source project
    :param List[str] languages: a list of language codes to export localizations for
    :param str output_dir: path to a location where the XLIFF files will be exported
    :return: a list of the generated XLIFF files, loaded as IosXliffFile models
    :rtype: List[IosXliffFile]
    """

    import subprocess
    from os.path import join

    xcb_params = ['-exportLocalizations', '-localizationPath', output_dir,
                  '-project', xcodeproj_path]

    for language in languages:
        xcb_params.append('-exportLanguage')
        xcb_params.append(language)

    pwt('GENERATING XLIFF FILES FOR {} TO {}'.format(', '.join(languages), output_dir), color='y')
    xcb = subprocess.Popen(['xcodebuild'] + xcb_params, stdout=subprocess.PIPE)
    xcb.wait()

    xliff_files = []  # type: List[IosXliffFile]
    for language in languages:
        xliff_file_path = join(output_dir, '{}.xcloc/'.format(language),
                               'Localized Contents', '{}.xliff'.format(language))
        xliff_file = IosXliffFile(file_path=xliff_file_path)
        xliff_files.append(xliff_file)

    return xliff_files


def load_xliff_files(languages, input_dir):
    """
    Loads XLIFF files for the specified languages, from an input directory
    :param List[str] languages: a list of language codes to export localizations for
    :param str input_dir: the input directory path
    :return: a list of the XLIFF files found, loaded as IosXliffFile models
    :rtype: List[IosXliffFile]
    """
    from os.path import join

    pwt('LOADING LOCALIZATIONS FROM {}'.format(input_dir), color='y')

    xliff_files = []  # type: List[IosXliffFile]
    for language in languages:
        xliff_file_path = join(input_dir, '{}.xcloc/'.format(language),
                               'Localized Contents', '{}.xliff'.format(language))

        if not path.isfile(xliff_file_path):
            continue

        xliff_file = IosXliffFile(file_path=xliff_file_path)
        xliff_files.append(xliff_file)
        pwt('LOADED {}'.format(xliff_file_path), color='y')

    return xliff_files
