# app.py
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, page_container

app = dash.Dash(
    __name__,
    # Use vanilla Bootstrap theme (light)
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    use_pages=True,
    suppress_callback_exceptions=True,
)
server = app.server

# Primary navigation
nav = dbc.Nav(
    [
        dbc.NavLink(
            page["name"],
            href=page["path"],
            active="exact",
            className="nav-link-custom"  # Apply custom style
        )
        for _, page in dash.page_registry.items()
    ],
    className="navbar-custom",  # Style wrapper for nav
)

app.layout = dbc.Container(
    [
        html.Header(
            [
                html.H1("HPgnomAD", className="site-title"),
                nav,
            ],
            className="header-container",  # Styled header wrapper
        ),
        html.Main(
            page_container,
            className="main-container",  # Styled main content area
        ),
        html.Footer(
            [
                html.A(
                    "Sichuan ICP No. 2025140770-2",
                    href="https://beian.miit.gov.cn/",
                    target="_blank",
                    style={"color": "#888", "textDecoration": "none", "marginRight": "12px", "fontSize": "0.95em"}
                ),
                html.A(
                    "© 2025 Chongqing Medical University, All rights reserved.",
                    href="https://www.cqmu.edu.cn/",
                    target="_blank",
                    style={"color": "#888", "textDecoration": "none", "fontSize": "0.95em"}
                )
            ],
            className="footer-container",
        ),
    ],
    fluid=True,
)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050)
