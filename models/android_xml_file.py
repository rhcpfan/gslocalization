from sys import exit
from copy import deepcopy
from os import path, walk
from lxml import etree
from typing import List
from utils.gs_header_types import AndroidHeaderValues
from utils.utils import get_language_name, string_has_placeholders, escape_xml_characters, unescape_xml_characters
from pygsheets.custom_types import ValueRenderOption

from utils.utils import pwt, is_python_2
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
        source_header_value = AndroidHeaderValues.SOURCE_LANGUAGE.format(self.source_language)
        target_header_value = AndroidHeaderValues.TARGET_LANGUAGE.format(self.target_language)

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

        f_stream = open(file_path, 'r', encoding='utf-8')
        str_content = f_stream.read()
        f_stream.close()

        normalized_xml = normalize_xml_file_content(str_content)

        xml_root = etree.fromstring(normalized_xml)

        for string_element in xml_root.iter('string'):
            string_id = string_element.get('name')

            string_value = etree.tostring(string_element, encoding='unicode')
            string_value = string_value.split('\">')[-1]
            string_value = string_value[:string_value.index('</string>')]

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
        """
        Updates the source_text property, based on the provided source language file (matches between string IDs)
        :param AndroidXmlFile source_xml_file: the xml file for the development language
        """
        pwt("UPDATING SOURCES FOR {}".format(self.original_file_path), color='y')

        # Add original text (source language) to translation units
        for t_unit in self.translation_units:
            t_unit_source_match = next((t for t in source_xml_file.translation_units if t.identifier == t_unit.identifier), None)
            if t_unit_source_match is None:
                pwt("{} - {} NOT FOUND IN SOURCE LANGUAGE FILE".format(t_unit.identifier, t_unit.target_text), color='r')
            else:
                t_unit.source_text = t_unit_source_match.source_text

        target_lang_ids = [t_unit.identifier for t_unit in self.translation_units]
        self.untranslated = deepcopy(
            [t for t in source_xml_file.translation_units if t.identifier not in target_lang_ids])

        for t_unit in self.untranslated:
            t_unit.target_text = ''
            t_unit.target_language = self.target_language_code
            t_unit.friendly_target_language = self.target_language
            pwt("MISSING {} TRANSLATION FOR: {} - {}".format(self.target_language, t_unit.identifier,
                                                             t_unit.source_text), color='r')

    def upload_to_google_sheets(self, gsheets_manager):
        # type: (GoogleSheetsManager) -> None

        pwt("SYNCING {} WITH GOOGLE SHEETS".format(self.original_file_path), color='y')
        lang_ws = gsheets_manager.get_worksheet(platform='android',
                                                language=self.target_language,
                                                header_values=self.header_values)

        ws_records = lang_ws.get_all_records(numericise_data=False, value_render=ValueRenderOption.FORMULA)
        ws_records_ids = [r[AndroidHeaderValues.STRING_ID] for r in ws_records]

        missing_records = [u.record_value for u in self.translation_units if u.identifier not in ws_records_ids]
        missing_untranslated_records = [u.record_value for u in self.untranslated if u.identifier not in ws_records_ids]
        missing_records += missing_untranslated_records

        if len(missing_records) > 0:
            lang_ws.insert_rows(row=lang_ws.rows - 1, number=len(missing_records), values=missing_records, inherit=True)

        lang_ws.sort_range((2, 1), (lang_ws.rows, lang_ws.cols))

        for r_to_add in missing_records:
            pwt("ADDED {} TO {} - {}".format(r_to_add, lang_ws.spreadsheet.title, lang_ws.title), color='y')

        pwt("ADDED {} RECORDS TO {} - {}".format(len(missing_records), lang_ws.spreadsheet.title, lang_ws.title), color='g')

        pass

    def update_from_google_sheets(self, gsheets_manager, dev_language_file):
        # type: (GoogleSheetsManager, AndroidXmlFile) -> None

        pwt("UPDATING {}".format(self.original_file_path), color='y')
        online_translation_units = self.__get_google_sheets_translation_units(gsheets_manager=gsheets_manager,
                                                                              dev_language_file=dev_language_file)

        mismatched_records = []
        for offline_t_unit in self.translation_units:
            online_t_unit = next((u for u in online_translation_units if u.identifier == offline_t_unit.identifier), None)

            if online_t_unit is None:
                mismatched_records.append(offline_t_unit)
            else:
                offline_target_text = offline_t_unit.target_text if offline_t_unit.target_text is not None else ''
                if online_t_unit.target_text != offline_target_text:
                    offline_t_unit.target_text = online_t_unit.target_text
                    mismatched_records.append(offline_t_unit)

        for untranslated_unit in self.untranslated:
            matched_unit = next((u for u in online_translation_units if u.identifier == untranslated_unit.identifier and
                             u.target_text is not None and u.target_text != ''), None)

            if matched_unit is not None:
                m_unit_target_text = matched_unit.target_text if matched_unit.target_text is not None else ''
                untranslated_unit.target_text = m_unit_target_text
                mismatched_records.append(untranslated_unit)

        for t_unit in mismatched_records:
            matched_unit = next((online_unit for online_unit in online_translation_units if
                                 online_unit.identifier == t_unit.identifier), None)
            if matched_unit is not None and matched_unit.is_translated():
                pwt(u"TRANSLATED: {}".format(matched_unit), color='g')
                t_unit.target_text = matched_unit.target_text

    def __get_google_sheets_translation_units(self, gsheets_manager, dev_language_file):
        # type: (GoogleSheetsManager, AndroidXmlFile) -> List[XliffTranslationUnit]
        lang_ws = gsheets_manager.get_worksheet(platform='android',
                                                language=self.target_language,
                                                header_values=self.header_values)
        ws_records = lang_ws.get_all_records(numericise_data=False, value_render=ValueRenderOption.FORMULA)
        xml_translation_units = []

        if len(ws_records) == 0:
            return xml_translation_units

        target_language_key = AndroidHeaderValues.TARGET_LANGUAGE.format(self.target_language)

        for record in ws_records:

            xml_translation_unit = AndroidXmlTranslationUnit(target_text=record[target_language_key],
                                                             identifier=record[AndroidHeaderValues.STRING_ID],
                                                             target_language=self.target_language_code,
                                                             friendly_target_language=self.target_language)

            dev_lang_unit = next((t for t in dev_language_file.translation_units if
                                            t.identifier == xml_translation_unit.identifier), None)

            if dev_lang_unit is not None:
                xml_translation_unit.source_text = dev_lang_unit.source_text
                xml_translation_unit.source_language = dev_language_file.source_language_code
                xml_translation_unit.friendly_source_language = dev_language_file.source_language
                xml_translation_units.append(xml_translation_unit)

        return xml_translation_units

    @staticmethod
    def unescape_xml_string_content(xml_content):
        """

        :param str xml_content:
        :return:
        :rtype: str
        """
        import re
        formatted_lines = []
        for xml_line in xml_content.splitlines():
            match = re.search(r'\s*?<string name=".*">(?P<tag_content>.*)</string>', xml_line)
            if not match:
                formatted_lines.append(xml_line)
            else:
                tag_content = match.group('tag_content')
                if string_has_placeholders(tag_content):
                    escaped_tag_content = escape_xml_characters(tag_content)
                    formatted_lines.append(xml_line.replace(tag_content, escaped_tag_content))
                else:
                    unescaped_tag_content = unescape_xml_characters(tag_content)
                    formatted_lines.append(xml_line.replace(tag_content, unescaped_tag_content))
            pass

        output_str = '\n'.join(formatted_lines)
        output_str = output_str.replace('&amp;lt;', '&lt;').replace('&amp;gt;', '&gt;').replace('&amp;amp;', '&amp;')
        # > is accepted in Android XML
        output_str = output_str.replace('&gt;', '>').replace('\?', '?')

        return output_str

    def update_source_xml(self):
        # type: () -> None

        f_stream = open(self.original_file_path, 'r', encoding='utf-8')
        str_content = f_stream.read()
        f_stream.close()

        normalized_xml = normalize_xml_file_content(str_content)

        xml_root = etree.fromstring(normalized_xml)

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
                string_node.tail = '\n\t'
                string_node.text = escape_xml_characters(t_unit.target_text)
                xml_root.append(string_node)
            elif xml_t_unit_node is not None:

                if string_has_placeholders(t_unit.target_text):
                    xml_t_unit_node.text = escape_xml_characters(t_unit.target_text)
                else:
                    xml_t_unit_node.text = unescape_xml_characters(t_unit.target_text)

        xml_string_content = etree.tostring(xml_root,
                                            pretty_print=True,
                                            encoding='utf-8',
                                            xml_declaration=True).decode('utf-8')

        # Indent the added comment (if any)
        if should_add_comment:
            xml_string_content = xml_string_content.replace('\n<!--', '\n\n\t<!--')

        # Unescape the strings that have no placeholders
        xml_string_content = AndroidXmlFile.unescape_xml_string_content(xml_string_content)

        # Overwrite the source file
        with open(self.original_file_path, 'w', encoding='utf-8') as out_file:
            out_file.write(xml_string_content)

        pass


