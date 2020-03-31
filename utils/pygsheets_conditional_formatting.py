import pygsheets
from pygsheets.client import Client
from pygsheets.worksheet import Worksheet


def add_conditional_formatting_rule(sheets_client, worksheet, start, end, condition_type, formula, color):
    """
    Changes the cell's background color to `color` if the required conditions are met.
    See https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets/other#ConditionType
    for more condition types.
    Args:
        sheets_client: The Google Sheets client.
        worksheet: The Worksheet to apply changes to.
        start: The start range (tuple of int).
        end: The end range (tuple of int).
        condition_type: The type of formula.
        formula: The formula value.
        color: The background color to apply on cells meeting the criteria.
    """
    # type: (Client, Worksheet, tuple, tuple, str, str, tuple) -> None

    add_formatting_rule_request = {
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [
                    {
                        "sheetId": worksheet.id,
                        "startColumnIndex": start[0],
                        "startRowIndex": start[1],
                        "endColumnIndex": end[0],
                        "endRowIndex": end[1]
                    }
                ],
                "booleanRule": {
                    "condition": {
                        "type": condition_type
                    },
                    "format": {
                        "backgroundColor": {
                            "red": color[0],
                            "green": color[1],
                            "blue": color[2],
                            "alpha": 1
                        }
                    }
                }
            },
            "index": 0
        }
    }

    if condition_type not in ['BLANK']:
        add_formatting_rule_request['addConditionalFormatRule']['rule']['booleanRule']['condition']['values'] = {'userEnteredValue': formula}
        pass

    sheets_api_wrapper = sheets_client.sheet
    sheets_api_wrapper.batch_update(spreadsheet_id=worksheet.spreadsheet.id, requests=add_formatting_rule_request)
