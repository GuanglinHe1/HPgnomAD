# -*- coding: utf-8 -*-
import dash
from dash import dcc, html, Input, Output, State, callback
import dash_bootstrap_components as dbc
import base64
import os
from dash.exceptions import PreventUpdate

# Base directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMP_DIR = os.path.join(BASE_DIR, "temp")

# Register the reference panel page
dash.register_page(
    __name__,
    path="/reference-panel",
    name="Reference Panel"
)

# Reference Panel layout
layout = dbc.Container([
    # Page title
    html.H1("Reference Panel", className="my-4 text-center"),
    
    # Introduction section
    dbc.Row([
        html.Div([
            # Image
            html.Div(
                html.Img(
                    src="https://picturerealm.oss-cn-chengdu.aliyuncs.com/obsidian/dna-8895875.png",
                    style={"height": "200px", "maxHeight": "300px", "width": "450px", "objectFit": "contain"}
                ),
                className="col-md-4 d-flex align-items-center justify-content-center px-4",
                style={"minHeight": "250px"}
            ),
            # Markdown description
            html.Div(
                dcc.Markdown(
                    '''
                    ## What is a reference panel?
                    
                    A reference panel is a curated collection of genomic variants from a diverse set of individuals or strains, 
                    serving as a foundation for comparative genomic analyses. In the context of *Helicobacter pylori* research, 
                    our reference panel contains high-quality SNP data from thousands of *H. pylori* strains collected globally. 
                    
                    This reference panel enables researchers to:
                    - Compare their own *H. pylori* genomic data against a comprehensive database
                    - Identify population-specific variants and evolutionary relationships
                    - Perform imputation analysis to fill in missing genotype information
                    - Conduct genome-wide association studies (GWAS) with enhanced statistical power
                    - Trace the geographic origins and migration patterns of *H. pylori* strains
                    
                    Our panel includes strains from diverse geographic regions and populations, providing 
                    resolution for understanding *H. pylori* genetic diversity and evolution.
                    ''',
                    className="mb-3",
                    style={
                        "fontSize": "1.1rem",
                        "lineHeight": "1.6",
                        "textAlign": "justify",
                        "textJustify": "inter-word"
                    }
                ),
                className="col-md-8 d-flex align-items-center"
            ),
        ], className="row mb-4 px-4 d-flex align-items-center justify-content-center", style={"maxWidth": "1200px", "margin": "0 auto"}),
    ]),
    
    # Buttons
    dbc.Row([
        dbc.Col([
            dbc.Button(
                "Upload Your VCF File",
                id="upload-btn",
                style={"backgroundColor": "#005EA5", "borderColor": "#005EA5"},
                size="lg",
                className="mx-2 mb-3"
            ),
        ], width=6, className="text-center"),
        dbc.Col([
            html.A(
                dbc.Button(
                    "Download Reference Panel",
                    style={"backgroundColor": "#005EA5", "borderColor": "#005EA5"},
                    size="lg",
                    className="mx-2 mb-3"
                ),
                href="https://s1-software.oss-cn-chengdu.aliyuncs.com/Reference_Panel.zip",
                target="_blank"
            ),
        ], width=6, className="text-center"),
    ], justify="center", className="mb-4"),
    
    # Hidden upload area
    dcc.Upload(
        id='upload-vcf',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select VCF Files', style={'color': '#005EA5', 'textDecoration': 'underline'})
        ]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '2px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'borderColor': '#005EA5',
            'textAlign': 'center',
            'margin': '10px 0',
            'backgroundColor': '#f8f9fa',
            'display': 'none'  # Hidden by default
        },
        multiple=False,
        accept='.vcf,.vcf.gz'
    ),
    
    # Upload status
    html.Div(id='upload-status'),
    
    # Hidden download links
    html.Div(id='download-links', style={'display': 'none'}),
    
    # Download components
    dcc.Download(id="download-file1"),
    dcc.Download(id="download-file2"),
    
], fluid=True, className="py-3")

# Toggle upload area when button is clicked
@callback(
    Output('upload-vcf', 'style'),
    Input('upload-btn', 'n_clicks'),
    State('upload-vcf', 'style')
)
def toggle_upload_area(n_clicks, current_style):
    if n_clicks and n_clicks > 0:
        # Reveal upload box
        current_style['display'] = 'block'
        return current_style
    return current_style

# Handle file uploads
@callback(
    Output('upload-status', 'children'),
    Input('upload-vcf', 'contents'),
    State('upload-vcf', 'filename'),
    State('upload-vcf', 'last_modified')
)
def update_upload_status(contents, filename, last_modified):
    if contents is None:
        return ""
    
    # Restrict by file extension
    if not (filename.endswith('.vcf') or filename.endswith('.vcf.gz')):
        return dbc.Alert(
            "Error: Please upload files with .vcf or .vcf.gz extension only.",
            color="danger",
            className="mt-3"
        )
    
    # Decode content
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    
    # Enforce a 20 MB file size limit
    if len(decoded) > 20 * 1024 * 1024:  # 20 MB in bytes
        return dbc.Alert(
            "Error: File size exceeds 20MB limit. Please upload a smaller file.",
            color="danger",
            className="mt-3"
        )
    
    # Persist uploaded file under the project
    os.makedirs(TEMP_DIR, exist_ok=True)
    file_path = os.path.join(TEMP_DIR, filename)
    
    try:
        with open(file_path, 'wb') as f:
            f.write(decoded)
        
        return dbc.Alert(
            f"Success: '{filename}' uploaded successfully! File saved to the local temp directory.",
            color="success",
            className="mt-3"
        )
    except Exception as e:
        return dbc.Alert(
            f"Error: Failed to save file. {str(e)}",
            color="danger",
            className="mt-3"
        )

