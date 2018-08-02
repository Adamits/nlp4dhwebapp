import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.dates import date2num
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import io
import base64
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages

"""
This is for graphing with matplotlib. From this class, we can get the base64 of a bar graph
with years on the x axis, and counts on the y axis for clusters of query bars.

This will be extended to line graphs, and to more dynamic graphs than just years x counts.

the save_YYY methods are for saving a base64 string as a file in YYY format. It takes in the
base64 as an argument so that our stateless web app can pass around that base64 serialized string
and ask for the file in a request.
"""

class Graph():
    def __init__(self, x, labels, data):
        # Should be the years
        self.x = x
        # Should be the queries
        self.labels = labels
        # x axis labels, by # bars per label
        # aka, queries x years
        self.data = data
        self.figure = None
        self.figure = self.figure if self.figure else self._make_figure()

    def _make_figure(self):
        width = .1
        fig=plt.figure()
        ax=fig.add_subplot(111)

        idx = np.arange(len(self.x))

        for i, d in enumerate(self.data):
            coords = [i*width+j for j in range(len(d))]
            ax.bar(coords, height=d, width=width, align='center')

        plt.legend(self.labels, loc='upper right')
        ax.set_xticks([x + width for x in idx])
        ax.set_xticklabels(self.x)

        return fig

    def get_base64(self):
        fig = self.figure
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        plt.close(fig)
        buf.seek(0)  # rewind to beginning of file
        fig_png = base64.b64encode(buf.getvalue())
        return fig_png.decode('utf8')

    def save_PDF(self, fn):
        pdf_path = settings.CORPORA_DIR + fn + '.pdf'
        f = self.figure

        pp = PdfPages(pdf_path)
        pp.savefig(f)
        pp.close()

        return pdf_path

    def save_PNG(self, fn):
        png_path = settings.CORPORA_DIR + fn + '.png'
        f = self.figure
        FigureCanvas(f)
        f.savefig(png_path)

        return png_path

    def save_as(self, fn, f_type):
        if f_type.lower() == "pdf":
            return self.save_PDF(fn)
        elif f_type.lower() == "png":
            return self.save_PNG(fn)
        else:
            raise Exception("Unimplemented filetype: %s" % f_type)
