import os
import datetime
import json
import traceback
from google.oauth2 import service_account
from googleapiclient.discovery import build
from google_functions.slide_figure_array import SlideFigureArray
from misc_utilities import generate_uuid


def create_general_slide_template(slide_id, title_id, subtitle_id, body_id):
    layout_type = 'SECTION_TITLE_AND_DESCRIPTION'
    data_requests = [
        {
            'createSlide': {
                'objectId': slide_id,
                'slideLayoutReference': {'predefinedLayout': layout_type},
                'placeholderIdMappings': [
                    {'layoutPlaceholder': {'type': 'TITLE', 'index': 0},
                     'objectId': title_id},
                    {'layoutPlaceholder': {'type': 'SUBTITLE', 'index': 0},
                        'objectId': subtitle_id},
                    {'layoutPlaceholder': {'type': 'BODY', 'index': 0},
                        'objectId': body_id},
                ]
            }
        },
        {'insertText': {'objectId': title_id,
                        'text': 'p'}},
        {'insertText': {'objectId': body_id,
                        'text': 'All text '}},
        {'insertText': {'objectId': subtitle_id,
                        'text': 'sub-placeholder'}}
    ]
    return data_requests


def create_blank_slide_template(slideId, title_id, body_id, text="", text_url=""):
    """
    This template is of the form: 
    __________________________
    |_text_______________|    |
    |       |                 |
    |  text |                 |
    |       |                 |
    |_______|                 |
    |                         |
    |_________________________|    
    """
    layout_type = 'BLANK'
    data_requests = [
        {
            'createSlide': {
                'objectId': slideId,
                'slideLayoutReference': {'predefinedLayout': layout_type},
            }
        },
    ]
    pt350w = {'magnitude': 2.89*72,
              'unit': 'PT'}
    pt350h = {'magnitude': 3.82*72,
              'unit': 'PT'}
    linkstart = text.index('<')
    linkend = text.index('>')
    # parse out the replacement value from <link>
    split = text[linkstart+1:linkend]
    edited_text = text[:linkstart] + split + text[linkend+1:]

    data_requests += [{'createShape': {
        'objectId': body_id,
        'shapeType': 'TEXT_BOX',
        'elementProperties': {
            'pageObjectId': slideId,
            'size': {'height': pt350h,
                     'width': pt350w},
            'transform': {'scaleX': 1,
                          'scaleY': 1,
                          'translateX': .16 * 72,
                          'translateY': 1.39*72,
                          'unit': 'PT'}
        }
    }
    },
        {'insertText': {'objectId': body_id,
                        'insertionIndex': 0,
                        'text': edited_text}}
    ]

    data_requests += [{"updateTextStyle": {"objectId": body_id,
                                           "textRange": {"startIndex": linkstart,
                                                         "endIndex": linkstart + len(split),
                                                         "type": "FIXED_RANGE"},
                                           "fields": "link",
                                           "style": {"link": {"url": text_url}}}}]
    if layout_type != "BLANK":
        data_requests += [{'updatePageElementTransform': {"objectId": title_id,
                                                          "applyMode": "RELATIVE",
                                                          "transform": {"scaleX": 1,
                                                                        "scaleY": 1,
                                                                        "shearX": 0,
                                                                        "shearY": 0,
                                                                        "unit": "PT",
                                                                        "translateX": 0,
                                                                        "translateY": -30}}}]
        data_requests += [{"updateTextStyle": {"objectId": title_id,
                                               "fields": 'fontSize',
                                               "style": {"fontFamily": 'Arial',
                                                         "fontSize": {"magnitude": 24, "unit": "PT"}}}}]

    return data_requests


