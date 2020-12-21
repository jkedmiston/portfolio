import os
import latex_reports


def test_latex_report(app):
    with app.test_request_context():
        a = latex_reports.latex_doc.LatexDoc(
            "tmp/latex_test.tex", preamble=latex_reports.STANDARD_PREAMBLE)
        a.add_contents(r"""\section{Hello}""")
        out = a.write()
        assert os.path.isfile(out)
        assert out.split('.')[-1] == 'pdf'
        out = os.system("rm %s" % out)
        assert out == 0
