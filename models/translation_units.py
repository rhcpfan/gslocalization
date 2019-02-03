#!/usr/bin/python
# -*- coding: utf-8 -*-

from typing import List


class XliffTranslationUnit(object):
    def __init__(self, source_text, target_text, example_text, notes, identifier,
                 file_path, source_language, target_language, friendly_source_language, friendly_target_language):
        # type: (str, str, str, str, str, str, str, str, str, str) -> XliffTranslationUnit

        self.identifier = identifier  # type: str
        self.source_language = source_language  # type: str
        self.target_language = target_language  # type: str
        self.source_text = source_text  # type: str
        self.target_text = target_text  # type: str
        self.notes = [note.strip() for note in notes.split('\n')]  # type: List[str]
        self.example_text = example_text
        self.file_path = file_path

        self.friendly_source_language = friendly_source_language
        self.friendly_target_language = friendly_target_language

    def __str__(self):
        notes_text = ', '.join(self.notes)
        if self.target_text is not None and self.target_text != '':
            return u'{} ==> {} ({})'.format(self.source_text, self.target_text, notes_text)
        else:
            return u'{} ==> NO_TRANSLATION ({})'.format(self.source_text, notes_text)

    @property
    def record_value(self):
        """
        :return: A list of the translation unit properties, in the same order as they should
        be placed in the corresponding worksheet.
        :rtype: List[str]
        """
        return [self.source_text, self.target_text, self.example_text, ', '.join(self.notes), self.identifier,
                self.file_path]

    def is_translated(self):
        """
        :return: True if the text_string is not None or empty, False otherwise
        :rtype: bool
        """
        return True if self.target_text.strip() is not '' else False


class AndroidXmlTranslationUnit(object):
    def __init__(self, target_text, identifier, target_language, friendly_target_language):

        self.identifier = identifier  # type: str

        self.target_language = target_language  # type: str
        self.friendly_target_language = friendly_target_language  # type: str
        self.target_text = target_text.replace('&lt;', '<').replace('&gt;', '>')  # type: str

        self.source_language = None  # type: str
        self.friendly_source_language = None  # type: str
        self.source_text = None  # type: str

    def __str__(self):
        return u"{} = {} ({})".format(self.identifier, self.target_text, self.friendly_target_language)

    @property
    def record_value(self):
        """
        :return: A list of the translation unit properties, in the same order as they should
        be placed in the corresponding worksheet.
        :rtype: List[str]
        """
        return [self.source_text, self.target_text, self.identifier]

    def is_translated(self):
        # type: () -> bool
        return True if self.target_text.strip() is not '' else False


class DotNetResxTranslationUnit(object):
    def __init__(self, target_text, identifier, target_language, friendly_target_language):

        self.identifier = identifier  # type: str

        self.target_language = target_language  # type: str
        self.friendly_target_language = friendly_target_language  # type: str
        self.target_text = target_text.replace('&lt;', '<').replace('&gt;', '>')  # type: str

        self.source_language_code = None  # type: str
        self.source_language = None  # type: str
        self.source_text = None  # type: str

    def __str__(self):
        return "{} = {} ({})".format(self.identifier, self.target_text, self.friendly_target_language)

    @property
    def record_value(self):
        return [self.source_text, self.target_text, self.identifier]

    def is_translated(self):
        # type: () -> bool
        return True if self.target_text.strip() is not '' else False