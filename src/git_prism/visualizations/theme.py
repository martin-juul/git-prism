"""Color theme for git-prism visualizations.

This module defines all colors in one place. Both CSS templates and
Plotly charts reference these values for consistency.
"""

# Background colors
BG_PRIMARY = "#0f172a"
BG_SECONDARY = "#1e293b"
BG_TERTIARY = "#334155"

# Text colors
TEXT_PRIMARY = "#f1f5f9"
TEXT_SECONDARY = "#cbd5e1"
TEXT_MUTED = "#94a3b8"

# Accent colors
ACCENT_PRIMARY = "#818cf8"      # Indigo
ACCENT_SECONDARY = "#34d399"    # Green
ACCENT_WARNING = "#fbbf24"      # Amber
ACCENT_DANGER = "#f87171"       # Red

# UI colors
BORDER_COLOR = "#475569"
GRID_COLOR = "rgba(71, 85, 105, 0.5)"

# Chart color palette (for multiple series)
CHART_PALETTE = [
    "#818cf8",  # Indigo
    "#34d399",  # Green
    "#fbbf24",  # Amber
    "#f87171",  # Red
    "#a78bfa",  # Purple
    "#f472b6",  # Pink
    "#2dd4bf",  # Teal
    "#fb923c",  # Orange
]

# Plotly dark theme layout
PLOTLY_DARK_LAYOUT = {
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor": "rgba(51, 65, 85, 0.5)",
    "font": {"family": "system-ui, sans-serif", "color": TEXT_PRIMARY},
    "title_font_color": TEXT_PRIMARY,
    "xaxis": {
        "gridcolor": GRID_COLOR,
        "linecolor": BORDER_COLOR,
        "tickfont": {"color": TEXT_SECONDARY},
    },
    "yaxis": {
        "gridcolor": GRID_COLOR,
        "linecolor": BORDER_COLOR,
        "tickfont": {"color": TEXT_SECONDARY},
    },
    "legend": {"font": {"color": TEXT_SECONDARY}},
}
