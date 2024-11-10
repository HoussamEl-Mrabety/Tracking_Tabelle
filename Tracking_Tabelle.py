"""
Dieser Python-Code verwendet Dash zur Erstellung einer web-basierten Anwendung für das Tracking von Laborprozessen.

Hauptfunktionen:
1. Eingabefelder zur Erfassung von Prozessdaten wie Datum, Uhrzeit, Kommentar, Operator, Status und Operation.
2. Speicherung der erfassten Prozessdaten in einer SQLite-Datenbank.
3. Dynamische Anzeige der gespeicherten Daten in einer Tabelle.
4. Visualisierung der Anzahl der Einträge pro Arbeiter als Balkendiagramm.

Der Code verwendet:
- SQLAlchemy zur Verwaltung der SQLite-Datenbank.
- Dash Bootstrap Components zur Gestaltung der Benutzeroberfläche.
- Plotly Express zur Erstellung des Balkendiagramms.

Die Dash-Anwendung ermöglicht es den Benutzern, neue Prozessdaten hinzuzufügen, die Datenbank zu aktualisieren und die Ergebnisse in Echtzeit anzuzeigen.
"""

import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime
import plotly.express as px  # Bibliothek für Diagramme

# Initialisiere die Datenbankverbindung
engine = create_engine("sqlite:///tracking_data.db")
connection = engine.connect()

# Lösche die Tabelle 'tracking', falls sie existiert, um sicherzustellen, dass eine neue Tabelle erstellt wird
connection.execute(text("DROP TABLE IF EXISTS tracking"))

# Erstelle die Tabelle 'tracking' mit den erforderlichen Spalten
connection.execute(
    text(
        "CREATE TABLE tracking (datum TEXT, prozess TEXT, status TEXT, uhrzeit TEXT, operator TEXT, operation TEXT)"
    )
)


# Funktion zum Laden der Daten aus der Datenbank in ein DataFrame
def load_data():
    return pd.read_sql("SELECT * FROM tracking", connection)


# Initialisiere die Dash-Anwendung
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Definiere das Layout der Anwendung
app.layout = html.Div(
    [
        html.H1("Laborprozess-Tracking"),
        # Eingabeformulare für Datum und Uhrzeit
        dbc.Row(
            [
                dbc.Col(
                    dcc.DatePickerSingle(
                        id="datum",
                        placeholder="Datum auswählen",
                        display_format="DD.MM.YYYY",
                        date=datetime.now().strftime(
                            "%Y-%m-%d"
                        ),  # Setzt das heutige Datum
                        style={"margin-bottom": "10px", "width": "100%"},
                    ),
                    width=6,  # Breite auf 50% der Zeile setzen
                ),
                dbc.Col(
                    dbc.Input(
                        id="uhrzeit",
                        placeholder="Uhrzeit auswählen",
                        type="time",
                        value=datetime.now().strftime(
                            "%H:%M"
                        ),  # Setzt die aktuelle Uhrzeit als Standardwert
                        style={"margin-bottom": "10px", "width": "100%"},
                    ),
                    width=6,  # Breite auf 50% der Zeile setzen
                ),
            ],
            style={"margin-bottom": "10px"},
        ),
        # Eingang für Prozess, Operator, Status und Operation
        dbc.Input(
            id="prozess",
            placeholder="Kommentar eingeben",
            type="text",
            style={"margin-bottom": "10px"},
        ),
        dcc.Dropdown(
            id="Operator",
            options=[
                {"label": "Houssam", "value": "Houssam"},
                {"label": "Alex", "value": "Alex"},
                {"label": "Mo", "value": "Mo"},
                {"label": "Sam", "value": "Sam"},
            ],
            placeholder="Name eingeben",
            style={"margin-bottom": "10px"},
        ),
        dcc.Dropdown(
            id="status",
            options=[
                {"label": "Erledigt", "value": "Erledigt"},
                {"label": "In Bearbeitung", "value": "In Bearbeitung"},
                {"label": "Ausstehend", "value": "Ausstehend"},
            ],
            placeholder="Status auswählen",
            style={"margin-bottom": "10px"},
        ),
        dcc.Dropdown(
            id="Operation",
            options=[
                {"label": "PCR", "value": "PCR"},
                {"label": "Cobas", "value": "Cobas"},
                {"label": "Analyse", "value": "Analyse"},
                {"label": "Probenaufbereitung", "value": "Probenaufbereitung"},
            ],
            placeholder="Operation auswählen",
            style={"margin-bottom": "10px"},
        ),
        # Button, um Eintrag hinzuzufügen
        dbc.Button(
            "Eintrag hinzufügen",
            id="submit",
            n_clicks=0,
            color="primary",
            style={"margin-bottom": "20px"},
        ),
        # Div zur Anzeige der Tabelle
        html.Div(id="table-container"),
        # Div zur Anzeige des Balkendiagramms
        html.Div([dcc.Graph(id="bar-chart")]),
    ]
)


# Callback zum Hinzufügen von Daten zur Datenbank und zur Aktualisierung der Anzeige
@app.callback(
    [Output("table-container", "children"), Output("bar-chart", "figure")],
    [Input("submit", "n_clicks")],
    [
        State("datum", "date"),
        State("uhrzeit", "value"),
        State("Operator", "value"),
        State("Operation", "value"),
        State("status", "value"),
        State("prozess", "value"),
    ],
)
def update_table_and_chart(
    n_clicks, datum, uhrzeit, operator, operation, status, prozess
):
    # Prüfe, ob alle Formularfelder ausgefüllt sind und ein Klick auf den Button erfolgt ist
    if n_clicks > 0:
        try:
            # Daten zur Datenbank hinzufügen
            connection.execute(
                text(
                    "INSERT INTO tracking (datum, prozess, status, uhrzeit, operator, operation) VALUES (:datum, :prozess, :status, :uhrzeit, :operator, :operation)"
                ),
                {
                    "datum": datum,
                    "prozess": prozess,
                    "status": status,
                    "uhrzeit": uhrzeit,
                    "operator": operator,
                    "operation": operation,
                },
            )
        except Exception as e:
            # Fehler abfangen und als Warnung anzeigen
            return dbc.Alert(f"Fehler beim Einfügen der Daten: {e}", color="danger"), {}

    # Daten aus der Datenbank laden
    df = load_data()

    # Erstelle eine Tabelle aus den Daten
    table = dbc.Table.from_dataframe(df, striped=True, bordered=True, hover=True)

    # Erstelle ein Balkendiagramm aus den Daten
    if not df.empty:
        fig = px.bar(
            df,
            x="operator",
            title="Anzahl der Einträge pro Arbeiter",
            labels={"operator": "Arbeiter", "count": "Anzahl der Einträge"},
        )
        fig.update_layout(barmode="group")
    else:
        fig = {}

    # Rückgabe der Tabelle und des Diagramms
    return table, fig


# Starten des Dash-Servers
if __name__ == "__main__":
    app.run_server(
        debug=True, port=8051
    )  # Verwenden Sie 8051 oder einen anderen freien Port

# Verbindung schließen nach Beendigung
connection.close()
