from dash import Dash, html, dcc
import plotly.express as px
import pandas as pd

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = Dash('tiny reserving engine', external_stylesheets=external_stylesheets)

# assume you have a "long-form" data frame
# see https://plotly.com/python/px-arguments/ for more options
df = pd.DataFrame({
    "Fruit": ["Apples", "Oranges", "Bananas", "Apples", "Oranges", "Bananas"],
    "Amount": [4, 1, 2, 2, 4, 5],
    "City": ["SF", "SF", "SF", "Montreal", "Montreal", "Montreal"]
})

fig = px.bar(df, x="Fruit", y="Amount", color="City", barmode="group")

app.layout = html.Div(children=[
    html.H1(children='tiny actuarial engine'),
    html.Div(children= [html.Button(id='home_link', children='home'),
                        html.Button(id='upload_link', children='upload')],
             style={'width':'30%'}),
    dcc.Markdown(children='''
       ### This is a test 
       with no apparent result
    '''),

])

if __name__ == '__main__':
    app.run_server(debug=True)