def normalize_xml_file_content(file_content):
    """
    Use this method to escape HTML tags from the XML file (to be able to parse it properly using lxml)
    :param str file_content: The content of the XML file
    :return: The XML content with the inner HTML tags escaped (replaces "<"  with "&lt;")
    :rtype: str
    """

    import re
    html_tags_regex_pattern = r"<(?!string|\/string|\?|resources|\/resources|!)(\/?.*?)>"
    html_tags_replacement_pattern = r"&lt;\1>"

    filtered_content = re.sub(pattern=html_tags_regex_pattern,
                              repl=html_tags_replacement_pattern,
                              string=file_content,
                              flags=(re.VERBOSE | re.U))

    return filtered_content.encode('utf-8')


def import_from_res_folder(res_folder_path, development_language):
    # type: (str) -> List[AndroidXmlFile]

    pwt("LOADING XML FILES FROM {}".format(res_folder_path), color='y')

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

            xml_files.append(AndroidXmlFile(file_path=file_path, source_language=development_language))
            pwt("FOUND {}".format(file_path), color='y')

    if len(xml_files) == 0:
        pwt("COULD NOT FIND ANY XML FILES IN {}".format(res_folder_path), color='r')
        exit(1)

    source_language_file = [f for f in xml_files if f.source_language_code == f.target_language_code].pop()

    for xml_file in (f for f in xml_files if f.source_language_code != f.target_language_code):
        xml_file.update_source_language(source_xml_file=source_language_file)

    return xml_files
