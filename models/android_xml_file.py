from sys import exit
from copy import deepcopy
from os import path, walk
from lxml import etree
from typing import List
from utils.gs_header_types import AndroidHeaderValues
from utils.utils import get_language_name, get_language_code
from pygsheets.custom_types import ValueRenderOption

from utils.utils import print_with_timestamp, is_python_2
from models.translation_units import AndroidXmlTranslationUnit

if is_python_2():
    from io import open


class AndroidXmlFile(object):

    def __init__(self, file_path, source_language):
        # type: (str, str) -> AndroidXmlFile
        self.source_language = get_language_name(source_language)
        self.source_language_code = source_language  # type: str
        self.target_language = None  # type: str
        self.target_language_code = None  # type: str
        self.translation_units = []  # type: List[AndroidXmlTranslationUnit]
        self.untranslated = []  # type: List[AndroidXmlTranslationUnit]
        self.original_file_path = file_path  # type: str
        self.load(file_path=file_path)

    @property
    def header_values(self):
        source_header_value = '{}'.format(self.source_language)
        target_header_value = '{}'.format(self.target_language)

        return [source_header_value, target_header_value, AndroidHeaderValues.STRING_ID]

    def load(self, file_path):
        # type: (str) -> None

        parent_folder_name = path.basename(path.dirname(file_path))
        lang_tokens = parent_folder_name.split('-')

        if len(lang_tokens) < 2:
            self.target_language_code = self.source_language_code
        else:
            self.target_language_code = lang_tokens[-1]  # last element

        self.target_language = get_language_name(self.target_language_code)

        xml_root = etree.parse(file_path).getroot()

        for string_element in xml_root.iter('string'):
            string_id = string_element.get('name')

            element_to_string = etree.tostring(string_element, encoding='unicode')
            element_to_string = element_to_string.split('\">')[-1]
            element_to_string = element_to_string[:element_to_string.index('</string>')]

            string_value = element_to_string

            # a reason for string_value being None it's the
            # presence of HTML code inside the string
            # ex: <string name="hello_bold"><b>hello</b></string>
            if string_value is None:
                child_nodes = string_element.getchildren()
                if len(child_nodes) > 0:
                    string_value = etree.tostring(child_nodes[0], encoding='unicode')

            t_unit = AndroidXmlTranslationUnit(target_text=string_value,
                                               identifier=string_id,
                                               target_language=self.target_language_code,
                                               friendly_target_language=self.target_language)

            t_unit.source_language = self.source_language_code
            t_unit.friendly_source_language = self.source_language

            if self.target_language_code == self.source_language_code:
                t_unit.source_text = string_value.replace('&lt;', '<').replace('&gt;', '>')

            self.translation_units.append(t_unit)
        pass

    def update_source_language(self, source_xml_file):
        # type: (AndroidXmlFile) -> None

        print_with_timestamp("UPDATING SOURCES FOR {}".format(self.original_file_path), color='y')

        # Add original text (source language) to translation units
        for t_unit in self.translation_units:
            t_unit_source_matches = [t for t in source_xml_file.translation_units if t.identifier == t_unit.identifier]
            if len(t_unit_source_matches) > 0:
                t_unit.source_text = t_unit_source_matches[0].source_text
                pass
            else:
                print_with_timestamp("{} - {} NOT FOUND IN SOURCE LANGUAGE FILE".format(t_unit.identifier, t_unit.target_text), color='r')

        target_lang_ids = [t_unit.identifier for t_unit in self.translation_units]
        self.untranslated = deepcopy(
            [t for t in source_xml_file.translation_units if t.identifier not in target_lang_ids])

        for t_unit in self.untranslated:
            t_unit.target_text = ''
            t_unit.target_language = self.target_language_code
            t_unit.friendly_target_language = self.target_language
            print_with_timestamp("MISSING {} TRANSLATION FOR: {} - {}".format(self.target_language, t_unit.identifier,
                                                               t_unit.source_text), color='r')

        pass

    def upload_to_google_sheets(self, gsheets_manager):
        # type: (GoogleSheetsManager) -> None

        print_with_timestamp("SYNCING {} WITH GOOGLE SHEETS".format(self.original_file_path), color='y')
        lang_ws = gsheets_manager.get_worksheet(platform='android',
                                                language=self.target_language,
                                                header_values=self.header_values)

        ws_records = lang_ws.get_all_records(numericise_data=False, value_render=ValueRenderOption.FORMULA)
        ws_records_ids = [r[AndroidHeaderValues.STRING_ID] for r in ws_records]

        records_to_add = [u.record_value for u in self.translation_units if u.identifier not in ws_records_ids]
        untranslated_records = [u.record_value for u in self.untranslated if u.identifier not in ws_records_ids]
        records_to_add = records_to_add + untranslated_records

        if len(records_to_add) > 0:
            lang_ws.insert_rows(row=lang_ws.rows - 1, number=len(records_to_add), values=records_to_add, inherit=True)

        lang_ws.sort_range((2, 1), (lang_ws.rows, lang_ws.cols))

        for r_to_add in records_to_add:
            print_with_timestamp("ADDED {} TO {} - {}".format(r_to_add, lang_ws.spreadsheet.title, lang_ws.title), color='y')

        print_with_timestamp("ADDED {} RECORDS TO {} - {}".format(len(records_to_add), lang_ws.spreadsheet.title, lang_ws.title), color='g')

        pass

    def update_from_google_sheets(self, gsheets_manager, dev_language_file):
        # type: (GoogleSheetsManager, AndroidXmlFile) -> None

        print_with_timestamp("UPDATING {}".format(self.original_file_path), color='y')
        online_translation_units = self.__get_google_sheets_translation_units(gsheets_manager=gsheets_manager,
                                                                              dev_language_file=dev_language_file)

        mismatched_records = []
        for offline_t_unit in self.translation_units:
            online_t_units = [u for u in online_translation_units if u.identifier == offline_t_unit.identifier]

            if len(online_t_units) == 0:
                mismatched_records.append(offline_t_unit)
            else:
                offline_target_text = offline_t_unit.target_text if offline_t_unit.target_text is not None else ''
                if online_t_units[0].target_text != offline_target_text:
                    offline_t_unit.target_text = online_t_units[0].target_text
                    mismatched_records.append(offline_t_unit)

        for untranslated_unit in self.untranslated:
            matched_units = [u for u in online_translation_units if u.identifier == untranslated_unit.identifier and
                             u.target_text is not None and u.target_text != '']

            if len(matched_units) > 0:
                m_unit = matched_units[0]
                m_unit_target_text = m_unit.target_text if m_unit.target_text is not None else ''
                untranslated_unit.target_text = m_unit_target_text
                mismatched_records.append(untranslated_unit)

        for t_unit in mismatched_records:
            matched_units = [online_unit for online_unit in online_translation_units if
                             online_unit.identifier == t_unit.identifier]
            if len(matched_units) > 0 and matched_units[0].is_translated():
                print_with_timestamp(u"TRANSLATED: {}".format(matched_units[0]), color='g')
                t_unit.target_text = matched_units[0].target_text

    def __get_google_sheets_translation_units(self, gsheets_manager, dev_language_file):
        # type: (GoogleSheetsManager, AndroidXmlFile) -> List[XliffTranslationUnit]
        lang_ws = gsheets_manager.get_worksheet(platform='android',
                                                language=self.target_language,
                                                header_values=self.header_values)
        ws_records = lang_ws.get_all_values()

        xml_translation_units = []

        if len(ws_records) < 2:
            return xml_translation_units

        # remove header values
        ws_headers = ws_records[0]
        ws_records = ws_records[1:]

        target_language = ws_headers[1]
        target_language_code = get_language_code(target_language)

        for record in ws_records:

            xml_translation_unit = AndroidXmlTranslationUnit(target_text=record[1],
                                                             identifier=record[2],
                                                             target_language=target_language_code,
                                                             friendly_target_language=target_language)

            matched_dev_language_records = [t for t in dev_language_file.translation_units if
                                            t.identifier == xml_translation_unit.identifier]

            if len(matched_dev_language_records) > 0:
                dev_lang_unit = matched_dev_language_records[0]
                xml_translation_unit.source_text = dev_lang_unit.source_text
                xml_translation_unit.source_language = dev_language_file.source_language_code
                xml_translation_unit.friendly_source_language = dev_language_file.source_language
                xml_translation_units.append(xml_translation_unit)

        return xml_translation_units

    def update_source_xml(self):
        # type: () -> None

        xml_tree = etree.parse(self.original_file_path)
        xml_root = xml_tree.getroot()

        units_to_update = self.translation_units + [u for u in self.untranslated if u.target_text != '']

        should_add_comment = False
        for t_unit in units_to_update:

            xml_search_query = './/string[@name=\"{}\"]'.format(t_unit.identifier)
            xml_t_unit_node = xml_root.find(xml_search_query)

            if xml_t_unit_node is None and t_unit.is_translated():
                should_add_comment = True
                break

        if should_add_comment:
            comment = etree.Comment(' IMPORTED FROM GOOGLE SHEETS ')
            comment.tail = '\n'
            xml_root.append(comment)

        for t_unit in units_to_update:

            xml_search_query = './/string[@name=\"{}\"]'.format(t_unit.identifier)
            xml_t_unit_node = xml_root.find(xml_search_query)

            if xml_t_unit_node is None and t_unit.is_translated():
                string_node = etree.Element('string')
                string_node.set('name', t_unit.identifier)
                string_node.tail = '\n'
                string_node.text = t_unit.target_text.replace('<', '&lt;').replace('>', '&gt;')
                xml_root.append(string_node)
            elif xml_t_unit_node is not None:

                element_to_string = etree.tostring(xml_t_unit_node, encoding='unicode')
                element_to_string = element_to_string.split('\">')[-1]
                element_to_string = element_to_string[:element_to_string.index('</string>')]

                target_language_text = element_to_string
                if target_language_text != t_unit.target_text:
                    xml_t_unit_node.text = t_unit.target_text

        xml_string_content = etree.tostring(xml_tree,
                                            pretty_print=True,
                                            encoding='utf-8',
                                            xml_declaration=True).decode('utf-8')

        # Replace html tag characters (&, &lt;, &gt;)
        xml_string_content = xml_string_content.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        xml_string_content = xml_string_content.replace('&', '&amp;')
        # Indent the added 'string'
        xml_string_content = xml_string_content.replace('\n<string', '\n\t<string')
        # Indent the added comment (if any)
        if should_add_comment:
            xml_string_content = xml_string_content.replace('\n<!--', '\n\n\t<!--')
        # Overwrite the source file
        with open(self.original_file_path, 'w', encoding='utf-8') as out_file:
            out_file.write(xml_string_content)

        pass

    def import_in_xcode(self, xcodeproj_path):
        # type: (str) -> None

        import subprocess

        xcb_params = ['-importLocalizations', '-localizationPath', self.original_file_path,
                      '-project', xcodeproj_path]

        print_with_timestamp("IMPORTING {} INTO {}".format(self.original_file_path, path.basename(path.normpath(xcodeproj_path))),
                             color='g')
        xcb = subprocess.Popen(['xcodebuild'] + xcb_params, stderr=subprocess.PIPE)
        xcb.wait()


