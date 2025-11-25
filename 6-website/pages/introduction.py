# -*- coding: utf-8 -*-
import dash
from dash import dcc, html
import dash_bootstrap_components as dbc

# Register the introduction page
dash.register_page(
    __name__,
    path="/introduction",
    name="Introduction"
)

# Helicobacter pylori overview
layout = dbc.Container([
    # Page heading
    html.H1([
        "Introduction to ",
        html.Em("Helicobacter pylori")
    ], className="my-4 text-center"),
    
    # Overview section
    dbc.Row([
        dbc.Col([
            html.Div([
                html.H3([
                    "What is ",
                    html.A(
                        html.Em('Helicobacter pylori'),
                        href="https://en.wikipedia.org/wiki/Helicobacter_pylori",
                        target="_blank"
                    ),
                    "?"
                ], className="mb-3"),
                html.P([
                    html.A(
                        html.Em("Helicobacter pylori (H. pylori)"),
                        href="https://en.wikipedia.org/wiki/Helicobacter_pylori",
                        target="_blank"
                    ),
                    " is a gram-negative, microaerophilic, spiral-shaped bacterium that colonizes the human stomach.",
                    " It was first identified in 1982 by Australian scientists ",
                    html.A("Barry Marshall", href="https://en.wikipedia.org/wiki/Barry_Marshall", target="_blank"),
                    " and ",
                    html.A("Robin Warren", href="https://en.wikipedia.org/wiki/Robin_Warren", target="_blank"),
                    ", who discovered that it was present in patients with chronic gastritis and gastric ulcers, ",
                    "conditions that were not previously believed to have a microbial cause. Their discovery revolutionized our understanding of gastric diseases."
                ]),
                
                dbc.Card(
                    dbc.CardBody([
                        html.H5("Key Facts", className="card-title"),
                        html.Ul([
                            html.Li([
                                html.Em("H. pylori"),
                                " infects approximately 50% of the world's population"
                            ]),
                            html.Li("Infection rates vary significantly between countries and populations"),
                            html.Li("It is usually acquired in childhood and can persist for life if not treated"),
                            html.Li("Most infected individuals remain asymptomatic"),
                            html.Li([
                                "It is the strongest known risk factor for ",
                                html.A("gastric cancer", href="https://www.cancer.gov/types/stomach/hp/stomach-treatment-pdq", target="_blank")
                            ])
                        ])
                    ]),
                    className="mb-4"
                ),
            ], className="mb-4")
        ], width=12)
    ]),
    
    # H. pylori and disease
    dbc.Row([
        dbc.Col([
            html.H3([html.Em("H. pylori"), " and Disease"], className="mb-3"),
            html.P([
                html.Em("H. pylori"), " is strongly associated with various gastric pathologies including:"
            ]),
            dbc.Row([
                dbc.Col([
                    dbc.Card(
                        dbc.CardBody([
                            html.H5("Chronic Gastritis", className="card-title"),
                            html.P("Inflammation of the stomach lining that can persist for years")
                        ])
                    ),
                ], width=4),
                dbc.Col([
                    dbc.Card(
                        dbc.CardBody([
                            html.H5("Peptic Ulcer Disease", className="card-title"),
                            html.P("Sores that develop in the lining of the stomach or duodenum")
                        ])
                    ),
                ], width=4),
                dbc.Col([
                    dbc.Card(
                        dbc.CardBody([
                            html.H5("Gastric Cancer", className="card-title"),
                            html.P([html.Em("H. pylori"), " is classified as a Class I carcinogen by WHO"])
                        ])
                    ),
                ], width=4),
            ], className="mb-4"),
        ], width=12)
    ]),
    
    # H. pylori genomic features
    dbc.Row([
        dbc.Col([
            html.H3("Genomic Features", className="mb-3"),
            html.P([
                html.Em("H. pylori"), " exhibits remarkable genetic diversity, with significant differences between strains isolated from different geographic regions. ",
                "This genetic variability contributes to differences in virulence and antibiotic resistance patterns."
            ]),
            html.Div([
                html.H5("Key Genomic Characteristics:"),
                html.Ul([
                    html.Li("Genome size: ~1.6-1.7 Mb"),
                    html.Li("Extremely high mutation and recombination rates"),
                    html.Li("Significant variation in gene content between strains"),
                    html.Li("Contains numerous virulence factors (e.g., CagA, VacA, BabA)"),
                    html.Li("Possesses mechanisms to evade host immune responses")
                ])
            ], className="mb-4"),
        ], width=12)
    ]),
    
    # H. pylori geographic distribution
    dbc.Row([
        dbc.Col([
            html.H3("Geographic Distribution", className="mb-3"),
            html.P([
                html.Em("H. pylori"), " prevalence varies significantly across different regions of the world. ",
                "The bacterium's genetic diversity also shows strong geographic structure, suggesting ancient co-evolution with human populations. ",
                "This makes ", html.Em("H. pylori"), " a valuable tool for tracing human migrations throughout history."
            ]),
            html.Div([
                html.H5("Prevalence by Region:"),
                html.Ul([
                    html.Li("Africa: 70-90%"),
                    html.Li("South America: 70-80%"),
                    html.Li("Asia: 50-80%"),
                    html.Li("Europe: 30-50%"),
                    html.Li("North America: 20-40%"),
                    html.Li("Australia: 15-30%")
                ])
            ])
        ], width=12)
    ]),
    
    # Research tools
    dbc.Row([
        dbc.Col([
            html.H3("Research and Analysis Tools", className="mb-4 mt-4"),
            html.P([
                "Modern genomic approaches have revolutionized ", html.Em("H. pylori"), " research, enabling detailed analyses of strain diversity, virulence, and transmission patterns. ",
                "Our ", html.Em("H. pylori"), " SNP Query Portal allows researchers to explore specific genetic variations across different populations and geographic regions."
            ]),
            dbc.Button(
                "Go to Query Portal",
                href="/query",
                color="primary",
                className="mt-3"
            )
        ], width=12, className="mb-5")
    ]),
    
    # References
    dbc.Row([
        dbc.Col([
            html.Hr(),
            html.H5("References", className="mt-3"),
            html.Ol([
                html.Li("Lintao L et al. Fine-scale global population structure of Helicobacter pylori and distinct high-altitude adaptations on the Tibetan Plateau inferred from evolutionary analysis of large-scale genomic datasets. XXXX. 2025"),
                html.Li("Marshall BJ, Warren JR. Unidentified curved bacilli in the stomach of patients with gastritis and peptic ulceration. Lancet. 1984"),
                html.Li(["Hooi JKY, et al. Global Prevalence of ", html.Em("Helicobacter pylori"), " Infection: Systematic Review and Meta-Analysis. Gastroenterology. 2017"]),
                html.Li(["Salama NR, et al. Life in the human stomach: persistence strategies of the bacterial pathogen ", html.Em("Helicobacter pylori"), ". Nat Rev Microbiol. 2013"]),
                html.Li(["Thorell K, et al. Rapid evolution of distinct ", html.Em("Helicobacter pylori"), " subpopulations in the Americas. PLoS Genet. 2017"])
            ])
        ], width=12)
    ])
    
], fluid=True, className="py-3")
