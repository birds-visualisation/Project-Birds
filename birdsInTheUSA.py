import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objs as go
from mpl_toolkits.basemap import Basemap
from Fond2carte import *
import calendar
import numpy as np
from scrap import *
import time

from plotly.graph_objs import Scattermapbox, Data, Layout
mapbox_access_token = 'pk.eyJ1IjoiYXVyZWR0Nzg5MiIsImEiOiJjamlscm5seHYwang4M3Bzem91NnFnbWh1In0.qLkGWDjKPKdG37SRQzp_Tg'

stateslatlong = pd.read_csv("stateslatlong.csv", sep=";", header=None)

# Lancement du serveur
app = dash.Dash()

app.css.append_css({
    "external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"
})

target_lock = False
state_lock = ""
lock = False
pos_lock = [0, 0]


# min max carte
extrema = [-130, -60, 20, 55]
list_seasons = np.array(['Winter', 'Spring', 'Summer', 'Autumn'])

# Objet basemap
m = Basemap(projection='merc',
            llcrnrlon=extrema[0], urcrnrlon=extrema[1],
            llcrnrlat=extrema[2], urcrnrlat=extrema[3],
            rsphere=6371200., resolution='c', area_thresh=10000)

traces_cc = get_coastline_traces(
    m) + get_country_traces(m)+get_state_traces(m)

df = pd.read_csv('df_2005_2016_2.csv')


