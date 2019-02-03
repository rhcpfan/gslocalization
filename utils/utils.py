import sys
from colorama import init, Fore
from datetime import datetime

# Init colorama
init()


def is_python_2():
    # type: () -> bool
    python_ver = sys.version_info
    return python_ver < (3, 0)


def print_with_timestamp(string_to_print, color):
    # type: (str, str) -> None
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