def __normalize_xml_file(file_path):
    # type: (str) -> None

    import re

    f_stream = open(file_path, 'r', encoding='utf-8')
    str_content = f_stream.read()
    f_stream.close()

    html_tags_regex_pattern = r"<(?!string|\/string|\?|resources|\/resources|!)(\/?.*?)>"
    html_tags_replacement_pattern = r"&lt;\1&gt;"

    filtered_content = re.sub(pattern=html_tags_regex_pattern,
                              repl=html_tags_replacement_pattern,
                              string=str_content,
                              flags=(re.VERBOSE | re.U))

    with open(file_path, 'w', encoding='utf-8') as xml_file:
        xml_file.write(filtered_content)

    pass


def import_from_res_folder(res_folder_path, development_language):
    # type: (str) -> List[AndroidXmlFile]

    print_with_timestamp("LOADING XML FILES FROM {}".format(res_folder_path), color='y')

    xml_files = []  # type: List[AndroidXmlFile]
    for root, dirs, files in walk(res_folder_path):
        for file in files:
            # skip folders that are not for localized string
            if 'values' not in path.basename(root):
                continue
            # skip files that are not 'strings.xml' or 'array.xml'
            if not file.endswith('strings.xml'):  # and not file.endswith('array.xml'):
                continue
            file_path = path.join(root, file)
            __normalize_xml_file(file_path)
            xml_files.append(AndroidXmlFile(file_path=file_path, source_language=development_language))
            print_with_timestamp("FOUND {}".format(file_path), color='y')

    if len(xml_files) == 0:
        print_with_timestamp("COULD NOT FIND ANY XML FILES IN {}".format(res_folder_path), color='r')
        exit(1)

    source_language_file = [f for f in xml_files if f.source_language_code == f.target_language_code].pop()

    for xml_file in (f for f in xml_files if f.source_language_code != f.target_language_code):
        xml_file.update_source_language(source_xml_file=source_language_file)

    return xml_files