def preprocess(df):
    species = pd.DataFrame(
        {'species': df.columns[7:-1], 'int_species': range(0, len(df.columns[7:-1]))})
    df = df.set_index(['DATE', 'LATITUDE', 'LONGITUDE',
                       'COUNT_TYPE', 'STATE_PROVINCE'])
    df = pd.DataFrame(df.iloc[:, 3:-1].stack()).reset_index()
    df.columns = list(df.columns[:-2]) + ['species', 'count']
    df = df[df['count'] != 0]
    df = pd.merge(species, df, on='species')
    df = df.set_index('DATE')
    df.index = pd.to_datetime(df.index)

    df = df[(df.LONGITUDE > (extrema[0]+10)) &
            (df.LONGITUDE < (extrema[1]-10))]
    #df = df[(df.LATITUDE > (extrema[2]+10)) & (df.LATITUDE < (extrema[3]-10))]
    df['year'] = df.index.year
    df['season'] = ((df.index.month-1)//3)+1
    df['month'] = df.index.month
    return df


df = preprocess(df)
available_indicators = df['species'].unique()

cur_year = df['year'].max()
cur_season = df['season'].max()
cur_month = df['month'].max()

app.layout = html.Div([
    html.Div(id="interface", children=[

        html.Div([

            html.Div([
                dcc.Dropdown(
                    id='select-species1',
                    options=[{'label': i, 'value': i}
                             for i in available_indicators],
                    value='Species1'
                )], style={'width': '49%', 'display': 'inline-block'}),
            html.Div([
                dcc.Dropdown(
                    id='select-species2',
                    options=[{'label': i, 'value': i}
                             for i in available_indicators],
                    value='Species2'
                )], style={'width': '49%', 'display': 'inline-block'})
        ]),

        html.Div([

            html.Div([
                dcc.RadioItems(
                    id='crossfilter-step',
                    options=[{'label': i, 'value': i}
                             for i in ['year', 'season', 'month']],
                    value='year',
                    labelStyle={'display': 'inline-block'}
                )], style={'width': '49%', 'display': 'inline-block', 'float': 'left'}),

            html.Div(id='controls-container-radio', children=[
                dcc.RadioItems(
                    id='crossfilter-groupby',
                    options=[{'label': i, 'value': i}
                             for i in ['all', 'by a given season', 'by a given month']],
                    value='all',
                    labelStyle={'display': 'inline-block'}
                )], style={'width': '49%', 'display': 'inline-block', 'float': 'right'})
        ], style={'width': '100%', 'display': 'inline-block', 'padding': '10px 5px', "height": 20}
        )],
        style={
            'borderBottom': 'thin lightgrey solid',
            'backgroundColor': 'rgb(250, 250, 250)',
            'height': 80}),

    html.Div(id="bird-info", children=[
        html.Div([
            html.Div([
                html.A(html.Img(id="img-bird1", width=80,
                                height=60), id="link-bird1")
            ], style={'width': '15%', 'float': 'left', 'padding': '10px 2px'}),
            html.Div([
                html.P(id="text-bird1"),
            ], style={'width': '75%',
                      "height": 62,
                      'float': 'left',
                      "border-radius": "5px",
                      "padding": "0.5em 1em",
                      "box-decoration-break": "clone",
                      "overflow": "auto",
                      "border-width": "2px",
                      "border-style": "solid",
                      "border-color": "#33bbff"
                      })
        ],
            style={'width': '49%', 'float': 'left', 'padding': '1px 1px'}
        ),

        html.Div([
            html.Div([
                html.A(html.Img(id="img-bird2", width=80,
                                height=60), id="link-bird2")
            ], style={'width': '15%', 'float': 'left', 'padding': '10px 5px'}),
            html.Div([
                html.P(id="text-bird2"),
            ], style={'width': '75%',
                      "height": 62,
                      'float': 'left',
                      "border-radius": "5px",
                      "padding": "0.5em 1em",
                      "box-decoration-break": "clone",
                      "overflow": "auto",
                      "border-width": "2px",
                      "border-style": "solid",
                      "border-color": "#33bbff"})

        ],
            style={'width': '49%', 'float': 'left', 'padding': '1px 1px'}
        ),
    ], style={'display': 'inline-block', 'width': '100%'}),

    html.Div(id="graph", children=[
        html.Div([
            dcc.Graph(
                id='crossfilter-graph1',
                hoverData={'points': [{'customdata': 'California'}]})
        ], style={'width': '48%', 'display': 'inline-block', "vertical-align": "top", "padding": "5px 5px"}),


        html.Div([
            dcc.Graph(id='crossfilter-graph2'),
            dcc.Graph(id='polulation_bird')

        ], style={'width': '49%', 'display': 'inline-block'})

    ], style={'display': 'inline-block', 'width': '100%'}),

    html.Div(id='slider', children=[
        html.Div(id='controls-container-slider1',
                 children=[
                     dcc.Slider(
                         id='crossfilter-year--slider',
                         min=df['year'].min(),
                         max=df['year'].max(),
                         value=df['year'].max(),
                         step=None,
                         marks={str(st): str(st) for st in df['year'].unique()}), ],
                 style={'width': '45%', 'padding': '0px 5px 5px 5px'}),

        html.Div(id='controls-container-slider2',
                 children=[
                     dcc.Slider(
                         id='crossfilter-season--slider',
                         min=df['season'].min(),
                         max=df['season'].max(),
                         value=df['season'].max(),
                         step=None,
                         marks={str(st): list_seasons[st-1]
                                for st in df['season'].unique()},
                         disabled=True)],
                 style={'width': '45%', 'padding': '0px 5px 5px 5px'}),

        html.Div(id='controls-container-slider3',
                 children=[
                     dcc.Slider(
                         id='crossfilter-month--slider',
                         min=df['month'].min(),
                         max=df['month'].max(),
                         value=df['month'].max(),
                         step=None,
                         marks={str(st): calendar.month_abbr[st]
                                for st in df['month'].unique()},
                         disabled=True)],
                 style={'width': '45%', 'padding': '0px 5px 5px 5px'})
    ], style={'width': '90%', "vertical-align": "top", 'padding': '0px 5px 5px 5px'})
])

# Pour graph de droite


def make_geo(dff, species1, species2, state, title):

    lat_center = stateslatlong[stateslatlong[0] == state][1].values[0]
    lon_center = stateslatlong[stateslatlong[0] == state][2].values[0]

    lon = dff[dff.species == species1].LONGITUDE
    lon_extrema = [lon.min()-5, lon.max()+5]

    lat = dff[dff.species == species1].LATITUDE
    lat_extrema = [lat.min()-5, lat.max()+5]
    return {
        'data': [
            go.Scattermapbox(
                lon=dff[dff.species == species1].LONGITUDE,
                lat=dff[dff.species == species1].LATITUDE,
                text=dff['species'],
                mode='markers',
                name=species1,
                marker=dict(
                    size=1.5 * np.log(dff[dff.species == species1]['count']),
                    opacity=0.5,
                    color='red',
                    symbol='circle',
                )),
            go.Scattermapbox(
                lon=dff[dff.species == species2].LONGITUDE,
                lat=dff[dff.species == species2].LATITUDE,
                text=dff['species'],
                mode='markers',
                name=species2,
                marker=dict(
                    size=1.5 * np.log(dff[dff.species == species2]['count']),
                    opacity=0.5,
                    color='green',
                    symbol='circle',
                )),
        ],
        'layout': {
            'autosize': 'False',
            'hovermode': 'closest',
            'mapbox': dict(
                accesstoken=mapbox_access_token,
                bearing=0,
                pitch=0,
                zoom=4,
                center=dict(
                    lat=lat_center,
                    lon=lon_center
                ),
                style='outdoors'
            ),
            'hovermode': 'closest',
            'height': 225,
            'margin': {'l': 20, 'b': 30, 'r': 10, 't': 10},
            'annotations': [{
                'x': 0, 'y': 0.85, 'xanchor': 'left', 'yanchor': 'bottom',
                'xref': 'paper', 'yref': 'paper', 'showarrow': False,
                'align': 'left', 'bgcolor': 'rgba(255, 255, 255, 0.5)',
                'text': title
            }],
            'yaxis': {'type': 'linear'},
            'xaxis': {'showgrid': False}
        }
    }


@app.callback(
    dash.dependencies.Output('crossfilter-year--slider', 'disabled'),
    [dash.dependencies.Input('crossfilter-step', 'value'), ])
def disable_slider1(step_type):
    return step_type != 'year'


@app.callback(
    dash.dependencies.Output('crossfilter-season--slider', 'disabled'),
    [dash.dependencies.Input('crossfilter-step', 'value'),
     dash.dependencies.Input('crossfilter-groupby', 'value')
     ])
def disable_slider2(step_type, groupby):
    return not((step_type == 'season') | ((step_type == 'year') & (groupby == 'by a given season')))


@app.callback(
    dash.dependencies.Output('crossfilter-month--slider', 'disabled'),
    [dash.dependencies.Input('crossfilter-step', 'value'),
     dash.dependencies.Input('crossfilter-groupby', 'value')
     ])
def disable_slider3(step_type, groupby):
    return not((step_type == 'month') | ((step_type == 'year') & (groupby == 'by a given month')))


@app.callback(
    dash.dependencies.Output('controls-container-radio', 'style'),
    [dash.dependencies.Input('crossfilter-step', 'value')])
def display_groupby(toggle_value):
    if toggle_value != 'year':
        return {'display': 'none'}
    else:
        return {'display': 'block'}


@app.callback(
    dash.dependencies.Output('controls-container-slider1', 'style'),
    [dash.dependencies.Input('crossfilter-step', 'value')])
def display_slider1(toggle_value):
    if toggle_value != 'year':
        return {'display': 'none'}
    else:
        return {'display': 'block', 'width': '49%', 'padding': '0px 20px 20px 20px'}


@app.callback(
    dash.dependencies.Output('controls-container-slider2', 'style'),
    [dash.dependencies.Input('crossfilter-step', 'value'),
     dash.dependencies.Input('crossfilter-groupby', 'value')])
def display_slider2(step_type, groupby):
    if not ((step_type == 'season') | ((step_type == 'year') & (groupby == 'by a given season'))):
        return {'display': 'none'}
    else:
        return {'display': 'block', 'width': '49%', 'padding': '0px 20px 20px 20px'}


@app.callback(
    dash.dependencies.Output('controls-container-slider3', 'style'),
    [dash.dependencies.Input('crossfilter-step', 'value'),
     dash.dependencies.Input('crossfilter-groupby', 'value')])
def display_slider3(step_type, groupby):
    if not ((step_type == 'month') | ((step_type == 'year') & (groupby == 'by a given month'))):
        return {'display': 'none'}
    else:
        return {'display': 'block', 'width': '49%', 'padding': '0px 20px 20px 20px'}


@app.callback(
    dash.dependencies.Output('bird-info', 'style'),
    [dash.dependencies.Input('select-species1', 'value'),
     dash.dependencies.Input('select-species2', 'value')])
def display_bird_info(species1, species2):
    if species1 == "Species1" or species2 == "Species2":
        return {'display': 'none'}
    else:
        return {'display': 'block'}


@app.callback(
    dash.dependencies.Output('img-bird1', 'src'),
    [dash.dependencies.Input('select-species1', 'value')])
def update_bird1_img(species1):
    s, img, link = get_bird_info(species1)
    if species1 == "Species1":
        return None
    else:
        return img


@app.callback(
    dash.dependencies.Output('text-bird1', 'children'),
    [dash.dependencies.Input('select-species1', 'value')])
def update_bird1_text(species1):
    s, img, link = get_bird_info(species1)
    if species1 == "Species1":
        return None
    else:
        # return s.split("\n")[-1][:250] + " ..."
        return s.split("\n")[-1]


@app.callback(
    dash.dependencies.Output('link-bird1', 'href'),
    [dash.dependencies.Input('select-species1', 'value')])
def update_bird1_link(species1):
    s, img, link = get_bird_info(species1)
    if species1 == "Species1":
        return None
    else:
        return link


@app.callback(
    dash.dependencies.Output('img-bird2', 'src'),
    [dash.dependencies.Input('select-species2', 'value')])
def update_bird2_img(species2):
    s, img, link = get_bird_info(species2)
    if species2 == "Species2":
        return None
    else:
        return img


@app.callback(
    dash.dependencies.Output('text-bird2', 'children'),
    [dash.dependencies.Input('select-species2', 'value')])
def update_bird2_text(species2):
    s, img, link = get_bird_info(species2)
    if species2 == "Species2":
        return None
    else:
        return s.split("\n")[-1]


@app.callback(
    dash.dependencies.Output('link-bird2', 'href'),
    [dash.dependencies.Input('select-species2', 'value')])
def update_bird2_link(species2):
    s, img, link = get_bird_info(species2)
    if species2 == "Species2":
        return None
    else:
        return link


@app.callback(
    dash.dependencies.Output('crossfilter-graph2', 'figure'),
    [dash.dependencies.Input('crossfilter-graph1', 'hoverData'),
     dash.dependencies.Input('crossfilter-graph1', 'clickData'),
     dash.dependencies.Input('crossfilter-step', 'value'),
     dash.dependencies.Input('select-species1', 'value'),
     dash.dependencies.Input('select-species2', 'value'),
     dash.dependencies.Input('crossfilter-year--slider', 'value'),
     dash.dependencies.Input('crossfilter-season--slider', 'value'),
     dash.dependencies.Input('crossfilter-month--slider', 'value'),
     dash.dependencies.Input('crossfilter-groupby', 'value')])
def update_graph2(hoverData, clickData, step_type, species1, species2, year_value,
                  season_value, month_value, groupby):
    global target_lock
    global state_lock
    global lock

    time.sleep(.300)
    while lock:
        pass

    if target_lock is True:
        state_name = state_lock
    else:
        state_name = hoverData['points'][0]['customdata']

    dff = df[df['STATE_PROVINCE'] == state_name]
    if (step_type == 'year') & (groupby == 'all'):
        dff = dff[dff[step_type] == year_value]
    elif (step_type == 'year') & (groupby == 'by a given season'):
        dff = dff[(dff[step_type] == year_value) &
                  (dff['season'] == season_value)]
    elif (step_type == 'year') & (groupby == 'by a given month'):
        dff = dff[(dff[step_type] == year_value) &
                  (dff['month'] == month_value)]
    elif step_type == 'season':
        dff = dff[dff[step_type] == season_value]
    elif step_type == 'month':
        dff = dff[dff[step_type] == month_value]
    return make_geo(dff, species1, species2, state_name, '')


@app.callback(
    dash.dependencies.Output('polulation_bird', 'figure'),
    [dash.dependencies.Input('crossfilter-graph1', 'hoverData'),
     dash.dependencies.Input('crossfilter-graph1', 'clickData'),
     dash.dependencies.Input('crossfilter-step', 'value'),
     dash.dependencies.Input('select-species1', 'value'),
     dash.dependencies.Input('select-species2', 'value'),
     dash.dependencies.Input('crossfilter-year--slider', 'value'),
     dash.dependencies.Input('crossfilter-season--slider', 'value'),
     dash.dependencies.Input('crossfilter-month--slider', 'value'),
     dash.dependencies.Input('crossfilter-groupby', 'value')])
def update_hist(hoverData, clickData, step_type, species1, species2, year_value,
                season_value, month_value, groupby):

    global target_lock
    global state_lock
    global lock

    time.sleep(.300)
    while lock:
        pass

    if target_lock is True:
        state_name = state_lock
    else:
        state_name = hoverData['points'][0]['customdata']
    tickmode = 'linear'
    if step_type == 'season':
        step_type = 'season2'
    if (step_type == 'year') & (groupby == 'by a given season'):
        step_type = ['year', 'season2']
    elif (step_type == 'year') & (groupby == 'by a given month'):
        step_type = ['year', 'month']
        tickmode = 'auto'

    dff = df
    dff['season2'] = list_seasons[df.season-1]
    dff1 = dff[(dff['STATE_PROVINCE'] == state_name)
               & (dff.species == species1)]
    dff2 = dff[(dff['STATE_PROVINCE'] == state_name)
               & (dff.species == species2)]
    dff1 = dff1.groupby(step_type).sum()[['count']]
    dff2 = dff2.groupby(step_type).sum()[['count']]
    dff1['date'] = dff1.index.values
    dff2['date'] = dff2.index.values

    if type(step_type) != str:
        dff1['date'] = dff1['date'].apply(
            lambda x: '-'.join([str(elt) for elt in x]))
        dff2['date'] = dff2['date'].apply(
            lambda x: '-'.join([str(elt) for elt in x]))
    if species2 != 'Species2':
        return{
            'data': [
                go.Bar(
                    x=dff1['date'],
                    y=dff1['count'],
                    text=species1,
                    opacity=0.5,
                    marker=dict(color='red'),
                    name=species1
                ),
                go.Bar(
                    x=dff2['date'],
                    y=dff2['count'],
                    text=species2,
                    opacity=0.5,
                    marker=dict(color='green'),
                    name=species2
                )
            ],
            'layout': go.Layout(
                title='Bird population in '+state_name,
                # xaxis={'title': 'Date'},
                xaxis={'title': 'Date', 'tickmode': tickmode,
                       'nticks': len(dff1['date'].unique())},
                yaxis={'title': 'Polulation'},
                margin={'l': 80, 'b': 100, 't': 40, 'r': 10},
                legend={'x': 0, 'y': 1},
                height=300,
                hovermode='closest'
            )
        }
    else:
        return{
            'data': [
                go.Bar(
                    x=dff1['date'],
                    y=dff1['count'],
                    text=species1,
                    opacity=0.5,
                    marker=dict(color='red'),
                    name=species1
                )
            ],
            'layout': go.Layout(
                title='Bird population in '+state_name,
                # xaxis={'title': 'Date'},
                xaxis={'title': 'Date', 'tickmode': tickmode,
                       'nticks': len(dff1['date'].unique())},
                yaxis={'title': 'Polulation'},
                margin={'l': 80, 'b': 100, 't': 40, 'r': 10},
                legend={'x': 0, 'y': 1},
                height=300,
                hovermode='closest'
            )
        }


@app.callback(
    dash.dependencies.Output('crossfilter-graph1', 'figure'),
    [dash.dependencies.Input('crossfilter-step', 'value'),
     dash.dependencies.Input('crossfilter-graph1', 'clickData'),
     dash.dependencies.Input('select-species1', 'value'),
     dash.dependencies.Input('select-species2', 'value'),
     dash.dependencies.Input('crossfilter-year--slider', 'value'),
     dash.dependencies.Input('crossfilter-season--slider', 'value'),
     dash.dependencies.Input('crossfilter-month--slider', 'value'),
     dash.dependencies.Input('crossfilter-groupby', 'value')])
def update_graph(step_type, clickData, column1_name, column2_name,
                 year_value, season_value, month_value, groupby):

    global lock
    global state_lock
    global target_lock
    global pos_lock
    global cur_year
    global cur_season
    global cur_month

    lock = True

    toggle_slider = False
    if cur_year != year_value:
        toggle_slider = True
    elif cur_season != season_value:
        toggle_slider = True
    elif cur_month != month_value:
        toggle_slider = True

    cur_year = year_value
    cur_season = season_value
    cur_month = month_value

    if (step_type == 'year') & (groupby == 'all'):
        dff = df[df[step_type] == year_value]
    elif (step_type == 'year') & (groupby == 'by a given season'):
        dff = df[(df[step_type] == year_value) &
                 (df['season'] == season_value)]
    elif (step_type == 'year') & (groupby == 'by a given month'):
        dff = df[(df[step_type] == year_value) & (df['month'] == month_value)]
    elif step_type == 'season':
        dff = df[df[step_type] == season_value]
    elif step_type == 'month':
        dff = df[df[step_type] == month_value]

    res = {
        'data': traces_cc+[
            dict(
                type='histogram2dcontour',
                x=dff[dff['species'] == column1_name]['LONGITUDE'],
                y=dff[dff['species'] == column1_name]['LATITUDE'],
                z=dff[dff['species'] == column1_name]['count'],
                histnorm="percent",
                text=dff[dff['species'] == column1_name]['species'],
                colorscale=[[0, 'rgba(255, 204, 204,0)'], [0.1, 'rgba(255, 204, 204,0.5)'], [
                    1, 'rgba(255, 0, 0,1)']],
                showscale=False,
                opacity=1,
                visible=True,
                line=dict(width=0),),
            dict(
                type='histogram2dcontour',
                x=dff[dff['species'] == column2_name]['LONGITUDE'],
                y=dff[dff['species'] == column2_name]['LATITUDE'],
                z=dff[dff['species'] == column2_name]['count'],
                colorscale=[[0, 'rgba(153, 255, 153,0)'], [0.1, 'rgba(153, 255, 153,0.5)'], [
                    1, 'rgba(0, 255, 0,1)']],
                showscale=False,
                opacity=0.4,
                visible=True,
                histnorm="percent",
                line=dict(width=0),),
            dict(
                type='scattergl',
                x=stateslatlong[2][(stateslatlong[0] != "Hawaii") & (
                    stateslatlong[0] != "Alaska")],
                y=stateslatlong[1][(stateslatlong[0] != "Hawaii") & (
                    stateslatlong[0] != "Alaska")],
                text=stateslatlong[0][(stateslatlong[0] != "Hawaii") & (
                    stateslatlong[0] != "Alaska")],
                customdata=stateslatlong[0][(stateslatlong[0] != "Hawaii") & (
                    stateslatlong[0] != "Alaska")],
                mode='markers',
                marker={
                    'size': 15,
                    'opacity': 0,
                    'line': {'width': 0.5, 'color': 'white'}
                })
        ],
        'layout': go.Layout(
            showlegend=False,
            margin={'l': 40, 'b': 10, 't': 10, 'r': 0},
            height=450,
            hovermode='closest',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis={'visible': False, 'range': extrema[0:2]},
            yaxis={'visible': False, 'range': extrema[2:]}
        )
    }

    if target_lock is True and toggle_slider is True:
        selector = dict(
            type='scattergl',
            x=[pos_lock[0]],
            y=[pos_lock[1]],
            mode='markers',
            marker={
                'symbol': 'x',
                'size': 15,
                'opacity': 1,
                'color': 'red',
                'line': {'width': 0.5, 'color': 'white'}
            })
        res["data"].append(selector)
        lock = False
        return res
    if target_lock is False and toggle_slider is True:
        lock = False
        return res

    elif clickData:
        selector = dict(
            type='scattergl',
            x=[clickData["points"][0]["x"]],
            y=[clickData["points"][0]["y"]],
            mode='markers',
            marker={
                'symbol': 'x',
                'size': 15,
                'opacity': 1,
                'color': 'red',
                'line': {'width': 0.5, 'color': 'white'}
            })

        if target_lock is False:
            res["data"].append(selector)
            state_lock = clickData['points'][0]['customdata']
            target_lock = True
            pos_lock[0] = clickData['points'][0]['x']
            pos_lock[1] = clickData['points'][0]['y']
        elif (clickData['points'][0]['customdata'] == state_lock) and (target_lock is True):
            state_lock = ""
            target_lock = False
        elif (clickData['points'][0]['customdata'] != state_lock) and (target_lock is True):
            res["data"].append(selector)
            state_lock = clickData['points'][0]['customdata']
            target_lock = True
            pos_lock[0] = clickData['points'][0]['x']
            pos_lock[1] = clickData['points'][0]['y']

        lock = False
        return res

    else:
        lock = False
        return res


if __name__ == '__main__':
    app.run_server()
