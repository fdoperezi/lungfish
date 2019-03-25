import os, glob, numpy as np, pandas as pd

from functools import partial
from collections import defaultdict
# flask
from flask import Flask
from flask_cors import CORS
# packages for visualization
import pydicom

from PIL import Image
import plotly.graph_objs as go
import plotly.plotly as py
import plotly.tools as tls
from plotly.offline import download_plotlyjs, init_notebook_mode,  iplot, plot
import plotly

# dash

import flask
import dash
import dash_core_components as dcc
from dash.dependencies import Input, Output,State
import dash_table_experiments as dt
import dash_html_components as html
import dash_table
# datatable filtering
import json


#import directories from app.py
# import functions from app.py
from app import app, server, pl_bone, colors,indicator,  df_to_table, histogram_equalization, get_pl_image, DICOM_heatmap



#####################################################################
# A function to read dcm meta data into a dataframe
def read_dcm_meta(image_directory,save_csv_dir):
    image_fps = []
    for (dirpath, dirnames, filenames) in os.walk(image_directory):
        #print(filenames)
        image_fps += [os.path.join(dirpath, file) for file in filenames if file.endswith('.dcm')]
    print(len(image_fps),'.dcm files were found in',image_directory)

    dcms = [pydicom.read_file(x, stop_before_pixels=True) for x in image_fps]

    meta, tag_to_key = zip(*[parse_dcm_metadata(x) for x in dcms])

    df_dcm = pd.DataFrame.from_records(data=meta)
    print(df_dcm.head(1))
    filename= 'df_dcm_' + str(len(image_fps)) + 'dash_sample.csv'
    df_dcm.to_csv(os.path.join(save_csv_dir,filename),index=False)
    return df_dcm

#####################################################################
# 2. directories
# Sample image data
sample_image=('./data/sample_image/')

# Sample meta data
sample_meta=('./data/sample_meta/')
#####################################################################
# 1.1 Read csv data
df1 =pd.read_csv('./data/sample_meta/df_dcm_merge_box_bbcounts_app1000samples_cleaned.csv')
df1['Number'] = range(1, len(df1) + 1)

#####################################################################



layout = [
    # top controls
    html.Div(
        [
        html.H2("Visualization of Registered Medical Images"),
        dcc.Dropdown(
            id='app-1-dropdown',
            options=[
                {'label': 'Select Dataset - {}'.format(i), 'value': i} for i in [
                    'Sample Dataset'
                    ]
                ]
            ),
        ],
        className="row",
        style={'marginBottom': 5, 'marginTop': 50,'fontsize':20},
    ),

    # indicators div
    html.Div(
        [
            indicator(
                "#00cc96",
                html.H4("1000 Samples"),
                "left_image_upload_indicator",
            ),
            indicator(
                "#119DFF",
                html.H4("225 Pneumonia Samples "),
                "middle_image_upload_indicator",
            ),
            indicator(
                "#EF553B",
                html.H4("775 Normal Samples"),
                "right_image_upload_indicator",
            ),
        ],
        className="row",
    ),


        # 2. 2nd row: table
    html.Div(
        style={'backgroundColor': colors['background'],'color': colors['text']},
        children =
        [
            html.H3('Metadata of DICOM Files'),
        # use datatable experiments dt
            dt.DataTable(
            id='dt_interactive',
            # rows
            rows=df1.to_dict('records'),# initialize the rows
            columns=df1.columns,
            row_selectable=True,
            filterable=True,
            sortable=True,
            selected_row_indices=[],
            max_rows_in_viewport=10,
            resizable =True,
            enable_drag_and_drop=True,
            header_row_height=50,
            column_widths=200,
            row_scroll_timeout=1,
            row_update= True,
            editable =True
            ),
            html.H2(''),
            html.H2('Image Visulization of DICOM Files'),
            html.Div(id='selected-indexes',style={'margin-top': 50,'marginBottom': 10}),
            dcc.Graph(id='dt_graph')
        ]
        ),

]


#####################################################################
# 1. Update dt.DataTable rows in a callback
@app.callback(
    Output('dt_interactive', 'selected_row_indices'),
    [Input('dt_graph', 'clickData')],
    [State('dt_interactive', 'selected_row_indices')])
def update_selected_row_indices(clickData, selected_row_indices):
    if clickData:
        for point in clickData['points']:
            if point['pointNumber'] in selected_row_indices:
                selected_row_indices.remove(point['pointNumber'])
            else:
                selected_row_indices.append(point['pointNumber'])
                print('selected_row_indices',selected_row_indices)
    return selected_row_indices

#####################################################################
# 1.2 update dt.graph
@app.callback(
    Output('dt_graph', 'figure'),
    [Input('dt_interactive', 'rows'),
     Input('dt_interactive', 'selected_row_indices')])
def update_figure(rows, selected_row_indices):
    #df1 = pd.DataFrame(rows)
    selected_rows=[rows[i] for i in selected_row_indices]
    #selected_rows=selected_row_indices[-1]
    print(selected_rows)
    print(len(selected_rows))
    newst_row = selected_rows[0]
    print('the new one is',selected_rows[0])
    # limit to one image
    # 1) Select image name
    #image_dcm = [y['image_dcm'] for y in selected_rows]
    newest_image_dcm = newst_row['image_dcm']
    #print('the neweste image_dcm is',newest_image_dcm)
    newset_image_name=''.join(map(str, newest_image_dcm))
    #print('newset_image_name', newset_image_name)
    pl_img=get_pl_image(os.path.join(sample_image,newset_image_name), hist_equal=True, no_bins=36)

    fig=DICOM_heatmap(pl_img, str(newset_image_name))
    #fig3 =py.iplot(fig2, filename='DICOM-MRBRAIN') don't do image show in dash
    # add patches

    return fig

#####################################################################
