import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import random

# Set page config
st.set_page_config(page_title="Syringe Inspection Simulator", layout="wide")

# Initialize session state variables
if 'streaming' not in st.session_state:
    st.session_state.streaming = False
if 'data' not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=['TAGNAME', 'TAGVALUE', 'TIMESTAMP'])
if 'start_time' not in st.session_state:
    st.session_state.start_time = datetime.now()
if 'cumulative_data' not in st.session_state:
    st.session_state.cumulative_data = pd.DataFrame(columns=['TAGNAME', 'TAGVALUE', 'TIMESTAMP'])

# Sidebar controls
st.sidebar.title("Control Panel")

# Batch configuration
batch_name = st.sidebar.text_input("Batch Name", "Batch-1")
stream_speed = st.sidebar.slider("Stream Speed (seconds)", 1, 10, 5)

# Defect rate controls
st.sidebar.subheader("Defect Rates (%)")
defect_rate_1 = st.sidebar.slider("Tag-1 (Flange Defect)", 0.0, 5.0, 1.0)
defect_rate_2 = st.sidebar.slider("Tag-2 (Glass Defect)", 0.0, 5.0, 1.5)
defect_rate_3 = st.sidebar.slider("Tag-3 (Wall Defect)", 0.0, 5.0, 0.8)

# Inspection rate
inspections_per_interval = st.sidebar.slider("Inspections per 5-min interval", 100, 1000, 500)

def generate_interval_data(timestamp):
    """Generate data for one 5-minute interval"""
    data = []
    
    # Calculate defects based on rates
    defects_1 = int(inspections_per_interval * (defect_rate_1 / 100))
    defects_2 = int(inspections_per_interval * (defect_rate_2 / 100))
    defects_3 = int(inspections_per_interval * (defect_rate_3 / 100))
    total_defects = defects_1 + defects_2 + defects_3
    
    # Add noise to make it more realistic
    defects_1 += np.random.randint(-2, 3)
    defects_2 += np.random.randint(-2, 3)
    defects_3 += np.random.randint(-2, 3)
    
    # Ensure non-negative values
    defects_1 = max(0, defects_1)
    defects_2 = max(0, defects_2)
    defects_3 = max(0, defects_3)
    total_defects = defects_1 + defects_2 + defects_3
    
    # Create rows for each tag
    data.append({'TAGNAME': 'tag-1', 'TAGVALUE': defects_1, 'TIMESTAMP': timestamp})
    data.append({'TAGNAME': 'tag-2', 'TAGVALUE': defects_2, 'TIMESTAMP': timestamp})
    data.append({'TAGNAME': 'tag-3', 'TAGVALUE': defects_3, 'TIMESTAMP': timestamp})
    data.append({'TAGNAME': 'tag-4', 'TAGVALUE': total_defects, 'TIMESTAMP': timestamp})
    data.append({'TAGNAME': 'tag-5', 'TAGVALUE': inspections_per_interval, 'TIMESTAMP': timestamp})
    
    return pd.DataFrame(data)

def update_cumulative_data():
    """Update cumulative values for tag-4 and tag-5"""
    cumulative_data = []
    
    for tag in ['tag-4', 'tag-5']:
        tag_data = st.session_state.data[st.session_state.data['TAGNAME'] == tag].copy()
        if not tag_data.empty:
            tag_data['TAGVALUE'] = tag_data['TAGVALUE'].cumsum()
            cumulative_data.append(tag_data)
    
    if cumulative_data:
        st.session_state.cumulative_data = pd.concat(cumulative_data, ignore_index=True)

def create_plots():
    """Create and update all three plots"""
    # 1. Individual defects plot (tag-1, tag-2, tag-3)
    fig1 = go.Figure()
    
    for tag in ['tag-1', 'tag-2', 'tag-3']:
        tag_data = st.session_state.data[st.session_state.data['TAGNAME'] == tag].copy()
        if not tag_data.empty:
            fig1.add_trace(go.Scatter(
                x=tag_data['TIMESTAMP'],
                y=tag_data['TAGVALUE'],
                name=tag,
                mode='lines+markers'
            ))
    
    fig1.update_layout(
        title="Individual Defect Types Over Time",
        xaxis_title="Time",
        yaxis_title="Number of Defects",
        height=300
    )
    
    # 2. Total defects plot (tag-4)
    fig2 = go.Figure()
    
    tag4_data = st.session_state.cumulative_data[st.session_state.cumulative_data['TAGNAME'] == 'tag-4'].copy()
    if not tag4_data.empty:
        fig2.add_trace(go.Scatter(
            x=tag4_data['TIMESTAMP'],
            y=tag4_data['TAGVALUE'],
            name='Total Cumulative Defects',
            mode='lines+markers',
            line=dict(width=3, color='red')
        ))
    
    fig2.update_layout(
        title="Cumulative Total Defects Over Time",
        xaxis_title="Time",
        yaxis_title="Total Number of Defects",
        height=300
    )
    
    # 3. Total inspected plot (tag-5)
    fig3 = go.Figure()
    
    tag5_data = st.session_state.cumulative_data[st.session_state.cumulative_data['TAGNAME'] == 'tag-5'].copy()
    if not tag5_data.empty:
        fig3.add_trace(go.Scatter(
            x=tag5_data['TIMESTAMP'],
            y=tag5_data['TAGVALUE'],
            name='Total Inspected',
            mode='lines+markers',
            line=dict(width=3, color='green')
        ))
    
    fig3.update_layout(
        title="Cumulative Total Inspected Syringes Over Time",
        xaxis_title="Time",
        yaxis_title="Number of Inspected Syringes",
        height=300
    )
    
    return fig1, fig2, fig3

