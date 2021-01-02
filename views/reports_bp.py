"""
Functions for producing reports, generally taking in a Google sheet URL and returning
analyzed results in PDF or Google slides forms.
"""
import os
import sys
import copy
import numpy as np
import datetime
import collections
import flask
from misc_utilities import generate_uuid

from flask import request, flash, Markup
from flask import Blueprint, render_template
from flask_wtf import FlaskForm
from flask import (url_for, redirect, send_from_directory)
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from googleapiclient.errors import HttpError
import pandas as pd
import pygsheets
import google_functions.google_slides
import latex_reports.latex_doc
from latex_reports.latex_utilities import make_latex_safe
from flask import current_app
from google_functions import get_service_account_email

reports_bp = Blueprint(
    'reports_bp',
    __name__,
    template_folder='templates',
    static_folder='static'
)
# fontsize here found by trial and error with Gslides format and how large
# the matplotlib figures were.
MATPLOTLIB_FONTSIZE_FOR_GSLIDES = 16


def get_column_info(df):
    categorical_columns = []
    numerical_columns = []
    for i, colname in enumerate(df.columns):
        if not np.issubdtype(df[colname].dtype, np.number):
            categorical_columns.append(colname)
        else:
            numerical_columns.append(colname)

    return {'categorical_columns': categorical_columns,
            'numerical_columns': numerical_columns}


def basic_grouping_plots(df, unique_tag, sheet_url, sheet_name):
    """group by categories, then run the histograms on the grouping
    """

    column_info = get_column_info(df)
    categorical_columns = column_info["categorical_columns"]

    all_figures = collections.defaultdict(list)
    for cat in categorical_columns:
        grps = df.groupby(cat)

        counts = df[cat].value_counts().reset_index()
        counts = counts.sort_values(by=[cat, 'index'], ascending=False)
        for g in counts["index"]:
            dg = grps.get_group(g)
            if g == "" or g == np.nan:
                g_label = "Null-or-empty"
            else:
                g_label = g.replace(' ', '_')

            output = basic_histograms(dg,
                                      unique_tag=unique_tag,
                                      sheet_url=sheet_url,
                                      sheet_name=sheet_name,
                                      subtag=cat,
                                      grouping_label="%s = %s" % (
                                          cat, g_label),
                                      slide_title="Exploratory plots - histograms, on subgroup (%s = %s)" % (cat, g_label))
            all_figures["figures"].extend(output["figures"])

    return all_figures


def basic_bar_plots_for_categorical_features(df, unique_tag, sheet_url, sheet_name):
    """
    For categorical features only, do horizontal bar chart of counts
    """
    import seaborn as sns
    import matplotlib.pyplot as plt

    def xstrip(x):
        try:
            if x.strip() == "":
                return True
        except:
            current_app.logger.warning("data type %s is not a str" % x)
        return False

    sns.set_style('ticks')  # darkgrid, whitegrid, dark, white, ticks}

    plt.rcParams.update({'font.size': MATPLOTLIB_FONTSIZE_FOR_GSLIDES})
    fignames = []
    for i, colname in enumerate(df.columns):
        if np.issubdtype(df[colname].dtype, np.number) == False:
            # do categorical analysis, basic counts
            # make bar plot of counts
            nrows = len(df)
            empty = df.loc[df[colname].notnull(), colname].apply(
                xstrip).sum()
            count_invalid_data = df[colname].isnull().sum() + empty
            count_valid_data = len(df) - count_invalid_data
            fig, ax = plt.subplots(1, 1, figsize=(
                6.67, 5))  # fontFamily is serif
            counts = df[colname].value_counts().reset_index()
            counts = counts.sort_values(by=[colname, 'index'], ascending=True)
            counts.loc[counts["index"].isin(
                ["", np.nan]), "index"] = "<Null or empty>"
            ax.barh(counts["index"], counts[colname])
            ax.set_ylabel("  ")
            ax.set_title(" ")
            fig.tight_layout()
            left = fig.subplotpars.left
            fig.subplots_adjust(left=left + left * 0.15)
            fig.subplots_adjust(top=fig.subplotpars.top*0.95)
            figname = "tmp/basic_bar_plot_%s_%d.png" % (unique_tag, i)
            # currently, using scripts in the test folder to adjust
            # plotting positions, etc.
            if hasattr(sys, '_called_from_test'):
                fig.show()
                import pdb
                pdb.set_trace()

            fig.savefig(figname)
            plt.close(fig)

            if os.path.isfile(figname):
                description = f'Basic counts of {colname}, from the data source <linked here>\nTab: {sheet_name}\n\nNumber of rows: {nrows}\nNon-null data counts: {count_valid_data}\nNull or empty data counts: {count_invalid_data}\n'

                fignames.append({'figure': figname,
                                 'description': description,
                                 'xlabel': 'Counts',
                                 'caption': make_latex_safe(description).replace('<linked here>', r'\href{%(url)s}{\underline{linked here}}' % dict(url=sheet_url)).replace('\n', r'\\'),
                                 'ylabel': 'Category',
                                 "slide_title": "Exploratory plots - categories"})
    return {'figures': fignames}