def make_slideshow(form_info):
    """
    Assemble figures and tables into a google slideshow
    @form_info['figures']: list of [{'figure': 'url or path',
    'xlabel': 'Xlabel',
    'ylabel': 'Ylabel}, ...]

    """
    service_account_info = json.loads(
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"])
    credentials = service_account.Credentials.from_service_account_info(
        service_account_info)
    drive_service = build(
        'drive', 'v3', credentials=credentials, cache_discovery=False)
    slides_service = build(
        'slides', 'v1', credentials=credentials, cache_discovery=False)
    # https://developers.google.com/slides/?hl=en_US
    utcnow = datetime.datetime.utcnow().strftime(
        "%Y-%m-%d %H:%M:%S [UTC]")
    body = {'title': 'Autogen-%s' % utcnow}
    response = slides_service.presentations().create(body=body).execute()
    slide_deck_id = response.get('presentationId')
    title_slide = response['slides'][0]
    title_id = title_slide['pageElements'][0]['objectId']
    subtitle_id = title_slide['pageElements'][1]['objectId']
    current_timestamp = '''Created at: %s\nSource data linked here, tab %s''' % (
        utcnow, form_info["sheet_name"])
    linkstart = current_timestamp.index('linked here')
    linkend = linkstart + len('linked here') + 1
    # link the data source url to the Slides title slide.
    requests = [
        {
            'insertText': {
                'objectId': title_id,
                'text': form_info.get('title', '')}
        },
        {
            'insertText': {
                'objectId': subtitle_id,
                'text': current_timestamp,
            }
        },
        {
            'updateTextStyle': {
                'objectId': subtitle_id,
                'textRange': {'startIndex': linkstart,
                              'endIndex': linkend,
                              'type': 'FIXED_RANGE'},
                'fields': 'link',
                'style': {'link':
                          {
                              'url': form_info['url'],
                          }
                          }
            }
        },
    ]
    # To add slides:
    # https://developers.google.com/apps-script/reference/slides/predefined-layout#BLANK
    # refs: - https://developers.google.com/apps-script/advanced/slides
    #       - https://developers.google.com/slides/how-tos/create-slide
    #       - https://developers.google.com/slides/samples/slides#create_a_new_slide_and_modify_placeholders
    # Tables:
    #       - https://developers.google.com/slides/samples/tables

    # generate a slide for each figure
    slide_info = [{} for _ in form_info["figures"]]
    for kk, fig_info in enumerate(form_info["figures"]):
        slideId = generate_uuid()
        title_id = generate_uuid()
        subtitle_id = generate_uuid()
        body_id = generate_uuid()
        slide_info[kk]["slideId"] = slideId
        slide_info[kk]["title_id"] = title_id
        slide_info[kk]["subtitle_id"] = subtitle_id
        slide_info[kk]["body_id"] = body_id
        slide_info[kk]["request"] = create_blank_slide_template(
            slideId=slideId,
            title_id=title_id,
            body_id=body_id,
            text=fig_info.get(
                "description", "Data source: <link>, sheet: %s" % form_info["sheet_name"]),
            text_url=form_info["url"])
        sfarray = SlideFigureArray()
        sfarray.add_figure(fig_info)
        # sfarray.add_figure(info["photo_url"])
        # create_image(slide_id=slideId, scale=1, translate
        slide_creation_requests = sfarray.generate_slide_creation_requests(
            slide_id=slideId)
        slide_info[kk]["request"].extend(slide_creation_requests)

    for request_info in slide_info:
        requests.extend(request_info["request"])

    create_slides_requests_body = {
        'requests': requests
    }

    try:
        response = slides_service.presentations().batchUpdate(
            presentationId=slide_deck_id, body=create_slides_requests_body).execute()
    except:
        t = traceback.format_exc()
        print(t)
        return

    # Now, change permissions on the produced deck to the target owner.
    # See pygsheets in pygsheets/drive.py for these options.
    # PERMISSION_ROLES = ['organizer', 'owner', 'writer', 'commenter', 'reader']
    # PERMISSION_TYPES = ['user', 'group', 'domain', 'anyone']
    # https://developers.google.com/drive/api/v3/reference/permissions/create
    body = {"kind": "drive#permission",
            "type": "user",
            "role": "owner",
            "emailAddress": form_info["email"]}  # TODO, change to transfer ownership, see pygsheets/drive.py
    request = drive_service.permissions().create(
        fileId=slide_deck_id, body=body, transferOwnership='true', sendNotificationEmail='true', emailMessage="Transferred by Autogen")
    permission_move_result = request.execute()

    # delete access to the service account
    permission_id = permission_move_result["id"]
    output = drive_service.permissions().list(fileId=slide_deck_id).execute()
    for permission_info in output["permissions"]:
        if permission_info["id"] == permission_id:
            continue
        else:
            drive_service.permissions().delete(fileId=slide_deck_id,
                                               permissionId=permission_info["id"]).execute()

    return "https://docs.google.com/presentation/d/%s/edit" % slide_deck_id
