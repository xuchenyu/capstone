import requests, os
import cPickle as pickle
import pandas as pd
import numpy as np
from flask import Flask, render_template, request, redirect

from bokeh.embed import components
from bokeh.charts import Bar
from bokeh.models.glyphs import Circle
from collections import OrderedDict
from bokeh.models import (GMapPlot, GMapOptions, Range1d, ColumnDataSource, 
                          PanTool, WheelZoomTool, BoxSelectTool, ResetTool, PreviewSaveTool, HoverTool)

app = Flask(__name__)

@app.route('/')
def main():
    return redirect('/index')

@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/graph', methods=['POST'])
def show_graph():
    df_bikes = pickle.load(open('./static/df_bikes.pickle', 'r'))
    df_stations = pickle.load(open('./static/df_stations.pickle', 'r'))
    
    # obtain the bikeid from the form
    form_data = request.form
    if form_data.get('submit'):
        try:
            bikeid = int(form_data.get('bikeid'))
        except ValueError:
            return redirect('/index')
        if bikeid not in df_bikes.index:
            return redirect('/index')
    elif form_data.get('generate'):
        bikeid = int(np.random.choice(df_bikes.index))
    
    # make plots
    n_trips = int(df_bikes.ix[bikeid].n_trips)
    n_maints = int(df_bikes.ix[bikeid].n_maints)
    n_maints_month = int(df_bikes.ix[bikeid].n_maints_month)
    n_maints_area = int(df_bikes.ix[bikeid].n_maints_area)
    month_cols = range(2, 14)
    cluster_cols = range(14, 23)

    df_bikeid = pd.DataFrame.from_dict({'n_trips': df_bikes.ix[bikeid][month_cols], 'month': range(1, 13)})
    p_months = Bar(df_bikeid, label='month', values='n_trips', 
                   title='Trips by Month', title_text_font_size='20', 
                   ylabel='Count')
    script_months, div_months = components(p_months)
    
    lons = df_stations.longitude
    lats = df_stations.latitude
    names = df_stations.name
    clusters = df_stations.cluster+1
    sizes = [df_stations.groupby('cluster')['name'].count()[cl] for cl in df_stations.cluster]
    
    ns_trips = [int(df_bikes.ix[bikeid][cl+14]) for cl in df_stations.cluster]
    color_map = ['#ffffcc', '#ffeda0', '#fed976', '#feb24c', '#fd8d3c', '#fc4e2a', '#e31a1c', '#bd0026', '#800026']
    order_cluster = [int(CL[-1]) for CL in df_bikes.ix[bikeid][cluster_cols].order().index]
    converter = dict(zip(order_cluster, range(9)))
    colors = [color_map[converter[cl+1]] for cl in df_stations.cluster]
    
    map_options = GMapOptions(lat=41.8827, lng=-87.6227, map_type="roadmap", zoom=11)
    p_clusters = GMapPlot(x_range=Range1d(), y_range=Range1d(), 
                          map_options=map_options, title='Trips by Area')
    p_clusters.add_tools(PanTool(), WheelZoomTool(), BoxSelectTool(), PreviewSaveTool(), ResetTool(), HoverTool())
    source = ColumnDataSource(data=dict(lon=lons, lat=lats, radius=[12.5]*300, color=colors, 
                                        name=names, cluster=clusters, size=sizes, n_trips=ns_trips))
    circle = Circle(x="lon", y="lat", size="radius", fill_color="color", line_color=None, fill_alpha=1.0)
    p_clusters.add_glyph(source, circle)
    hover = p_clusters.select(dict(type=HoverTool))
    hover.point_policy = "follow_mouse"
    hover.tooltips = OrderedDict([("Station", "@name"), ("Area", "@cluster"), 
                                  ("Size", "@size stations"), ("Trips", "@n_trips")])
    script_clusters, div_clusters = components(p_clusters)
    
    return render_template('graph.html', 
                           bikeid=bikeid, n_trips=n_trips, n_maints=n_maints, 
                           n_maints_month=n_maints_month, n_maints_area=n_maints_area, 
                           script_months=script_months, div_months=div_months, 
                           script_clusters=script_clusters, div_clusters=div_clusters)

    @app.route('/analysis')
    def show_analysis():
        return render_template('analysis.html')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

