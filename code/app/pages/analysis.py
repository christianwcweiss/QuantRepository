import dash
import dash_bootstrap_components as dbc
import pandas as pd
from dash import html, dcc, callback, Input, Output

from components.atoms.content import MainContent
from components.atoms.header import PageHeader
from components.frame.body import PageBody
from db.database import SessionLocal
from models.credential_setting import CredentialSetting
from pages.base_page import BasePage
from quant_core.clients.mt5.mt5_client import Mt5Client
from quant_core.enums.platform import Platform
from quant_core.metrics.account.account_growth_over_time import AccountGrowthAbsoluteOverTime
from quant_core.services.core_logger import CoreLogger

dash.register_page(__name__, path="/analysis", name="Analysis")


class AnalysisPage(BasePage):
    def render(self):
        return PageBody([
            PageHeader("📈 Strategy Analysis"),
            MainContent([
                dbc.Button("Load MT5 Trade History", id="load-analysis-btn", color="primary", className="mb-3"),
                dcc.Loading(html.Div(id="analysis-output"), type="circle")
            ])
        ])


page = AnalysisPage("Strategy Analysis")
layout = page.layout


@callback(
    Output("analysis-output", "children"),
    Input("load-analysis-btn", "n_clicks"),
    prevent_initial_call=True
)
def load_mt5_history(_):
    with SessionLocal() as session:
        credentials = session.query(CredentialSetting).filter_by(
            platform=Platform.METATRADER.value,
            enabled=True
        ).all()

    all_dfs = []
    for cred in credentials:
        try:
            CoreLogger().info(f"🔍 Loading MT5 trades for {cred.uid}...")
            client = Mt5Client(secret_id=cred.secret_name)
            df = client.get_history_df(days=90)
            df["Account"] = cred.friendly_name or cred.uid
            all_dfs.append(df)
            client.shutdown()
        except Exception as e:
            CoreLogger().error(f"❌ Failed to load MT5 data for {cred.uid}: {e}")

    if not all_dfs:
        return dbc.Alert("⚠️ No data found or unable to connect to MT5 accounts.", color="warning")

    merged_df = pd.concat(all_dfs, ignore_index=True)

    fig_balance = AccountGrowthAbsoluteOverTime().to_chart(merged_df)

    return dbc.Container([
        dbc.Row([
            dbc.Col(dcc.Graph(figure=fig_balance), width=12),
            # Future charts can go here in additional dbc.Col()
        ])
    ], fluid=True)
