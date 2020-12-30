import os
import pygsheets
from googleapiclient.errors import HttpError
from google_functions import get_service_account_email


def upload_df_to_google_sheets(df, url, sheet_name):
    gsheets = pygsheets.authorize(
        service_account_env_var="GOOGLE_APPLICATION_CREDENTIALS")
    slug = os.path.basename(os.path.split(url)[0])
    try:
        sheet = gsheets.open_by_key(slug)
        wks = sheet.worksheet_by_title(title=sheet_name)
    except pygsheets.exceptions.WorksheetNotFound:
        sheet = gsheets.open_by_key(slug)
        wks = sheet.add_worksheet(title=sheet_name)
    except HttpError as err:
        email = get_service_account_email()
        error_message = "Permission is needed to modify the sheet. Give this email: %s permission to edit the sheet." % email
        return {'exit_code': -1, 'error_message': error_message}

    wks.set_dataframe(df, (1, 1), fit=True, nan='')
    return {'exit_code': 0}
