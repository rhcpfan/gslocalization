import sys
from colorama import init, Fore
from datetime import datetime

# Init colorama
init()


def is_python_2():
    # type: () -> bool
    python_ver = sys.version_info
    return python_ver < (3, 0)


def pwt(string_to_print, color):
    """
    Prints a colored output with a timestamp
    :param str string_to_print: the string to pring
    :param str color: color of the output (currently supports red, green and yellow ['r', 'g', 'y'])
    """
    current_timestamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S.%f')[:-3]

    print_color = Fore.WHITE
    color = color.lower()
    if color == 'red' or color == 'r':
        print_color = Fore.RED
    elif color == 'green' or color == 'g':
        print_color = Fore.GREEN
    elif color == 'yellow' or color == 'y':
        print_color = Fore.YELLOW

    print(u'{}[{}] {}'.format(print_color, current_timestamp, string_to_print))


def get_input(prompt):
    try:
        input_ = raw_input
    except NameError:
        input_ = input

    return input_(u'{}{}'.format(Fore.GREEN, prompt))


def get_language_name(language_code):
    # type: (str) -> str
    if is_python_2():
        import langcodes
        return langcodes.LanguageData().get(language_code).describe()['language']
    else:
        from langcodes import Language
        return Language(language=language_code).language_name()


def get_language_code(language_name):
    # type: (str) -> str
    if is_python_2():
        import langcodes
        return langcodes.LanguageData.find_name('language', language_name, 'en').language
    else:
        from langcodes import Language
        return Language(language_name).language


def xcode_supports_dev_language_operations():
    import subprocess
    from distutils.version import StrictVersion
    xcb_params = ['-version']
    xcb = subprocess.Popen(['xcodebuild'] + xcb_params, stdout=subprocess.PIPE)
    out, err = xcb.communicate()

    xcode_version_str = out.split('\n')[0].split(' ')[1]
    current_version = StrictVersion(xcode_version_str)
    ref_version = StrictVersion('10.2')

    return current_version >= ref_version


def string_has_placeholders(string):
    import re
    placeholders = re.findall(r'%[\d<]*\$*[bBhHsScCdoxXeEfgGaAtT]', string)
    return len(placeholders) > 0


def escape_xml_characters(xml_content):
    """
    Replaces invalid XML characters with their escaped version (@, ?, <, &, ', ") -> (\@, \?, &lt;, \', \")
    :param str xml_content: the string to escape
    :return: the content of the input, with the invalid characters escaped
    :rtype: str
    """
    import re

    # replace @ with \@
    output_string = re.sub(r'([^\\])@', r'\1\\@', xml_content)
    # replace ? with \?
    output_string = re.sub(r'([^\\])\?', r'\1\\?', output_string)
    # replace < with &lt;
    output_string = re.sub(r'<(?!string|\/string|\?|resources|\/resources|!)', r'&lt;', output_string)
    # replace & with &amp;
    output_string = re.sub(r'&(?!lt;|gt;|amp;|apos;|quot;)', r'&amp;', output_string)
    # replace ' with \'
    output_string = re.sub(r'([^\\])\'', r'\1\'', output_string)
    # replace " with \"
    output_string = re.sub(r'([^\\])\"', r'\1\"', output_string)
    # replace &gt; with > (this one is not invalid)
    output_string = re.sub(r'&gt;', r'>', output_string)

    output_string = output_string.replace('&amp;lt;', '&lt;').replace('&amp;gt;', '&gt;')

    return output_string


def unescape_xml_characters(xml_content):
    """
    Replaces the escaped version of XML characters (\@, \?, &lt;, \', \")
    with their plain text correspondent (@, ?, <, &, ', ")
    :param str xml_content: the string to escape
    :return: the content of the input, with the escaped characters converted back to plain text
    :rtype: str
    """
    import re

    output_string = re.sub(r'\\@', r'@', xml_content)
    output_string = re.sub(r'\\\?', r'?', output_string)
    output_string = re.sub(r'&lt;', r'<', output_string)
    output_string = re.sub(r'&amp;lt;', r'<', output_string)
    output_string = re.sub(r'&gt;', r'>', output_string)
    output_string = re.sub(r'&amp;gt;', r'>', output_string)

    return output_string