def basic_histograms(df, unique_tag, sheet_url, sheet_name, all_figures=None, mode=None, subtag="", grouping_label=None, slide_title="Exploratory plots - histograms"):
    """
    For numerical data, product histograms of non-null results.
    """
    import seaborn as sns
    import matplotlib.pyplot as plt

    # from pandas.api.types import is_numeric_dtype
    sns.set_style('ticks')  # darkgrid, whitegrid, dark, white, ticks}
    # found by trial and error with Gslides
    plt.rcParams.update({'font.size': MATPLOTLIB_FONTSIZE_FOR_GSLIDES})
    basic_describe = df.describe(include='all')
    fignames = []

    for i, colname in enumerate(df.columns):
        if colname not in basic_describe.columns:
            continue
        if not np.issubdtype(df[colname].dtype, np.number):
            # do categorical
            current_app.logger.info(
                "categorical feature detected on column %s" % colname)
            continue
        else:
            # numeric analysis
            valid_data = df[df[colname].notnull()][colname]
            count_invalid_data = df[colname].isnull().sum()  # TODO, add to tabular output # noqa
            count_valid_data = len(valid_data)  # TODO, add to tabular output # noqa
            mean = np.mean(valid_data)
            median = np.median(valid_data)
            stdev = np.std(valid_data)

            # make a single basic histogram of this variable
            if grouping_label is None:
                figname = "tmp/basic_histograms_%s%s_%d.png" % (
                    subtag, unique_tag, i)
            else:
                figname = "tmp/basic_histograms_%s%s%s_%d.png" % (
                    subtag, grouping_label.replace(' ', '').replace('=', '').replace('.', ''), unique_tag, i)

            try:
                # TODO: add test for categorical / string features
                fig, ax = plt.subplots(1, 1, figsize=(
                    6.67, 5))  # fontFamily is serif
                ax.hist(valid_data.values)
                # keep the plots bare bones, so that labels are added
                # at Google slides layer
                # basically just change the size of fonts
                ax.set_title(" ")
                ax.set_ylabel(" ")
                fig.tight_layout()
                left = fig.subplotpars.left
                fig.subplots_adjust(left=left + left * 0.1)
                fig.subplots_adjust(top=fig.subplotpars.top*0.95)
                # fig.tight_layout()
                if hasattr(sys, '_called_from_test'):
                    fig.show()
                    import pdb
                    pdb.set_trace()

                fig.savefig(figname)
                plt.close(fig)
            except:
                # Log error TODO
                current_app.logger.warning(
                    "Error occured on column %s" % colname)
                pass

            if os.path.isfile(figname):
                if grouping_label is not None:
                    hist_description = "%s, subgroup(%s)" % (
                        colname, grouping_label)
                else:
                    hist_description = colname

                description = f'Basic histogram of {hist_description}, from the data source <linked here>\nTab: {sheet_name}\n\nValid data counts: {count_valid_data}\nInvalid data counts: {count_invalid_data}\nMean: {mean:.2f}\nMedian: {median:.2f}\nStd. dev: {stdev:.2f}\n'

                fignames.append({'figure': figname,
                                 'description': description,
                                 'caption': make_latex_safe(description).replace('<linked here>', r'\href{%(url)s}{\underline{linked here}}' % dict(url=sheet_url)).replace('\n', r'\\'),
                                 'xlabel': colname,
                                 'ylabel': 'Counts',
                                 "slide_title": slide_title})

    return {'basic_describe': basic_describe,
            'figures': fignames}