# Create main layout
st.title("Syringe Inspection Data Stream Simulator")

# Create placeholders for plots
defect_plot = st.empty()
total_defects_plot = st.empty()
inspection_plot = st.empty()
metrics_placeholder = st.container()

# Start/Stop button
if st.sidebar.button("Start/Stop Stream"):
    st.session_state.streaming = not st.session_state.streaming
    if st.session_state.streaming:
        st.session_state.start_time = datetime.now()
        # Add batch start marker
        batch_start = pd.DataFrame([{
            'TAGNAME': 'tag-0',
            'TAGVALUE': batch_name,
            'TIMESTAMP': st.session_state.start_time
        }])
        st.session_state.data = pd.concat([st.session_state.data, batch_start], ignore_index=True)

# Save data button
if st.sidebar.button("Save Data"):
    if not st.session_state.data.empty:
        st.session_state.data.to_excel("inspection_data.xlsx", index=False)
        st.sidebar.success("Data saved to inspection_data.xlsx")

# Main streaming loop
while st.session_state.streaming:
    # Generate new data
    current_time = datetime.now()
    new_data = generate_interval_data(current_time)
    st.session_state.data = pd.concat([st.session_state.data, new_data], ignore_index=True)
    
    # Update cumulative data
    update_cumulative_data()
    
    # Create and update plots
    fig1, fig2, fig3 = create_plots()
    defect_plot.plotly_chart(fig1, use_container_width=True)
    total_defects_plot.plotly_chart(fig2, use_container_width=True)
    inspection_plot.plotly_chart(fig3, use_container_width=True)
    
    # Display current metrics
    with metrics_placeholder:
        cols = st.columns(4)
        latest_data = st.session_state.data.groupby('TAGNAME').last()
        cumulative_data = st.session_state.cumulative_data.groupby('TAGNAME').last()
        
        if not latest_data.empty and not cumulative_data.empty:
            cols[0].metric("Total Inspected", int(cumulative_data.loc['tag-5', 'TAGVALUE']))
            cols[1].metric("Total Defects", int(cumulative_data.loc['tag-4', 'TAGVALUE']))
            defect_rate = (cumulative_data.loc['tag-4', 'TAGVALUE'] / cumulative_data.loc['tag-5', 'TAGVALUE']) * 100
            cols[2].metric("Defect Rate", f"{defect_rate:.2f}%")
            cols[3].metric("Batch", batch_name)
    
    time.sleep(stream_speed)

# Keep displaying the plots even when streaming is stopped
if not st.session_state.streaming and not st.session_state.data.empty:
    fig1, fig2, fig3 = create_plots()
    defect_plot.plotly_chart(fig1, use_container_width=True)
    total_defects_plot.plotly_chart(fig2, use_container_width=True)
    inspection_plot.plotly_chart(fig3, use_container_width=True)
    
    # Display final metrics
    with metrics_placeholder:
        cols = st.columns(4)
        latest_data = st.session_state.data.groupby('TAGNAME').last()
        cumulative_data = st.session_state.cumulative_data.groupby('TAGNAME').last()
        
        if not latest_data.empty and not cumulative_data.empty:
            cols[0].metric("Total Inspected", int(cumulative_data.loc['tag-5', 'TAGVALUE']))
            cols[1].metric("Total Defects", int(cumulative_data.loc['tag-4', 'TAGVALUE']))
            defect_rate = (cumulative_data.loc['tag-4', 'TAGVALUE'] / cumulative_data.loc['tag-5', 'TAGVALUE']) * 100
            cols[2].metric("Defect Rate", f"{defect_rate:.2f}%")
            cols[3].metric("Batch", batch_name)