# -*- coding: utf-8 -*-
import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc

# Register the homepage
dash.register_page(
    __name__,
    path="/",
    name="Homepage"
)

layout = html.Div(
    className="main-container homepage-bg d-flex flex-column justify-content-center align-items-center",
    style={"minHeight": "80vh", "background": "transparent"},  # Keep background transparent
    children=[
        # Title styled with the shared class
        html.H1("Welcome!", className="site-title mb-4"),

        # Database overview
        html.Div([
            # Illustration
            html.Div(
                html.Img(
                    src="https://picturerealm.oss-cn-chengdu.aliyuncs.com/obsidian/dna-8895875.png",
                    style={"height": "200px", "maxHeight": "300px", "width": "450px", "objectFit": "contain"}
                ),
                className="col-md-4 d-flex align-items-center justify-content-center px-4",
                style={"minHeight": "250px"}
            ),
            # Narrative description
            html.Div(
                dcc.Markdown(
                    '''
                    HpgenomAD is a global whole-genome resource for *Helicobacter pylori* that provides a comprehensive SNP variation atlas. 
                    We integrated publicly available datasets with newly generated genome sequences from *H. pylori* isolates of the Qinghai–Tibet Plateau 
                    to develop an extensive SNP query system. Via the **Query** interface, users enter an SNP position—referenced to strain 
                    [HP26695](https://www.ncbi.nlm.nih.gov/nuccore/NC_000915.1?report=genbank)—and obtain variant counts and allele frequencies 
                    across diverse strain populations, geographical subdivisions and latitudinal gradients.
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
        ], className="row mb-4 px-4 d-flex align-items-center justify-content-center", style={"maxWidth": "1200px"}),

        # Three evenly sized buttons
        html.Div([
            dbc.Button(
                "Introduction",
                id="to-intro",
                style={
                    "backgroundColor": "#005EA5",
                    "borderColor": "#005EA5",
                    "color": "#fff",
                    "width": "180px",
                    "height": "70px",
                    "fontSize": "1.25rem",
                    "fontWeight": "bold",
                    "margin": "0 18px",
                    "borderRadius": "16px",
                    "boxShadow": "0 2px 8px rgba(0,94,165,0.08)",
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "center"
                },
                className="button-square"
            ),
            dbc.Button(
                "Reference Panel",
                id="to-reference-panel",
                style={
                    "backgroundColor": "#005EA5",
                    "borderColor": "#005EA5",
                    "color": "#fff",
                    "width": "180px",
                    "height": "70px",
                    "fontSize": "1.25rem",
                    "fontWeight": "bold",
                    "margin": "0 18px",
                    "borderRadius": "16px",
                    "boxShadow": "0 2px 8px rgba(0,94,165,0.08)",
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "center"
                },
                className="button-square"
            ),
            dbc.Button(
                "SNP Query",
                id="to-query",
                style={
                    "backgroundColor": "#005EA5",
                    "borderColor": "#005EA5",
                    "color": "#fff",
                    "width": "180px",
                    "height": "70px",
                    "fontSize": "1.25rem",
                    "fontWeight": "bold",
                    "margin": "0 18px",
                    "borderRadius": "16px",
                    "boxShadow": "0 2px 8px rgba(0,94,165,0.08)",
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "center"
                },
                className="button-square"
            ),
        ], style={
            "display": "flex",
            "flexDirection": "row",
            "justifyContent": "center",
            "alignItems": "center",
            "marginBottom": "32px"
        }),

        # Highlighted stats
        html.Div([
            # Numeric values
            dbc.Row([
                dbc.Col(
                    html.H2("80+", style={"color": "#00BFFF", "fontWeight": "bold", "fontSize": "2.5rem"}),
                    className="text-center px-4", width=4
                ),
                dbc.Col(
                    html.H2("7500+", style={"color": "#0077C2", "fontWeight": "bold", "fontSize": "2.5rem"}),
                    className="text-center px-4", width=4
                ),
                dbc.Col(
                    html.H2("829700+", style={"color": "#00619a", "fontWeight": "bold", "fontSize": "2.5rem"}),
                    className="text-center px-4", width=4
                ),
            ], className="align-items-center justify-content-around", style={"marginBottom": "20px", "padding": "20px 30px 0px 30px"}),
            
            # Captions
            dbc.Row([
                dbc.Col(
                    html.P("Countries", style={"color": "#777", "fontSize": "1rem"}),
                    className="text-center px-4", width=4
                ),
                dbc.Col(
                    html.P("Strains", style={"color": "#777", "fontSize": "1rem"}),
                    className="text-center px-4", width=4
                ),
                dbc.Col(
                    html.P("Core SNP variants", style={"color": "#777", "fontSize": "1rem"}),
                    className="text-center px-4", width=4
                ),
            ], className="align-items-center justify-content-around", style={"padding": "0px 30px 20px 30px"}),
        ], className="mb-4 mt-4 py-4 w-100", style={"maxWidth": "1200px", "width": "90%", "backgroundColor": "#f8f9fa", "borderRadius": "10px", "boxShadow": "0 2px 6px rgba(0,0,0,0.05)"}),

        # Resource prompt
        html.Div(
            "For more resources, please visit the following databases.",
            style={
                "backgroundColor": "#e6f2fb",
                "color": "#005EA5",
                "fontWeight": "bold",
                "fontSize": "1.1rem",
                "borderRadius": "8px",
                "padding": "18px 24px",
                "margin": "0 auto 32px auto",
                "maxWidth": "900px",
                "textAlign": "center",
                "boxShadow": "0 1px 4px rgba(0,94,165,0.06)"
            }
        ),

        # Resource cards
        html.Div([
            html.Div([
                html.A([
                    html.Div("NCBI", style={"fontSize": "2.5rem", "fontWeight": "bold", "color": "#00619a", "height": "auto", "display": "flex", "alignItems": "flex-start", "justifyContent": "flex-start", "width": "100%"}),
                    html.Div(
                        "The National Center for Biotechnology Information is a US government–funded hub that hosts a suite of biomedical and genomic databases accessible through the Entrez search system.",
                        style={"fontSize": "0.95rem", "color": "#888", "marginTop": "18px", "padding": "0 10px", "lineHeight": "1.5", "fontWeight": "normal", "textAlign": "left", "width": "100%", "display": "block"}
                    )
                ],
                    href="https://www.ncbi.nlm.nih.gov/nuccore/?term=h.pylori",
                    target="_blank",
                    style={
                        "display": "flex",
                        "flexDirection": "column",
                        "alignItems": "flex-start",
                        "justifyContent": "flex-start",
                        "backgroundColor": "#e6f2fb",
                        "borderRadius": "14px",
                        "textAlign": "left",
                        "padding": "14px 12px 14px 12px",
                        "margin": "0 16px",
                        "textDecoration": "none",
                        "boxShadow": "0 2px 8px rgba(0,94,165,0.08)",
                        "minWidth": "320px",
                        "minHeight": "60px",
                        "maxWidth": "420px",
                        "transition": "background 0.2s"
                    }
                ),
                html.A([
                    html.Div("Enterobase", style={"fontSize": "2.5rem", "fontWeight": "bold", "color": "#00619a", "height": "auto", "display": "flex", "alignItems": "flex-start", "justifyContent": "flex-start", "width": "100%"}),
                    html.Div(
                        "EnteroBase is a free web-based platform that assembles, analyzes, and visualizes the genomic epidemiology of enteric bacteria across hundreds of thousands of genomes.",
                        style={"fontSize": "0.95rem", "color": "#888", "marginTop": "18px", "padding": "0 10px", "lineHeight": "1.5", "fontWeight": "normal", "textAlign": "left", "width": "100%", "display": "block"}
                    )
                ],
                    href="https://enterobase.warwick.ac.uk/species/helicobacter/search_strains?query=workspace:108555",
                    target="_blank",
                    style={
                        "display": "flex",
                        "flexDirection": "column",
                        "alignItems": "flex-start",
                        "justifyContent": "flex-start",
                        "backgroundColor": "#e6f2fb",
                        "borderRadius": "14px",
                        "textAlign": "left",
                        "padding": "14px 12px 14px 12px",
                        "margin": "0 16px",
                        "textDecoration": "none",
                        "boxShadow": "0 2px 8px rgba(0,94,165,0.08)",
                        "minWidth": "320px",
                        "minHeight": "60px",
                        "maxWidth": "420px",
                        "transition": "background 0.2s"
                    }
                ),
                html.A([
                    html.Div("PubMLST", style={"fontSize": "2.5rem", "fontWeight": "bold", "color": "#00619a", "height": "auto", "display": "flex", "alignItems": "flex-start", "justifyContent": "flex-start", "width": "100%"}),
                    html.Div(
                        "PubMLST is an open-access, curated collection of BIGSdb-powered databases integrating multilocus sequence typing, genome assemblies, and phenotype/provenance metadata for microbial species.",
                        style={"fontSize": "0.95rem", "color": "#888", "marginTop": "18px", "padding": "0 10px", "lineHeight": "1.5", "fontWeight": "normal", "textAlign": "left", "width": "100%", "display": "block"}
                    )
                ],
                    href="https://pubmlst.org/organisms/helicobacter-pylori",
                    target="_blank",
                    style={
                        "display": "flex",
                        "flexDirection": "column",
                        "alignItems": "flex-start",
                        "justifyContent": "flex-start",
                        "backgroundColor": "#e6f2fb",
                        "borderRadius": "14px",
                        "textAlign": "left",
                        "padding": "14px 12px 14px 12px",
                        "margin": "0 16px",
                        "textDecoration": "none",
                        "boxShadow": "0 2px 8px rgba(0,94,165,0.08)",
                        "minWidth": "320px",
                        "minHeight": "60px",
                        "maxWidth": "420px",
                        "transition": "background 0.2s"
                    }
                ),
            ], style={
                "display": "flex",
                "flexDirection": "row",
                "justifyContent": "center",
                "alignItems": "stretch",
                "gap": "48px",
                "width": "100%"
            }),
        ], className="mb-4", style={"maxWidth": "1600px", "margin": "0 auto"}),

        # Hidden redirect target
        dcc.Location(id="home-redirect", refresh=True)
    ]
)

@dash.callback(
    Output("home-redirect", "pathname"),
    Input("to-query", "n_clicks"),
    Input("to-intro", "n_clicks"),
    Input("to-reference-panel", "n_clicks")
)
def redirect_to_page(query_clicks, intro_clicks, ref_panel_clicks):
    ctx = dash.callback_context
    
    if not ctx.triggered:
        return dash.no_update
        
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    if button_id == "to-query" and query_clicks and query_clicks > 0:
        return "/query"
    elif button_id == "to-intro" and intro_clicks and intro_clicks > 0:
        return "/introduction"
    elif button_id == "to-reference-panel" and ref_panel_clicks and ref_panel_clicks > 0:
        return "/reference-panel"
        
    return dash.no_update