def perform_automatic_analysis(df, unique_tag, sheet_url, sheet_name):
    """
    From the dataframe, produce plots and summary stats, and present
    findings as a list of dictionary with {'basic_describe': summary_df,
                                           'figures': [{'figure': pathname,
                                                        'description': text on figure,
                                                        'xlabel', 'ylabel', 'slide_title'}, ...]
    """
    info = basic_histograms(df, unique_tag, sheet_url, sheet_name)
    category_info = basic_bar_plots_for_categorical_features(
        df,  unique_tag, sheet_url, sheet_name)
    grouping_info = basic_grouping_plots(df, unique_tag, sheet_url, sheet_name)
    final = info.copy()
    final["figures"].extend(category_info["figures"])
    final["figures"].extend(grouping_info["figures"])

    return final


def get_gsheets_slug_from_url(url):
    """
    Get the gsheets key , e.g.
    turns https://docs.google.com/spreadsheets/d/1u9**abcdefg**61mqkg/edit#gid=0 # noqa
    into 1u9**abcdefg**61mqkg
    """
    return os.path.basename(os.path.split(url)[0])


def clean_df(df):
    """
    Don't return a bunch of blank columns
    """

    col1 = df.columns[0]
    tmp = df[df[col1] != ""].copy()
    cols, = np.where(df.columns != '')
    tmp = tmp.iloc[:, cols].copy()
    return tmp


def get_df_from_worksheet(wks, cleaning):
    """
    Returns pandas dataframe from a pygsheets worksheet
    """
    try:
        df = wks.get_as_df()
    except AssertionError:
        df = wks.get_as_df(has_header=False)

    if cleaning:
        df = clean_df(df)
    return df


def get_writeable_worksheet(sheet, sheet_name):
    """
    returns pygsheets object for a given google sheet. If an error occurs, the type of error is returned so that it can be displayed on a web page
    """
    try:
        wks_in = sheet.worksheet_by_title(title=sheet_name)
        return {'sheet': wks_in, 'exit_code': 0}
    except pygsheets.exceptions.WorksheetNotFound:
        wks_in = sheet.add_worksheet(title=sheet_name)
        return {'sheet': wks_in, 'exit_code': 0}
    except HttpError as err:
        return {'exit_code': -1, 'error_message': 'Permission needed'}
    return {'exit_code': -1, 'error_message': 'Unknown'}


def get_worksheet_from_url(url, sheet_name):
    gsheets = pygsheets.authorize(
        service_account_env_var="GOOGLE_APPLICATION_CREDENTIALS")
    slug = get_gsheets_slug_from_url(url)
    try:
        sheet = gsheets.open_by_key(slug)
        worksheet_to_read = sheet.worksheet_by_title(title=sheet_name)
        return {'sheet': sheet,
                'worksheet': worksheet_to_read,
                'exit_code': 0}
    except pygsheets.exceptions.WorksheetNotFound:
        error_message = "Sheet %s not found, check URL and sheet name" % sheet_name
        return {'exit_code': -1,
                'error_message': error_message,
                'redirect': url_for('reports_bp.analyze_user_sheet')
                }
    except HttpError as err:
        email = get_service_account_email()
        error_message = "Permission is needed to modify the sheet. Give this email: %s permission to edit the sheet. " % email
        return {'exit_code': -1,
                'error_message': error_message,
                'redirect': url_for('reports_bp.analyze_user_sheet')}


def replace_figures_with_urls(figures):
    """ replace figure filenames with urls after upload
    """
    figures2 = copy.deepcopy(figures)
    from google_functions.google_storage import upload_file, get_signed_url_from_blob
    for kk, finfo in enumerate(figures):
        blob = upload_file(finfo["figure"])
        url = get_signed_url_from_blob(blob)
        figures2[kk]["url"] = url
    return figures2


@reports_bp.route('/retrieve_pdf', methods=["GET"])
def retrieve_pdf():
    """
    Helper to download the local file produced by an analysis run.
    """
    pdfname_only = request.args.get('fname')
    return send_from_directory("tmp", pdfname_only, as_attachment=True)


@reports_bp.route('/poc')
def poc():
    """
    A POC of google slides, for testing
    """
    doc_info = {
        'url': 'https://www.google.com',
        'email': os.environ["TEST_EMAIL"]}
    figures = [{'figure': 'tmp/fig0.png'},
               {'figure': 'tmp/fig1.png'},
               {'figure': 'tmp/fig2.png'}]
    replace_figures_with_urls(figures)
    doc_info["figures"] = figures

    out = google_functions.google_slides.make_slideshow(doc_info)
    return """<a href="%s">link</a>""" % out


