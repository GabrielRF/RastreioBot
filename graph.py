from bokeh.plotting import figure
from bokeh.plotting import output_file
from bokeh.plotting import save
import configparser
import datetime
from datetime import date
from datetime import datetime
from datetime import timedelta
import pandas as pd
import sqlite3
import sys

if __name__ == '__main__':

    config = configparser.ConfigParser()
    config.sections()
    config.read('bot.conf')

    db1 = 'RastreioBot.db'
    table1 = 'RastreioBot'

    x_label = 'Tempo'
    y_label = 'Quantidade'

    conn1 = sqlite3.connect(db1)
    df1 = pd.read_sql_query('SELECT * FROM ' + table1 + ' ORDER BY data ASC', 
        conn1, parse_dates=['data'])
    print(df1[-5:])
    conn1.close()

    output_file('/var/www/RastreioBot.html')

    p = figure(x_axis_type="datetime", title='RastreioBot',
        toolbar_location="above",
        tools='resize,pan,box_zoom,crosshair,wheel_zoom,reset')
    p.xaxis.axis_label = x_label
    p.yaxis.axis_label = y_label

    p.circle(df1['data'], df1['usuarios'], color='red', alpha=1, legend='Usuarios')
    p.line(df1['data'], df1['usuarios'], color='red', alpha=1, legend='Usuarios')
    p.circle(df1['data'], df1['andamento'], color='green', alpha=1, legend='Andamento')
    p.line(df1['data'], df1['andamento'], color='green', alpha=1, legend='Andamento')
    p.circle(df1['data'], df1['finalizados'], color='blue', alpha=1, legend='Finalizados')
    p.line(df1['data'], df1['finalizados'], color='blue', alpha=1, legend='Finalizados')
    p.legend.location = "top_left"

    save(p)

