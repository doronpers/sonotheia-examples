import json
import os
import tempfile
import webbrowser

import pandas as pd  # type: ignore
import plotly.graph_objects as go  # type: ignore
from plotly.subplots import make_subplots  # type: ignore


def create_dashboard(audit_file: str, output_html: str | None = None):
    """Create a Plotly dashboard from a JSONL audit file."""
    # Load audit data
    records = []
    with open(audit_file) as f:
        for line in f:
            records.append(json.loads(line))

    df = pd.DataFrame(records)

    # Flatten indicators and deferral
    indicators_df = pd.json_normalize(df["indicators"])
    deferral_df = pd.json_normalize(df["deferral"])

    # Combine
    plot_df = pd.concat(
        [df.drop(["indicators", "deferral"], axis=1), indicators_df, deferral_df],
        axis=1,
    )

    # Simple labels for slices
    plot_df["slice_label"] = (
        plot_df["slice_index"].astype(str) + " (" + plot_df["slice_start_s"].astype(str) + "s)"
    )

    # Subplots: 2 rows, 2 columns
    fig = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=(
            "Deferral Action Distribution",
            "Fragility Score by Slice",
            "Indicator Values across Perturbations",
            "Stability Heatmap",
        ),
        specs=[[{"type": "domain"}, {"type": "xy"}], [{"type": "xy"}, {"type": "xy"}]],
    )

    # 1. Deferral Distribution (Pie)
    action_counts = plot_df.groupby("recommended_action").size().reset_index(name="counts")
    fig.add_trace(
        go.Pie(
            labels=action_counts["recommended_action"],
            values=action_counts["counts"],
            hole=0.3,
        ),
        row=1,
        col=1,
    )

    # 2. Fragility Score by Slice (Bar)
    # Get one record per slice (fragility is the same across perturbations for a slice)
    fragility_df = plot_df.drop_duplicates(subset=["slice_index"])
    fig.add_trace(
        go.Bar(
            x=fragility_df["slice_label"],
            y=fragility_df["fragility_score"],
            marker_color=fragility_df["recommended_action"].map(
                {
                    "accept": "green",
                    "defer_to_review": "orange",
                    "insufficient_evidence": "red",
                }
            ),
        ),
        row=1,
        col=2,
    )

    # 3. Indicator Values (Line/Markers)
    # Filter for a few key indicators
    key_indicators = [c for c in indicators_df.columns if "mean" in c][:3]
    for ind in key_indicators:
        fig.add_trace(
            go.Scatter(
                x=plot_df["perturbation_name"],
                y=plot_df[ind],
                mode="lines+markers",
                name=ind,
            ),
            row=2,
            col=1,
        )

    # 4. Stability Heatmap (Indicator Variance)
    # Normalize indicators for heatmap comparison
    norm_indicators = indicators_df.div(indicators_df.max())
    fig.add_trace(
        go.Heatmap(
            z=norm_indicators.values.T,
            x=plot_df["perturbation_name"],
            y=norm_indicators.columns,
            colorscale="Viridis",
        ),
        row=2,
        col=2,
    )

    fig.update_layout(
        height=900,
        width=1200,
        title_text=f"Audio Trust Audit: {plot_df['input_file'].iloc[0]}",
        showlegend=True,
    )

    if output_html:
        fig.write_html(output_html)
        print(f"Dashboard saved to {output_html}")
    else:
        # Show in browser
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as tmp:
            fig.write_html(tmp.name)
            webbrowser.open("file://" + os.path.realpath(tmp.name))


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        create_dashboard(sys.argv[1])
