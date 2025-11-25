# pages/query.py

import os
import subprocess
import tempfile
import shutil
import pandas as pd
import plotly.io as pio
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dash import dcc, html, Input, Output, callback, callback_context
import dash_bootstrap_components as dbc
import dash
import io
import base64
import zipfile

# Register as a Dash Pages subpage
dash.register_page(
    __name__,
    path="/query",
    name="The SNP Query Portal",
)

# ─── Global configuration ───────────────────────────────────────────────────
pio.templates.default = "plotly_white"
# Project root paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT   = os.path.join(BASE_DIR, "query.sh")
CONF_DIR = os.path.join(BASE_DIR, "conf")

BASE_COLOR_MAP = {
    'A':'#0072B2','T':'#009E73',
    'G':'#F5C710','C':'#D55E00'
}

# ─── Analysis orchestration ─────────────────────────────────────────────────
def run_analysis(pos: int, outdir: str):
    """Invoke query.sh and send outputs to outdir."""
    subprocess.run(["bash", SCRIPT, str(pos), outdir], check=True, cwd=BASE_DIR)

def load_tables(outdir: str):
    """Read TSV and META files from outdir and return a dictionary."""
    tbl = {}
    tbl['chromo']    = pd.read_csv(os.path.join(outdir, "base_by_chromopainter4.tsv"), sep="\t")
    tbl['main']      = pd.read_csv(os.path.join(outdir, "base_by_main_population.tsv"), sep="\t")
    tbl['country']   = pd.read_csv(os.path.join(outdir, "base_by_chromopainter4_country.tsv"), sep="\t")
    tbl['continent'] = pd.read_csv(os.path.join(outdir, "base_by_main_population_continent.tsv"), sep="\t")
    tbl['allele']    = pd.read_csv(os.path.join(outdir, "allele_table.tsv"), sep="\t", names=["ID","Allele"])
    tbl['meta']      = pd.read_csv(os.path.join(CONF_DIR, "META_revised.csv"))
    return tbl

def get_annotation(pos: int):
    """Find annotation matching a genomic position."""
    annotation_file = os.path.join(CONF_DIR, "Annotation.csv")
    try:
        df_annotation = pd.read_csv(annotation_file)
        # Identify annotation intervals covering the position
        match = df_annotation[(df_annotation['Start'] <= pos) & (df_annotation['End'] >= pos)]
        if not match.empty:
            # Use the first matching annotation
            annotation = match.iloc[0]
            return f"Type: {annotation['Type']}, Annotation: {annotation['Attributes']}"
        else:
            return "No annotation found for this position."
    except Exception as e:
        return f"Error reading annotation: {str(e)}"

# ─── Plot builders ──────────────────────────────────────────────────────────
def fig_sub_vs_main(tbl):
    df_c, df_m = tbl['chromo'], tbl['main']
    bases = [c.replace("count_","") for c in df_c.columns if c.startswith("count_")]
    fig = make_subplots(rows=2, cols=2,
        subplot_titles=("Base count by sub population","Base count by main population",
                        "Base frequency by sub population","Base frequency by main population"),
        horizontal_spacing=0.1, vertical_spacing=0.25)
    for base in bases:
        fig.add_trace(go.Bar(x=df_c["Chromopainter4"], y=df_c[f"count_{base}"],
                             name=base, marker_color=BASE_COLOR_MAP[base], showlegend=True),
                      row=1, col=1)
        fig.add_trace(go.Bar(x=df_m["Main_Population"], y=df_m[f"count_{base}"],
                             name=base, marker_color=BASE_COLOR_MAP[base], showlegend=False),
                      row=1, col=2)
        fig.add_trace(go.Bar(x=df_c["Chromopainter4"], y=df_c[f"freq_{base}"],
                             name=base, marker_color=BASE_COLOR_MAP[base], showlegend=False),
                      row=2, col=1)
        fig.add_trace(go.Bar(x=df_m["Main_Population"], y=df_m[f"freq_{base}"],
                             name=base, marker_color=BASE_COLOR_MAP[base], showlegend=False),
                      row=2, col=2)
    fig.update_layout(height=900, width=1200, barmode="stack",
                      font=dict(family="Arial", size=12),
                      legend_title_text="Base",
                      margin=dict(t=80,b=50,l=100,r=100),  # Extra margin keeps plots centered
                      autosize=False,
                      template="plotly_white")
    for title,r,c in [("Sub population",1,1),("Main population",1,2),
                      ("Sub population",2,1),("Main population",2,2)]:
        fig.update_xaxes(title_text=title, row=r, col=c, tickangle=45)
    fig.update_yaxes(title_text="Count", row=1, col=1)
    fig.update_yaxes(title_text="Count", row=1, col=2)
    fig.update_yaxes(title_text="Frequency", row=2, col=1)
    fig.update_yaxes(title_text="Frequency", row=2, col=2)
    return fig

