import pandas as pd
import numpy as np
import datetime as dt
import io
from dash import Dash, dcc, html, Input, Output, dash_table

import base64

def generate_analysis_id():
    date_now = dt.datetime.utcnow()
    comp_tag = 'tia'
    comp_rand = str(int(np.random.uniform(0,1e9)))
    comp_year = str(date_now.year)
    comp_month = str(date_now.month)
    comp_day = str(date_now.day)
    
    return'_'.join([comp_tag, comp_year, comp_month, comp_day, comp_rand])



def parse_upload(contents, filename):
    
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')))
    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file.'
        ])

    return df
