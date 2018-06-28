import plotly.plotly as py
import numpy as np
from plotly.graph_objs import Scatter, Line
from mpl_toolkits.basemap import Basemap

# Methode get_paths ==> liste de points (pour le tracé)

# Make trace-generating function (return a Scatter object)


def make_scatter(x, y, color):
    return Scatter(
        x=x,
        y=y,
        mode='lines',
        line=Line(color=color, width=0.5),
        name=' '  # no name on hover
    )

# Functions converting coastline/country polygons to lon/lat traces


def polygons_to_traces(m, poly_paths, N_poly, color):
    ''' 
    pos arg 1. (poly_paths): paths to polygons
    pos arg 2. (N_poly): number of polygon to convert
    '''
    traces = []  # init. plotting list

    for i_poly in range(N_poly):
        poly_path = poly_paths[i_poly]

        # get the Basemap coordinates of each segment
        coords_cc = np.array(
            [(vertex[0], vertex[1])
             for (vertex, code) in poly_path.iter_segments(simplify=False)]
        )

        # convert coordinates to lon/lat by 'inverting' the Basemap projection
        lon_cc, lat_cc = m(coords_cc[:, 0], coords_cc[:, 1], inverse=True)

        # add plot.ly plotting options
        traces.append(make_scatter(lon_cc, lat_cc, color))
    return traces


def get_coastline_traces(m):
    poly_paths = m.drawcoastlines().get_paths()
    # use only the 91st biggest coastlines (i.e. no rivers)
    N_poly = len(poly_paths)
    return polygons_to_traces(m, poly_paths, N_poly, 'black')

# Function generating coastline lon/lat traces


def get_state_traces(m):
    poly_paths = m.drawstates().get_paths()  # coastline polygon paths
    # use only the 91st biggest coastlines (i.e. no rivers)
    N_poly = len(poly_paths)
    return polygons_to_traces(m, poly_paths, N_poly, 'black')

# Function generating country lon/lat traces


def get_country_traces(m):
    poly_paths = m.drawcountries().get_paths()  # country polygon paths
    N_poly = len(poly_paths)  # use all countries
    return polygons_to_traces(m, poly_paths, N_poly, 'black')


def get_river_traces(m):
    poly_paths = m.drawrivers().get_paths()
    N_poly = len(poly_paths)  # use all countries
    return polygons_to_traces(m, poly_paths, 50, 'blue')
