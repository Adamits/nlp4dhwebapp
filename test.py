import datetime
from django.http import HttpResponse

import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.dates import DateFormatter, date2num
import io

if __name__=='__main__':
  fig=plt.figure()
  ax=fig.add_subplot(111)
  dates = [datetime.datetime(2011, 1, 4, 0, 0),
     datetime.datetime(2011, 1, 5, 0, 0),
     datetime.datetime(2011, 1, 6, 0, 0)]

  data = [("label1", [4, 9, 2]), ("label2", [1,2,3]), ("label3", [11,12,13])]
  colors = ['r', 'g', 'b']

  x = dates
  x = date2num(dates)
  x_scale = list(range(int(-len(x)/2), 0))
  # Add 1 if odd
  endrange = int(len(x)/2) if len(x) % 2 == 0 else int(len(x)/2)+1
  x_scale += list(range(0, endrange))

  for i, tup in enumerate(data):
      l, d = tup
      ax.bar(x+x_scale[i]*0.2, d,width=0.2, color=colors[i], align='center')

  plt.legend([l for l, d in data], loc='upper center', bbox_to_anchor=(0.5,-0.1))
  ax.xaxis_date()