def fig_country_vs_continent(tbl):
    df_c, df_ct = tbl['country'], tbl['continent']
    bases = [c.replace("count_","") for c in df_c.columns if c.startswith("count_")]
    fig = make_subplots(rows=2, cols=2,
        subplot_titles=("Base count by country","Base count by continent",
                        "Base frequency by country","Base frequency by continent"),
        horizontal_spacing=0.1, vertical_spacing=0.25)
    for base in bases:
        fig.add_trace(go.Bar(x=df_c["Country"], y=df_c[f"count_{base}"],
                             name=base, marker_color=BASE_COLOR_MAP[base], showlegend=True),
                      row=1, col=1)
        fig.add_trace(go.Bar(x=df_ct["Continent"], y=df_ct[f"count_{base}"],
                             name=base, marker_color=BASE_COLOR_MAP[base], showlegend=False),
                      row=1, col=2)
        fig.add_trace(go.Bar(x=df_c["Country"], y=df_c[f"freq_{base}"],
                             name=base, marker_color=BASE_COLOR_MAP[base], showlegend=False),
                      row=2, col=1)
        fig.add_trace(go.Bar(x=df_ct["Continent"], y=df_ct[f"freq_{base}"],
                             name=base, marker_color=BASE_COLOR_MAP[base], showlegend=False),
                      row=2, col=2)
    fig.update_layout(height=900, width=1200, barmode="stack",
                      font=dict(family="Arial", size=12),
                      legend_title_text="Base",
                      margin=dict(t=80,b=50,l=100,r=100),  # Extra margin keeps plots centered
                      autosize=False,
                      template="plotly_white")
    for r,c in [(1,1),(1,2),(2,1),(2,2)]:
        fig.update_xaxes(title_text=("Country" if c in (1,3) else "Continent"),
                         row=r, col=c, tickangle=45)
    fig.update_yaxes(title_text="Count", row=1, col=1)
    fig.update_yaxes(title_text="Count", row=1, col=2)
    fig.update_yaxes(title_text="Frequency", row=2, col=1)
    fig.update_yaxes(title_text="Frequency", row=2, col=2)
    return fig

def fig_scatter_map(tbl):
    df = (pd.merge(tbl['allele'], tbl['meta'], on="ID")
          .assign(Base=lambda d: d["Allele"].str.split("/").str[0])
          .dropna(subset=["Latitude","Longitude"]))
    df_counts = df.groupby(["Latitude","Longitude","Base"], as_index=False).size().rename(columns={"size":"count"})
    fig = px.scatter_map(df_counts, lat="Latitude", lon="Longitude",
                         color="Base", size="count",
                         color_discrete_map=BASE_COLOR_MAP,
                         hover_data={"count":True},
                         map_style="open-street-map", zoom=1,
                         title="Sample distribution by base",
                         height=800)
    traces = sorted(fig.data,
                    key=lambda tr: max(tr.marker.size
                        if hasattr(tr.marker.size,"__len__") else [tr.marker.size]),
                    reverse=True)
    fig.data = tuple(traces)
    fig.update_layout(margin=dict(r=0,t=30,l=0,b=0),
                      legend_title_text="Base",
                      font=dict(family="Arial", size=12))
    return fig

