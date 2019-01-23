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

        if isinstance(target_text, basestring):
            target_text_str = target_text
        else:
            target_text_str = str(target_text)

        self.target_text = target_text_str  # type: str

        if isinstance(notes, basestring):
            notes_str = notes
        else:
            notes_str = str(notes)

        self.notes = [note.strip() for note in notes_str.split('\n')]  # type: List[str]
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
        return [self.source_text, self.target_text, self.example_text, ', '.join(self.notes), self.identifier,
                self.file_path]

    def is_translated(self):
        # type: () -> bool
        return True if self.target_text.strip() is not '' else False

    def dictionary_representation(self):
        # type: () -> dict

        source_text = self.source_text if self.source_text is not None else ''
        target_text = self.target_text if self.target_text is not None else ''

        return {
            self.friendly_source_language: source_text,
            self.friendly_target_language: target_text,
            'Example': self.example_text,
            'Notes': ', '.join(self.notes),
            'Element ID': self.identifier,
            'Path': self.file_path
        }


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
        return [self.source_text, self.target_text, self.identifier]

    def is_translated(self):
        # type: () -> bool
        return True if self.target_text.strip() is not '' else False

    def dictionary_representation(self):
        # type: () -> dict

        source_text = self.source_text if self.source_text is not None else ''
        target_text = self.target_text if self.target_text is not None else ''

        return {
            self.friendly_source_language: source_text,
            self.friendly_target_language: target_text,
            'Element ID': self.identifier
        }


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

    def dictionary_representation(self):
        # type: () -> dict

        source_text = self.source_text if self.source_text is not None else ''
        target_text = self.target_text if self.target_text is not None else ''

        return {
            self.source_language: source_text,
            self.friendly_target_language: target_text,
            'Element ID': self.identifier
        }
