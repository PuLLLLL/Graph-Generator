import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

st.set_page_config(page_title="Graph Generator", layout="wide")

st.title("📊 Advanced Graph Generator")

file = st.file_uploader("Upload CSV", type=["csv"])

if file:
    df = pd.read_csv(file)

    st.subheader("Preview Data")
    st.dataframe(df)

    all_columns = df.columns.tolist()
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()

    st.sidebar.header("X-Axis Settings")

    x_mode = st.sidebar.radio(
        "X-Axis Type",
        ["Auto Detect", "Single Column", "Separate Date & Time"]
    )

    datetime_col = None

    if x_mode == "Auto Detect":
        if "TestDate" in df.columns and "TestClock" in df.columns:
            try:
                datetime_col = pd.to_datetime(
                    df["TestDate"] + " " + df["TestClock"],
                    errors="coerce"
                )
            except:
                st.warning("Auto detect failed. Try manual format.")

    elif x_mode == "Single Column":
        col = st.sidebar.selectbox("Select X Column", all_columns)
        datetime_col = pd.to_datetime(df[col], errors="coerce")

    elif x_mode == "Separate Date & Time":
        date_col = st.sidebar.selectbox("Date Column", all_columns)
        time_col = st.sidebar.selectbox("Time Column", all_columns)

        fmt = st.sidebar.text_input(
            "Datetime Format (optional)",
            value="%d/%m/%y %H:%M:%S"
        )

        datetime_col = pd.to_datetime(
            df[date_col] + " " + df[time_col],
            format=fmt,
            errors="coerce"
        )

    df["DATETIME"] = datetime_col

    st.sidebar.header("Graph Settings")

    graph_type = st.sidebar.selectbox(
        "Graph Type",
        ["Line", "Scatter", "Bar", "Pie", "Heatmap"]
    )

    axis_mode = st.sidebar.radio(
        "Axis Mode",
        ["Single Y-Axis", "Dual Y-Axis"]
    )

    selected_cols = st.sidebar.multiselect(
        "Select Y Columns",
        numeric_cols
    )

    log_scale = st.sidebar.checkbox("Log Scale (Primary Axis)")

    left_cols = []
    right_cols = []

    if axis_mode == "Dual Y-Axis":
        st.sidebar.subheader("Assign Axis")

        for col in selected_cols:
            axis = st.sidebar.radio(
                f"{col}",
                ["Left", "Right"],
                horizontal=True,
                key=col
            )
            if axis == "Left":
                left_cols.append(col)
            else:
                right_cols.append(col)
    else:
        left_cols = selected_cols

    if graph_type == "Heatmap":
        st.subheader("🔥 Heatmap View")

        if selected_cols:
            fig = px.imshow(
                df[selected_cols].T,
                aspect='auto',
                labels=dict(x="Time Index", y="Sensor", color="Value")
            )
            st.plotly_chart(fig, use_container_width=True)

    elif graph_type == "Pie":
        st.subheader("🍰 Pie Chart View")

        if selected_cols:
            fig = px.pie(
                df,
                names=selected_cols[0],
                values=selected_cols[1] if len(selected_cols) > 1 else None,
                title="Pie Chart"
            )
            st.plotly_chart(fig, use_container_width=True)

    elif graph_type == ["Line", "Scatter", "Bar"]:

        fig = make_subplots(specs=[[{"secondary_y": True}]])

        # --- LEFT AXIS ---
        for col in left_cols:
            if graph_type == "Line":
                fig.add_trace(go.Scatter(x=df["DATETIME"], y=df[col],
                                         mode='lines+markers',
                                         name=col),
                              secondary_y=False)

            elif graph_type == "Scatter":
                fig.add_trace(go.Scatter(x=df["DATETIME"], y=df[col],
                                         mode='markers',
                                         name=col),
                              secondary_y=False)

            elif graph_type == "Bar":
                fig.add_trace(go.Bar(x=df["DATETIME"], y=df[col],
                                    name=col),
                              secondary_y=False)

        for col in right_cols:
            if graph_type == "Line":
                fig.add_trace(go.Scatter(x=df["DATETIME"], y=df[col],
                                         mode='lines',
                                         name=col),
                              secondary_y=True)

            elif graph_type == "Scatter":
                fig.add_trace(go.Scatter(x=df["DATETIME"], y=df[col],
                                         mode='markers',
                                         name=col),
                              secondary_y=True)

            elif graph_type == "Bar":
                fig.add_trace(go.Bar(x=df["DATETIME"], y=df[col],
                                    name=col),
                              secondary_y=True)

        fig.update_layout(
            height=600,
            legend=dict(orientation="h"),
            xaxis_title="Time"
        )

        if log_scale:
            fig.update_yaxes(type="log", secondary_y=False)

        fig.update_yaxes(title_text="Primary Axis", secondary_y=False)
        fig.update_yaxes(title_text="Secondary Axis", secondary_y=True)

        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Export")

    if st.button("Download HTML"):
        fig.write_html("graph.html")
        with open("graph.html", "rb") as f:
            st.download_button("Download File", f, file_name="graph.html")