def fig_density_map(tbl):
    df = (pd.merge(tbl['allele'], tbl['meta'], on="ID")
          .assign(Base=lambda d: d["Allele"].str.split("/").str[0])
          .dropna(subset=["Latitude","Longitude"]))
    df_counts = df.groupby(["Latitude","Longitude","Base"], as_index=False).size().rename(columns={"size":"count"})
    total = df_counts.groupby(["Latitude","Longitude"], as_index=False)["count"].sum().rename(columns={"count":"total"})
    df_counts = pd.merge(df_counts, total, on=["Latitude","Longitude"])
    df_counts["frequency"] = df_counts["count"] / df_counts["total"]
    fig = px.density_map(df_counts, lat="Latitude", lon="Longitude",
                        z="frequency", radius=10, map_style="open-street-map",
                        zoom=1, animation_frame="Base",
                        title="Frequency distribution by base",
                        labels={"frequency":"Frequency"},
                        color_continuous_scale="YlOrRd",
                        height=850)
    fig.update_layout(margin=dict(l=0,r=0,t=30,b=0),
                      font=dict(family="Arial", size=12),
                      coloraxis_colorbar=dict(title="Frequency density"))
    return fig

# ─── Page layout ────────────────────────────────────────────────────────────
layout = dbc.Container([
    html.H2("SNP Query and Visualization", className="mt-4 text-center"),
    dbc.Row(dbc.Col([
        html.Label("Input site of SNP: "),
        dcc.Input(
            id="pos-input",
            type="number",
            className="form-control search-box",
            placeholder="Example: 3408",
            style={"borderColor": "#005EA5", "borderWidth": "2px"}  # Inline blue border
        ),
        html.Br(),
        dbc.Button("Query", id="btn-query", n_clicks=0, color="primary")
    ], width=4), justify="center"),
    html.Hr(),
    dcc.Loading(html.Div(id="tabs-div"), type="circle"),
], fluid=True)

# ─── Callbacks ──────────────────────────────────────────────────────────────
from dash import State  # Import State for callbacks

@callback(
    Output("tabs-div", "children"),
    Input("btn-query", "n_clicks"),  # Trigger only when Query button is pressed
    State("pos-input", "value"),    # Treat input value as State instead of Input
)
def update_tabs(n_clicks, pos):
    # Prevent automatic triggering on initial load
    if n_clicks is None or n_clicks == 0:
        return html.P("Please enter the site and click 'Query'.", className="text-center text-muted")
    
    if pos is None:
        return html.P("Please enter a valid SNP position.", className="text-warning text-center")

    tmpdir = tempfile.mkdtemp(prefix="hpylori_", dir="/tmp")
    try:
        # Run the analysis pipeline
        try:
            run_analysis(int(pos), tmpdir)
        except subprocess.CalledProcessError:
            return html.P("The location you entered is not recorded, please try another SNP query.", className="text-warning text-center")

        # Validate allele_table output
        df_allele = pd.read_csv(os.path.join(tmpdir, "allele_table.tsv"),
                                sep="\t", names=["ID","Allele"])
        if df_allele.empty:
            return html.P("The location you entered is not recorded, please try another SNP query.", className="text-warning text-center")

        # Load tables and build figures
        tbl  = load_tables(tmpdir)
        fig1 = fig_sub_vs_main(tbl)
        fig2 = fig_country_vs_continent(tbl)
        fig3 = fig_scatter_map(tbl)
        fig4 = fig_density_map(tbl)

        # Retrieve annotation text
        annotation_text = get_annotation(int(pos))

        return html.Div([
            dbc.Tabs([
                dbc.Tab(dcc.Graph(figure=fig1), label="Classification"),
                dbc.Tab(dcc.Graph(figure=fig2), label="Geography"),
                dbc.Tab(dcc.Graph(figure=fig3), label="Scatter Map"),
                dbc.Tab(dcc.Graph(figure=fig4), label="Density Map"),
            ]),
            html.Hr(),
            html.P(
                f"Position {pos}; annotation: {annotation_text}",
                className="text-center text-muted",
                style={"fontSize": "12px", "color": "#6c757d", "marginTop": "20px"}
            )
        ])
    
    except Exception as e:
        shutil.rmtree(tmpdir, ignore_errors=True)
        return html.P(f"An error occurred: {str(e)}", className="text-danger text-center")