@reports_bp.route('/analyze_user_sheet_results', methods=['GET'])
def analyze_user_sheet_results():
    # TODO, make this spin until the background job is complete
    from database.schema import ReportResult
    unique_tag = request.args.get('unique_tag')
    report_result = ReportResult.query.filter(
        ReportResult.unique_tag == unique_tag).first()
    service_email = get_service_account_email()
    if report_result is None:
        slides_url = ""
        user_email = flask.session.get("user_email", "")
    else:
        slides_url = report_result.slides_url
        user_email = report_result.user_email
        # Todo, make it so that people have to create an account
        # to access results

    pdf_filename = "tmp/latex_files_%s.pdf" % unique_tag
    pdf_filename = os.path.basename(pdf_filename)
    return render_template('reports/analyze_user_sheet_finished.html',
                           slides_url=slides_url,
                           user_email=user_email,
                           service_email=service_email,
                           pdf_filename=pdf_filename)


@reports_bp.route('/analyze_user_sheet', methods=['GET', 'POST'])
def analyze_user_sheet():
    """
    Takes in google sheet url, uploads automatic analysis and produces
    LaTeX report of the same. Also produces Google slides of the images
    and transfers ownership over.
    """
    from extensions import db
    from database.schema import ReportResult

    class SheetForm(FlaskForm):
        name = StringField('Sheet URL', validators=[DataRequired()])
        sheet_name = StringField('Targeted tab name to analyze',
                                 validators=[DataRequired()])
        email = StringField(
            'Email address to share results', validators=[DataRequired()])
        submit = SubmitField("Analyze")

    form = SheetForm(request.form)

    if form.validate_on_submit():
        from celery_jobs.background_analyze_user_sheet import background_analyze_user_sheet
        service_email = get_service_account_email()
        url = form.data["name"]
        sheet_name = form.data["sheet_name"]
        email = form.data["email"]

        # use background job to do the Google slides report
        unique_tag = generate_uuid()

        report_result = ReportResult(unique_tag=unique_tag,
                                     user_email=email,
                                     service_email=service_email)
        db.session.add(report_result)
        db.session.commit()

        background_analyze_user_sheet.delay(
            url, sheet_name, email, unique_tag, report_result.id)
        flash("Check email %s for messages from %s" % (email,
                                                       service_email))

        info = get_worksheet_from_url(
            url=url, sheet_name=sheet_name)
        if info['exit_code'] == 0:
            sheet = info['sheet']
            worksheet_to_read = info['worksheet']
        else:
            flash(Markup(info['error_message']))
            return redirect(info["redirect"])

        info = get_writeable_worksheet(
            sheet=sheet, sheet_name=sheet_name + '-analysis')
        if info['exit_code'] == 0:
            wks_out = info['sheet']
        else:
            flash(Markup(info['error_message']))
            return redirect(url_for('reports_bp.analyze_user_sheet'))

        # do the automatic analysis
        df = get_df_from_worksheet(worksheet_to_read,
                                   cleaning=True)

        analysis = perform_automatic_analysis(
            df,
            unique_tag=unique_tag,
            sheet_url=url,
            sheet_name=sheet_name)  # generate figures, save them on container with fig.savefig()

        basic_describe = analysis["basic_describe"]
        figures = analysis["figures"]

        # write out latex file using the unique id.
        tex_filename = "tmp/latex_files_%s.tex" % unique_tag
        auto_report = latex_reports.latex_doc.LatexDoc(
            tex_filename,
            preamble=latex_reports.STANDARD_PREAMBLE)

        doc_info = {'analysis_date': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'url': '#'.join(url.split('#')[0:-1]),
                    'sheet_name': sheet_name,
                    'raw_table': basic_describe,
                    'figures': figures,
                    'title': '',
                    'email': email,
                    'table': basic_describe.to_latex()}

        auto_report.add_contents(r"""\section{Analysis of sheet}
Analysis date: %(analysis_date)s \\
Data source:  \href{%(url)s}{Google sheet}, Tab:%(sheet_name)s \\

\section{Overall results}
%(table)s
""" % doc_info)
        auto_report.add_clearpage()
        for fig in figures:
            auto_report.add_figure(
                fig["figure"], caption=fig["caption"])
            auto_report.add_clearpage()

        auto_report.add_contents(r"""\section{Appendix}
- full url to data source: \href{%(url)s}{\url{%(url)s}}
""" % doc_info)
        pdfname = auto_report.write()

        # Produce Google slides version of the report.
        # slides_url = ""
        # set the new output dataframe
        wks_out.set_dataframe(basic_describe, (1, 1),
                              fit=True, nan='', copy_index=True)
        pdfname_only = os.path.basename(pdfname)
        assert os.path.isfile(os.path.join("tmp", pdfname_only))
        flask.session["user_email"] = email
        return redirect(url_for("reports_bp.analyze_user_sheet_results", unique_tag=unique_tag))

    return render_template('reports/analyze_user_sheet.html',
                           service_email=get_service_account_email(),
                           form=form, action="")


