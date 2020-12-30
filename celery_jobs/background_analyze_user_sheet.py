import datetime
from extensions import celery
import google_functions.google_slides
from flask import url_for, redirect, flash, Markup
from misc_utilities import generate_uuid
from views.reports_bp import (
    get_worksheet_from_url,
    get_writeable_worksheet,
    perform_automatic_analysis,
    replace_figures_with_urls,
    get_df_from_worksheet,
)


@celery.task
def background_analyze_user_sheet(url, sheet_name, email, unique_tag, report_result_id):
    """
    Background job uploads figures to Google cloud storage, then places them in 
    Gslides presentations. 
    """
    info = get_worksheet_from_url(
        url=url, sheet_name=sheet_name)
    if info['exit_code'] == 0:
        sheet = info['sheet']
        worksheet_to_read = info['worksheet']
    else:
        flash(Markup(info['error_message']))
        raise Exception(info['error_message'])

    # do the automatic analysis
    df = get_df_from_worksheet(worksheet_to_read, cleaning=True)

    analysis = perform_automatic_analysis(
        df, unique_tag=unique_tag, sheet_url=url, sheet_name=sheet_name)  # generate figures and labels

    basic_describe = analysis["basic_describe"]
    figures = analysis["figures"]
    # Produce Google slides version of the report.
    figures = replace_figures_with_urls(figures)
    doc_info = {'analysis_date': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'url': '#'.join(url.split('#')[0:-1]),
                'sheet_name': sheet_name,
                'raw_table': basic_describe,
                'figures': figures,
                'title': '',
                'email': email,
                'table': basic_describe.to_latex()}

    # Make the slides from the figures, use the automated transfer ownership
    slides_url = google_functions.google_slides.make_slideshow(
        doc_info)
    from database.schema import ReportResult
    from extensions import db
    r = ReportResult.query.get(report_result_id)
    r.slides_url = slides_url
    db.session.commit()
