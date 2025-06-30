# -*- coding: utf-8 -*-
"""
Created on Tue Jun 24 14:29:59 2025
@author: GavagninM
-- Converted to Flask App --
"""

import plotly
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import json
from flask import Flask, render_template, request, jsonify
import os

# --- DATENLADUNG UND -VERARBEITUNG (mit relativen Pfaden) ---

# Annahme: Die Datendateien liegen im selben Ordner wie app.py
excel_path = 'Articles_collection_elab.xlsx'
json_path = 'connections.json'

# Überprüfen, ob die Dateien existieren, um verständliche Fehlermeldungen zu geben
if not os.path.exists(excel_path) or not os.path.exists(json_path):
    print(f"Fehler: Eine oder beide Datendateien nicht gefunden.")
    print(f"Stelle sicher, dass '{excel_path}' und '{json_path}' im selben Verzeichnis wie app.py liegen.")
    exit()

df = pd.read_excel(excel_path, sheet_name='for_python', usecols="A:D", engine='openpyxl')
df_cleaned = df.dropna()

trends_horizons = {row[0]: (row[1], row[2]) for row in df_cleaned.itertuples(index=False, name=None)}
trend_summaries = {row[0]: row[3] for row in df_cleaned.itertuples(index=False, name=None)}

with open(json_path, 'r', encoding='utf-8') as f:
    connections = json.load(f)


# --- KONSTANTEN UND HELFERFUNKTIONEN (unverändert) ---

MAX_HORIZON = 300
BASE_COLOR = 'blue'
HIGHLIGHT_COLOR = 'orange'
horizon_to_distance = {i: i / MAX_HORIZON for i in range(0, MAX_HORIZON + 300)}

def wrap_text(text, max_length=15):
    words = text.split()
    lines, line = [], ""
    for word in words:
        if len(line + word) <= max_length:
            line += word + " "
        else:
            lines.append(line.strip())
            line = word + " "
    lines.append(line.strip())
    return "<br>".join(lines)

# --- FUNKTION ZUM ERSTELLEN DER GRAFIK (unverändert) ---

def create_radar_figure(selected_trend=None):
    base_fig = go.Figure()
    n_trends = len(trends_horizons)
    angles = np.linspace(0, 2 * np.pi, n_trends, endpoint=False)
    trend_positions = {}

    # Radial grid lines
    for i in [100, 200, 300]:
        base_fig.add_trace(go.Scatterpolar(
            r=[horizon_to_distance[i]] * 100,
            theta=np.linspace(0, 360, 100),
            mode='lines',
            line=dict(color='gray', width=1),
            hoverinfo='skip',
        ))

    # Horizon labels
    for label, r_val in zip(["H1", "H2", "H3"], [80, 180, 280]):
        base_fig.add_trace(go.Scatterpolar(
            r=[horizon_to_distance[r_val]],
            theta=[0],
            mode='text',
            text=[label],
            textfont=dict(size=12, color='black'),
            showlegend=False,
            hoverinfo='skip',
        ))

    # Trend points
    for i, (trend, (horizon, size)) in enumerate(trends_horizons.items()):
        radius = horizon_to_distance.get(horizon, 10)
        angle_deg = np.degrees(angles[i])
        label_radius = 1.0 if i % 2 == 0 else 0.80
        trend_positions[trend] = (radius, angle_deg)

        base_fig.add_trace(go.Scatterpolar(
            r=[label_radius, radius], theta=[angle_deg, angle_deg], mode='lines',
            line=dict(color='gray', dash='dot', width=1), hoverinfo='skip', showlegend=False
        ))
        base_fig.add_trace(go.Scatterpolar(
            r=[label_radius], theta=[angle_deg], mode='text', text=[wrap_text(trend)],
            textfont=dict(size=10), showlegend=False, hoverinfo='skip'
        ))

        # Marker-Farbe basierend auf der Auswahl anpassen
        marker_color = HIGHLIGHT_COLOR if trend == selected_trend else BASE_COLOR
        base_fig.add_trace(go.Scatterpolar(
            r=[radius], theta=[angle_deg], mode='markers',
            marker=dict(size=size * 4 + 4, color=marker_color),
            name=trend,
            hovertemplate=f"{wrap_text(trend_summaries.get(trend, ''), 50)}<extra></extra>",
            customdata=[trend]
        ))

    # Verbindungslinien hinzufügen, wenn ein Trend ausgewählt ist
    if selected_trend:
        for conn in connections:
            if conn['source'] == selected_trend or conn['target'] == selected_trend:
                if conn['source'] in trend_positions and conn['target'] in trend_positions:
                    r1, theta1 = trend_positions[conn['source']]
                    r2, theta2 = trend_positions[conn['target']]
                    base_fig.add_trace(go.Scatterpolar(
                        r=[r1, r2], theta=[theta1, theta2], mode='lines',
                        line=dict(color='red', width=max(1, conn['weight'] / 20)),
                        hoverinfo='skip', showlegend=False
                    ))

    base_fig.update_layout(
        polar=dict(radialaxis=dict(visible=False, range=[0, 1]), angularaxis=dict(visible=False)),
        showlegend=False,
        title=dict(text="HAWE Trends Radar - Click a Trend to Show Connections", font=dict(size=14)),
        height=800,
        margin=dict(l=50, r=50, t=80, b=50)
    )

    return base_fig


# --- FLASK ANWENDUNG (unverändert) ---
app = Flask(__name__)

@app.route('/')
def index():
    fig = create_radar_figure()
    graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return render_template('index.html', graph_json=graph_json)

@app.route('/update_chart', methods=['POST'])
def update_chart():
    data = request.get_json()
    clicked_trend = data.get('trend')
    fig = create_radar_figure(selected_trend=clicked_trend)
    return jsonify(json.loads(json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)))

if __name__ == '__main__':
    app.run(debug=True)
