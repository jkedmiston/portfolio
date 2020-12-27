import math
import numpy as np
from misc_utilities import generate_uuid


class SlideFigureArray:
    def __init__(self, configuration="up_to_two_columns"):
        self.configuration = configuration
        self.figures = []

    def add_figure(self, fig):
        self.figures.append({'figure': fig})

    def number_of_figures(self):
        return len(self.figures)

    def create_ylabel(self, slide_id, ytext):
        left_id = generate_uuid()
        left_side_label_requests = [{'createShape': {"objectId": left_id,
                                                     "shapeType": "TEXT_BOX",
                                                     "elementProperties": {"pageObjectId": slide_id,
                                                                           "size": {"width": {"magnitude": 150,
                                                                                              "unit": "PT"},
                                                                                    "height": {"magnitude": 50,
                                                                                               "unit": "PT"},
                                                                                    },
                                                                           "transform": {"scaleX": 1,
                                                                                         "scaleY": 1,
                                                                                         "translateX": 200,
                                                                                         "translateY": 100,
                                                                                         "unit": "PT"},
                                                                           },
                                                     },
                                     },

                                    {
            "insertText": {"objectId": left_id,
                           "text": ytext,
                           "insertionIndex": 0}},

        ]
        left_side_rotation_requests = [{"updatePageElementTransform": {"objectId": left_id,
                                                                       "applyMode": "RELATIVE",
                                                                       "transform": {"scaleX": np.cos(90 * math.pi/180),
                                                                                     "scaleY": np.cos(90 * math.pi/180),
                                                                                     "shearX": np.sin(90 * math.pi/180),
                                                                                     "shearY": np.sin(90 * math.pi/180),
                                                                                     "unit": "PT"}
                                                                       }},
                                       {"updatePageElementTransform": {"objectId": left_id,
                                                                       "applyMode": "RELATIVE",
                                                                       "transform": {"scaleX": 1,
                                                                                     "scaleY": 1,
                                                                                     "translateX": (3.05-1.3)*72,
                                                                                     "translateY": -130+(.07*72),
                                                                                     "unit": "PT"}
                                                                       }}
                                       ]
        font_style_requests = [{"updateTextStyle": {"objectId": left_id,
                                                    "fields": 'fontSize,fontFamily',
                                                    "style": {"fontFamily": 'Open Sans',
                                                              "fontSize": {"magnitude": 16, "unit": "PT"}}}}]

        return left_side_label_requests + left_side_rotation_requests + font_style_requests

    def create_xlabel(self, slide_id, xtext):
        bottom_id = generate_uuid()
        bottom_label_requests = [{'createShape': {"objectId": bottom_id,
                                                  "shapeType": "TEXT_BOX",
                                                  "elementProperties": {"pageObjectId": slide_id,
                                                                        "size": {"width": {"magnitude": 150,
                                                                                           "unit": "PT"},
                                                                                 "height": {"magnitude": 50,
                                                                                            "unit": "PT"},
                                                                                 },
                                                                        "transform": {"scaleX": 1,
                                                                                      "scaleY": 1,
                                                                                      "translateX": 300 + (3.05-1.03)*72,
                                                                                      "translateY": 4.9*72+.07*72,
                                                                                      "unit": "PT"},
                                                                        },
                                                  }},
                                 {
                                     "insertText": {"objectId": bottom_id,
                                                    "text": xtext,
                                                    "insertionIndex": 0}}
                                 ]
        font_style_requests = [{"updateTextStyle": {"objectId": bottom_id,
                                                    "fields": 'fontSize,fontFamily',
                                                    "style": {"fontFamily": 'Open Sans',
                                                              "fontSize": {"magnitude": 16, "unit": "PT"}}}}]
        return bottom_label_requests + font_style_requests

    def create_title(self, slide_id, text):
        title_id = generate_uuid()
        bottom_label_requests = [{'createShape': {"objectId": title_id,
                                                  "shapeType": "TEXT_BOX",
                                                  "elementProperties": {"pageObjectId": slide_id,
                                                                        "size": {"width": {"magnitude": 8*72,
                                                                                           "unit": "PT"},
                                                                                 "height": {"magnitude": 0.6*72,
                                                                                            "unit": "PT"},
                                                                                 },
                                                                        "transform": {"scaleX": 1,
                                                                                      "scaleY": 1,
                                                                                      "translateX": 30,
                                                                                      "translateY": 10,
                                                                                      "unit": "PT"},
                                                                        },
                                                  }},
                                 {
                                     "insertText": {"objectId": title_id,
                                                    "text": text,
                                                    "insertionIndex": 0}}
                                 ]
        font_style_requests = [{"updateTextStyle": {"objectId": title_id,
                                                    "fields": 'fontSize,fontFamily',
                                                    "style": {"fontFamily": 'Arial',
                                                              "fontSize": {"magnitude": 24, "unit": "PT"}}}}]
        return bottom_label_requests + font_style_requests

    def insert_url_into_request(self, request, url):
        request["createImage"]["url"] = url

    def create_image(self, slide_id, scale=1, translate=[100, 0], url=None):
        """creates requests to put in an image. The url for the image can come now or later
        """
        # 72 pt/in, Google slides usually does position in inches
        photo_requests = [{'createImage': {'elementProperties': {'pageObjectId': slide_id,
                                                                 'transform': {
                                                                     'scaleX': scale,
                                                                     'scaleY': scale,
                                                                     'shearX': 0,
                                                                     'shearY': 0,
                                                                     'translateX': translate[0],
                                                                     'translateY': translate[1],
                                                                     'unit': 'PT'},
                                                                 },
                                           }}]
        if url:
            self.insert_url_into_request(photo_requests[0], url=url)

        return photo_requests

    def generate_slide_creation_requests(self, slide_id):
        n_figures = self.number_of_figures()
        upper_left_corner = np.array([1.3 + (3.05-1.3), +.07]) * 72.0

        if n_figures < 2:
            # basic
            img_requests = [*self.create_image(
                scale=1, translate=upper_left_corner, slide_id=slide_id)]
            pass
        elif n_figures == 2:
            # scaleX goes to 0.5
            img_requests = [*self.create_image(scale=.5, translate=upper_left_corner, slide_id=slide_id),
                            *self.create_image(scale=.5, translate=upper_left_corner + [0, 2.5 * 72], slide_id=slide_id)]

        else:
            raise
        for k, info in enumerate(self.figures):
            # createImage with url=f
            self.insert_url_into_request(
                img_requests[k], info["figure"]["url"])
            # img_requests[k]["createImage"]["url"] = info["figure"]["url"]
            xlabel = info["figure"]["xlabel"]
            ylabel = info["figure"]["ylabel"]
            slide_title = info["figure"].get("slide_title", "")
            # add xlabel ylabels and title
            # by ordering these after the figure, the z-stacking turns out as desired
            img_requests.extend(self.create_xlabel(
                slide_id=slide_id, xtext=xlabel))
            img_requests.extend(self.create_ylabel(
                slide_id=slide_id, ytext=ylabel))
            img_requests.extend(self.create_title(
                slide_id=slide_id, text=slide_title))
        return img_requests
