import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
import json
import os
from visualization.simple_engine_viz import create_simple_engine_viz

def create_showcase_dashboard():
    """Create a showcase dashboard to demonstrate all visualization capabilities"""
    
    # Set page config
    st.set_page_config(
        page_title="Rocket Engine Visualization Showcase",
        page_icon="🚀",
        layout="wide"
    )
    
    # Title and introduction
    st.title("Rocket Engine Visualization Showcase")
    st.markdown("""
    This showcase demonstrates the various visualization techniques implemented for the PINN-based PID Controller for Liquid Propulsion Engine project.
    Each tab shows a different visualization approach or perspective on the rocket engine system.
    """)
    
    # Create tabs for different visualizations
    tabs = st.tabs([
        "3D Engine Model", 
        "Engine Performance Graphs", 
        "Combustion Analysis", 
        "Thrust Profiles", 
        "Propellant Flow"
    ])
    
    # Default engine parameters
    engine_params = {
        "status": "Nominal Operation",
        "chamberPressure": 2.5,
        "mixtureRatio": 2.8,
        "chamberLength": 0.15,
        "chamberDiameter": 0.08,
        "throatDiameter": 0.03,
        "exitDiameter": 0.09,
        "nozzleLength": 0.12,
    }
    
    # Store in session state for reuse
    if "engine_params" not in st.session_state:
        st.session_state.engine_params = engine_params
    
    # 3D Engine Model Tab
    with tabs[0]:
        st.header("3D Engine Visualization")
        st.markdown("""
        This interactive 3D model shows the liquid rocket engine with realistic physics-based effects.
        The visualization includes the combustion chamber, nozzle, and exhaust plume with shock diamonds.
        """)
        
        # Create two columns
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Create the 3D visualization
            create_simple_engine_viz(height=600)
        
        with col2:
            st.subheader("Key Components")
            st.markdown("""
            - **Combustion Chamber**: Where propellants mix and burn
            - **Nozzle**: Accelerates exhaust gases
            - **Throat**: Choke point for supersonic flow
            - **Injector Face**: Where propellants are injected
            - **Exhaust Plume**: Visual representation of thrust
            - **Shock Diamonds**: Pressure equalization features
            """)
            
            st.subheader("Current Parameters")
            st.metric("Chamber Pressure", f"{engine_params['chamberPressure']:.1f} MPa")
            st.metric("Mixture Ratio", f"{engine_params['mixtureRatio']:.1f}")
            st.metric("Status", engine_params['status'])
    
    # Engine Performance Graphs
    with tabs[1]:
        st.header("Engine Performance Visualization")
        st.markdown("""
        These graphs show key performance metrics and their relationships.
        """)
        
        # Create sample data
        chamber_pressures = np.linspace(0.5, 5.0, 20)
        mixture_ratios = np.linspace(1.5, 6.0, 10)
        
        # Create mesh grid for 3D surface
        cp_grid, mr_grid = np.meshgrid(chamber_pressures, mixture_ratios)
        
        # Calculate thrust (simplified model)
        def calculate_thrust(cp, mr):
            # Basic formula relating chamber pressure and mixture ratio to thrust
            base_thrust = cp * 10000  # 10kN per MPa as baseline
            
            # Adjust for non-optimal mixture ratio (peak around 2.5-3.0)
            mr_factor = 1.0 - 0.2 * abs(mr - 2.7) / 2.7
            
            return base_thrust * mr_factor
        
        # Calculate thrust values
        thrust_values = np.zeros_like(cp_grid)
        for i in range(len(mixture_ratios)):
            for j in range(len(chamber_pressures)):
                thrust_values[i, j] = calculate_thrust(cp_grid[i, j], mr_grid[i, j])
        
        # Create 3D surface plot
        fig = go.Figure(data=[go.Surface(
            x=cp_grid, 
            y=mr_grid, 
            z=thrust_values,
            colorscale='Viridis'
        )])
        
        fig.update_layout(
            title="Thrust as Function of Chamber Pressure and Mixture Ratio",
            scene=dict(
                xaxis_title="Chamber Pressure (MPa)",
                yaxis_title="Mixture Ratio (O/F)",
                zaxis_title="Thrust (N)"
            ),
            width=900,
            height=600,
            margin=dict(l=65, r=50, b=65, t=90)
        )
        
        st.plotly_chart(fig)
        
        # Add additional 2D plots
        col1, col2 = st.columns(2)
        
        with col1:
            # ISP vs Mixture Ratio
            isp_values = []
            for mr in mixture_ratios:
                # Simplified ISP model
                if mr < 2.5:  # LOX/LH2
                    isp = 360 + (mr - 1.5) * 20
                elif mr < 3.5:  # LOX/CH4
                    isp = 300 + (mr - 2.5) * 10
                else:  # LOX/RP-1
                    isp = 280 + (mr - 3.5) * 5
                isp_values.append(isp)
            
            fig1 = px.line(
                x=mixture_ratios, 
                y=isp_values,
                labels={"x": "Mixture Ratio (O/F)", "y": "Specific Impulse (s)"},
                title="ISP vs Mixture Ratio"
            )
            st.plotly_chart(fig1)
            
        with col2:
            # Expansion Ratio vs Performance
            expansion_ratios = np.linspace(2, 20, 15)
            er_isp_gain = [5 * np.log(er/2) for er in expansion_ratios]
            
            fig2 = px.line(
                x=expansion_ratios, 
                y=er_isp_gain,
                labels={"x": "Expansion Ratio", "y": "ISP Gain (s)"},
                title="Expansion Ratio Effect on Performance"
            )
            st.plotly_chart(fig2)
    
    # Combustion Analysis
    with tabs[2]:
        st.header("Combustion Analysis Visualization")
        
        # Sample temperature distribution in combustion chamber
        x = np.linspace(0, 1, 50)  # Normalized chamber length
        y = np.linspace(-0.5, 0.5, 50)  # Normalized chamber radius
        X, Y = np.meshgrid(x, y)
        
        # Temperature distribution (higher near injector face, cooler near walls)
        Z = 3000 * (1 - 0.7*X) * (1 - 2.0*Y**2)
        
        # Create heatmap
        fig = px.imshow(
            Z,
            labels=dict(x="Chamber Length", y="Chamber Radius", color="Temperature (K)"),
            x=np.linspace(0, 0.15, 50),  # Convert to meters using chamber length
            y=np.linspace(-0.04, 0.04, 50),  # Convert to meters using chamber radius
            color_continuous_scale="inferno"
        )
        
        fig.update_layout(
            title="Temperature Distribution in Combustion Chamber",
            width=900,
            height=500
        )
        
        st.plotly_chart(fig)
        
        # Add explanatory text
        st.markdown("""
        The temperature distribution visualization shows how temperature varies throughout the combustion chamber:
        
        - **Highest temperatures** are near the center of the chamber where combustion is most intense
        - **Cooler regions** exist near the chamber walls due to boundary layer effects
        - **Temperature decreases** along the chamber length as gases expand
        
        This analysis helps identify potential hot spots and optimize cooling system design.
        """)
        
        # Add another visualization - Species concentration
        st.subheader("Species Concentration Along Chamber Length")
        
        chamber_length = np.linspace(0, 0.15, 100)
        
        # Simplified species concentration model
        fuel = 1.0 - 1.0 / (1.0 + np.exp(-20 * (chamber_length - 0.02)))
        oxidizer = 1.0 - 1.0 / (1.0 + np.exp(-20 * (chamber_length - 0.02)))
        combustion_products = 1.0 / (1.0 + np.exp(-20 * (chamber_length - 0.03)))
        
        # Create concentration plot
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=chamber_length, y=fuel, mode='lines', name='Fuel'))
        fig2.add_trace(go.Scatter(x=chamber_length, y=oxidizer, mode='lines', name='Oxidizer'))
        fig2.add_trace(go.Scatter(x=chamber_length, y=combustion_products, mode='lines', name='Combustion Products'))
        
        fig2.update_layout(
            title="Species Concentration Along Chamber Length",
            xaxis_title="Chamber Length (m)",
            yaxis_title="Normalized Concentration",
            width=900,
            height=400
        )
        
        st.plotly_chart(fig2)
    
    # Thrust Profiles
    with tabs[3]:
        st.header("Thrust Profile Visualization")
        
        # Sample thrust profile data for different scenarios
        time_points = np.linspace(0, 30, 300)
        
        # Normal operation thrust profile
        thrust_normal = 50000 * np.ones_like(time_points)
        thrust_normal[:50] = np.linspace(0, 50000, 50)  # Ramp-up
        thrust_normal[-50:] = np.linspace(50000, 0, 50)  # Shutdown
        
        # Add realistic oscillations
        oscillation = 1000 * np.sin(time_points * 2) + 500 * np.sin(time_points * 5) + 200 * np.sin(time_points * 11)
        thrust_normal += oscillation
        
        # Anomaly thrust profile (engine chugging)
        thrust_anomaly = thrust_normal.copy()
        # Add chugging effect between t=10s and t=15s
        chugging_idx = np.where((time_points >= 10) & (time_points <= 15))[0]
        thrust_anomaly[chugging_idx] += 5000 * np.sin(time_points[chugging_idx] * 20)
        
        # Create thrust profile plot
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=time_points, y=thrust_normal, mode='lines', name='Normal Operation'))
        fig.add_trace(go.Scatter(x=time_points, y=thrust_anomaly, mode='lines', name='Combustion Instability'))
        
        fig.update_layout(
            title="Thrust Profiles: Normal vs. Anomalous Operation",
            xaxis_title="Time (s)",
            yaxis_title="Thrust (N)",
            width=900,
            height=500,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            )
        )
        
        st.plotly_chart(fig)
        
        # Explanatory text
        st.markdown("""
        The thrust profile visualization shows how thrust varies over time during different engine operation scenarios:
        
        - **Normal Operation**: Shows smooth startup, steady-state operation with minor oscillations, and controlled shutdown
        - **Combustion Instability**: Demonstrates an anomalous condition with combustion instability (chugging) between t=10s and t=15s
        
        Analyzing these profiles helps identify potential issues and develop control strategies to maintain stable operation.
        """)
        
        # Frequency analysis
        st.subheader("Frequency Analysis of Thrust Oscillations")
        
        # Compute FFT of the oscillation component
        from scipy.fft import fft, fftfreq
        
        N = len(oscillation)
        T = time_points[1] - time_points[0]  # sampling interval
        
        yf = fft(oscillation)
        xf = fftfreq(N, T)[:N//2]
        
        # Plot only the positive frequencies
        fig2 = go.Figure(data=go.Scatter(
            x=xf[:N//4], 
            y=2.0/N * np.abs(yf[:N//4]),
            mode='lines'
        ))
        
        fig2.update_layout(
            title="Frequency Spectrum of Thrust Oscillations",
            xaxis_title="Frequency (Hz)",
            yaxis_title="Amplitude",
            width=900,
            height=400
        )
        
        st.plotly_chart(fig2)
    
    # Propellant Flow
    with tabs[4]:
        st.header("Propellant Flow Visualization")
        
        # Create a Sankey diagram to visualize propellant flow
        st.subheader("Propellant Flow Distribution")
        
        # Create Sankey diagram
        fig = go.Figure(data=[go.Sankey(
            arrangement = "snap",
            node = {
                "label": [
                    "Fuel Tank", "Oxidizer Tank", 
                    "Fuel Pump", "Oxidizer Pump",
                    "Fuel Valve", "Oxidizer Valve",
                    "Cooling Channels", "Injector",
                    "Combustion Chamber", "Nozzle",
                    "Exhaust"
                ],
                "color": [
                    "rgba(31, 119, 180, 0.8)", "rgba(255, 127, 14, 0.8)",
                    "rgba(44, 160, 44, 0.8)", "rgba(214, 39, 40, 0.8)",
                    "rgba(148, 103, 189, 0.8)", "rgba(140, 86, 75, 0.8)",
                    "rgba(227, 119, 194, 0.8)", "rgba(127, 127, 127, 0.8)",
                    "rgba(188, 189, 34, 0.8)", "rgba(23, 190, 207, 0.8)",
                    "rgba(31, 119, 180, 0.8)"
                ]
            },
            link = {
                "source": [0, 1, 2, 3, 4, 6, 5, 7, 7, 8, 9],
                "target": [2, 3, 4, 5, 6, 7, 7, 8, 8, 9, 10],
                "value": [10, 30, 10, 30, 10, 10, 30, 10, 30, 40, 40],
                "color": [
                    "rgba(31, 119, 180, 0.4)", "rgba(255, 127, 14, 0.4)",
                    "rgba(31, 119, 180, 0.4)", "rgba(255, 127, 14, 0.4)",
                    "rgba(31, 119, 180, 0.4)", "rgba(31, 119, 180, 0.4)",
                    "rgba(255, 127, 14, 0.4)", "rgba(31, 119, 180, 0.4)",
                    "rgba(255, 127, 14, 0.4)", "rgba(214, 39, 40, 0.4)",
                    "rgba(214, 39, 40, 0.4)"
                ]
            }
        )])
        
        fig.update_layout(
            title="Propellant Flow Path Visualization",
            width=900,
            height=600,
            font=dict(size=10)
        )
        
        st.plotly_chart(fig)
        
        # Add explanatory text
        st.markdown("""
        The Sankey diagram visualizes the flow of propellants through the engine:
        
        - **Blue flows**: Fuel (typically LH2, CH4, or RP-1)
        - **Orange flows**: Oxidizer (typically LOX)
        - **Red flows**: Hot combustion products
        
        The width of each flow path represents the relative mass flow rate.
        Notice how the fuel first passes through cooling channels before reaching the injector.
        """)
        
        # Add a pressure distribution chart
        st.subheader("Pressure Distribution Throughout Engine System")
        
        # Engine components and their typical pressures
        components = [
            "Fuel Tank", "Oxidizer Tank", "Fuel Pump Outlet", "Oxidizer Pump Outlet",
            "Cooling Channels", "Fuel Injector", "Oxidizer Injector", 
            "Combustion Chamber", "Nozzle Throat", "Nozzle Exit"
        ]
        
        # Pressure values in MPa
        pressures = [0.3, 0.3, 6.0, 6.0, 5.5, 4.0, 4.0, 2.5, 1.4, 0.1]
        
        # Create the pressure chart
        fig2 = px.bar(
            x=components, 
            y=pressures,
            labels={"x": "Engine Component", "y": "Pressure (MPa)"},
            title="Pressure Distribution Throughout Engine"
        )
        
        fig2.update_layout(width=900, height=400)
        st.plotly_chart(fig2)

    # Footer
    st.markdown("---")
    st.markdown("""
    This showcase demonstrates the visualization capabilities developed for the PINN-based PID Controller for Liquid Propulsion Engine project.
    All visualizations integrate physics-based models with realistic engine performance characteristics.
    """)

if __name__ == "__main__":
    create_showcase_dashboard() 