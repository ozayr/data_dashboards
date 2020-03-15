from covid19app import app
import json, plotly
from flask import render_template
from data_prep.data_get_prep import return_figs,get_totals # my data wrangling file

@app.route('/')
@app.route('/index')
def index():

    figures = return_figs()
    # plot ids for the html id tag
    ids = ['figure-{}'.format(i) for i, _ in enumerate(figures)]

    confs,recs,deaths = get_totals()
    # Convert the plotly figures to JSON for javascript in html template
    figuresJSON = json.dumps(figures, cls=plotly.utils.PlotlyJSONEncoder)

    return render_template('index.html',
                           total_confirms = confs,
                           total_recovered = recs,
                           total_deaths= deaths,
                           ids=ids,
                           figuresJSON=figuresJSON)