@reports_bp.route('/present_sheet', methods=['GET', 'POST'])
def present_sheet():
    """
    Takes in a url, upload pandas df to a google sheet and redirect there
    """
    class SheetForm(FlaskForm):
        name = StringField('Sheet URL', validators=[DataRequired()])
        sheet_name = StringField('Desired tab name',
                                 validators=[DataRequired()])
        submit = SubmitField("Submit")

    form = SheetForm(request.form)
    if form.validate_on_submit():
        gsheets = pygsheets.authorize(
            service_account_env_var="GOOGLE_APPLICATION_CREDENTIALS")
        url = form.data["name"]
        sheet_name = form.data["sheet_name"]
        slug = os.path.basename(os.path.split(url)[0])
        try:
            sheet = gsheets.open_by_key(slug)
            wks = sheet.worksheet_by_title(title=sheet_name)
        except pygsheets.exceptions.WorksheetNotFound:
            sheet = gsheets.open_by_key(slug)
            wks = sheet.add_worksheet(title=sheet_name)
        except HttpError as err:
            email = get_service_account_email()
            flash(Markup(
                "Permission is needed to modify the sheet. Give this email: %s permission to edit the sheet. " % email))
            return redirect(url_for('reports_bp.present_sheet'))

        # placeholder for more complicated function
        df = pd.DataFrame.from_dict({'x': [1, 2, 3],
                                     'y': ['a', 'b', 'c']})
        wks.set_dataframe(df, (1, 1), fit=True, nan='')
        flash(Markup('Success, click <a href="%s">here</a>' % url))
        return redirect(url_for('reports_bp.present_sheet'))

    form_html = render_template('partials/reports/basic_form.html',
                                form=form,
                                action=url_for('reports_bp.success'))

    return render_template('reports/present_sheet.html',
                           service_email=get_service_account_email(),
                           form_html=form_html)


@reports_bp.route('/success', methods=['POST'])
def success():
    return "Success"


@reports_bp.route('/latex_demo', methods=["GET"])
def latex_demo():
    from flask import send_from_directory
    dummy_file = r"""
\documentclass[12pt]{article}
\usepackage{graphicx}
\begin{document}
\section{Introduction}
This document is prepared in LaTeX, which may be integrated with python for automated reports easily.
\begin{enumerate}
\item{Item 1 - [Text here]}
\item{Item 2 - for an example ofembedded graphics, see Figure \ref{fig:label}}
\end{enumerate}
\begin{figure}
  \centering
\includegraphics[width=1\textwidth]{figures/getty_images.jpg}
\caption{Caption}
\label{fig:label}
\end{figure}
\end{document}
    """
    f = open("tmp/example_report.tex", "w")
    f.write(dummy_file)
    f.close()
    for j in range(3):
        out = os.system(
            "pdflatex -output-directory=/app/tmp /app/tmp/example_report.tex")
    if out == 0:
        return send_from_directory("/app/tmp", "example_report.pdf", as_attachment=True)
    else:
        return "Error"


@reports_bp.route('/upload_data', methods=["GET", "POST"])
def upload_data():
    class MyForm(FlaskForm):
        name = StringField('Label Name', validators=[DataRequired()])
        submit = SubmitField("Submit")

    form = MyForm(request.form)
    if form.validate_on_submit():
        # process form inputs here...
        # form.data["name"]
        return redirect(url_for('reports_bp.success'))

    html = render_template('partials/reports/basic_form.html',
                           form=form,
                           action=url_for('reports_bp.success'))

    return render_template('html.html',
                           html=html)
