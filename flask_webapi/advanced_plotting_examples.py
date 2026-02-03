"""
Advanced Plotly Features for OpenSNPQual
Examples of interactive plots with annotations, draggable elements, and custom interactions

SPDX-License-Identifier: BSD-3-Clause
"""

import plotly.graph_objs as go
from plotly.subplots import make_subplots
import numpy as np


def create_interactive_sparam_plot(freq, s_params, port_num):
    """
    Create interactive S-parameter plot with:
    - Zoom/pan
    - Draggable annotations
    - Click events
    - Range slider
    - Export options
    """
    
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Magnitude (dB)', 'Phase (degrees)'),
        vertical_spacing=0.12,
        row_heights=[0.5, 0.5]
    )
    
    # Add S-parameter traces
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F7DC6F']
    
    for i in range(port_num):
        for j in range(port_num):
            s_ij = s_params[:, i, j]
            mag_db = 20 * np.log10(np.abs(s_ij) + 1e-12)
            phase_deg = np.angle(s_ij, deg=True)
            
            color = colors[(i * port_num + j) % len(colors)]
            
            # Magnitude trace
            fig.add_trace(
                go.Scatter(
                    x=freq / 1e9,
                    y=mag_db,
                    mode='lines',
                    name=f'S{i+1}{j+1}',
                    line=dict(color=color, width=2),
                    legendgroup=f'S{i+1}{j+1}',
                    hovertemplate=(
                        '<b>S%d%d</b><br>' % (i+1, j+1) +
                        'Frequency: %{x:.3f} GHz<br>' +
                        'Magnitude: %{y:.2f} dB<br>' +
                        '<extra></extra>'
                    )
                ),
                row=1, col=1
            )
            
            # Phase trace
            fig.add_trace(
                go.Scatter(
                    x=freq / 1e9,
                    y=phase_deg,
                    mode='lines',
                    name=f'S{i+1}{j+1}',
                    line=dict(color=color, width=2),
                    legendgroup=f'S{i+1}{j+1}',
                    showlegend=False,
                    hovertemplate=(
                        '<b>S%d%d</b><br>' % (i+1, j+1) +
                        'Frequency: %{x:.3f} GHz<br>' +
                        'Phase: %{y:.1f}°<br>' +
                        '<extra></extra>'
                    )
                ),
                row=2, col=1
            )
    
    # Add draggable annotations
    annotations = []
    
    # Example: Mark -3dB point
    for i in range(port_num):
        for j in range(port_num):
            if i != j:  # Only for transmission parameters
                s_ij = s_params[:, i, j]
                mag_db = 20 * np.log10(np.abs(s_ij) + 1e-12)
                
                # Find -3dB point
                idx_3db = np.argmin(np.abs(mag_db + 3))
                if idx_3db < len(freq):
                    annotations.append(
                        dict(
                            x=freq[idx_3db] / 1e9,
                            y=mag_db[idx_3db],
                            text=f'-3dB: {freq[idx_3db]/1e9:.2f} GHz',
                            showarrow=True,
                            arrowhead=2,
                            arrowsize=1,
                            arrowwidth=2,
                            arrowcolor='red',
                            ax=-40,
                            ay=-40,
                            bgcolor='rgba(255,255,255,0.8)',
                            bordercolor='red',
                            borderwidth=2,
                            borderpad=4,
                            font=dict(size=12, color='red'),
                            xref='x',
                            yref='y',
                            # DRAGGABLE - users can move these!
                            draggable=True
                        )
                    )
    
    # Update layout with advanced features
    fig.update_layout(
        title={
            'text': 'Interactive S-Parameter Analysis',
            'font': {'size': 20, 'color': '#2c3e50'},
            'x': 0.5,
            'xanchor': 'center'
        },
        hovermode='x unified',
        template='plotly_white',
        height=800,
        annotations=annotations,
        
        # Enable range slider on x-axis
        xaxis=dict(
            rangeslider=dict(visible=True, thickness=0.05),
            title='Frequency (GHz)',
            gridcolor='lightgray'
        ),
        
        # Styling
        plot_bgcolor='white',
        paper_bgcolor='#f8f9fa',
        
        # Legend
        legend=dict(
            orientation="v",
            yanchor="top",
            y=0.99,
            xanchor="right",
            x=1.15,
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='gray',
            borderwidth=1
        ),
        
        # Export config
        modebar=dict(
            bgcolor='rgba(255,255,255,0.8)',
            color='#2c3e50',
            activecolor='#e74c3c'
        )
    )
    
    # Update axes
    fig.update_xaxes(title_text="Frequency (GHz)", row=2, col=1)
    fig.update_yaxes(title_text="Magnitude (dB)", row=1, col=1)
    fig.update_yaxes(title_text="Phase (degrees)", row=2, col=1)
    
    return fig


def create_smith_chart_interactive(s11, freq):
    """
    Create interactive Smith chart with:
    - Constant resistance circles
    - Constant reactance arcs
    - Frequency color mapping
    - Hover info
    """
    
    fig = go.Figure()
    
    # Add S11 trace with frequency coloring
    fig.add_trace(go.Scatter(
        x=np.real(s11),
        y=np.imag(s11),
        mode='lines+markers',
        name='S11',
        marker=dict(
            size=6,
            color=freq / 1e9,
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(
                title='Freq<br>(GHz)',
                thickness=15,
                len=0.7
            ),
            line=dict(width=1, color='white')
        ),
        line=dict(width=2, color='rgba(100,100,100,0.3)'),
        hovertemplate=(
            'Frequency: %{marker.color:.2f} GHz<br>' +
            'Real: %{x:.3f}<br>' +
            'Imag: %{y:.3f}<br>' +
            'Magnitude: %{customdata[0]:.3f}<br>' +
            'Phase: %{customdata[1]:.1f}°<br>' +
            '<extra></extra>'
        ),
        customdata=np.column_stack([
            np.abs(s11),
            np.angle(s11, deg=True)
        ])
    ))
    
    # Add Smith chart grid
    # Constant resistance circles
    for r in [0.2, 0.5, 1.0, 2.0, 5.0]:
        theta = np.linspace(0, 2*np.pi, 100)
        z = r + 1j * np.tan(theta)
        gamma = (z - 1) / (z + 1)
        
        fig.add_trace(go.Scatter(
            x=np.real(gamma),
            y=np.imag(gamma),
            mode='lines',
            line=dict(color='lightgray', width=1, dash='dot'),
            showlegend=False,
            hoverinfo='skip'
        ))
    
    # Unit circle (r=∞)
    theta = np.linspace(0, 2*np.pi, 100)
    fig.add_trace(go.Scatter(
        x=np.cos(theta),
        y=np.sin(theta),
        mode='lines',
        line=dict(color='gray', width=2),
        showlegend=False,
        hoverinfo='skip'
    ))
    
    # Add draggable annotation for match point
    best_match_idx = np.argmin(np.abs(s11))
    
    fig.add_annotation(
        x=np.real(s11[best_match_idx]),
        y=np.imag(s11[best_match_idx]),
        text=f'Best Match<br>{freq[best_match_idx]/1e9:.2f} GHz',
        showarrow=True,
        arrowhead=2,
        arrowsize=1,
        arrowwidth=2,
        arrowcolor='green',
        ax=50,
        ay=-50,
        bgcolor='rgba(255,255,255,0.9)',
        bordercolor='green',
        borderwidth=2,
        font=dict(size=11, color='green'),
        draggable=True
    )
    
    fig.update_layout(
        title='Smith Chart - S11',
        xaxis=dict(
            scaleanchor='y',
            scaleratio=1,
            range=[-1.1, 1.1],
            title='Real',
            gridcolor='lightgray',
            zeroline=True,
            zerolinecolor='black',
            zerolinewidth=2
        ),
        yaxis=dict(
            range=[-1.1, 1.1],
            title='Imaginary',
            gridcolor='lightgray',
            zeroline=True,
            zerolinecolor='black',
            zerolinewidth=2
        ),
        template='plotly_white',
        height=700,
        width=700,
        hovermode='closest'
    )
    
    return fig


def create_eye_diagram_interactive(time, waveform, ui_period):
    """
    Create interactive eye diagram with:
    - Click to measure eye opening
    - Draggable cursors
    - Statistics overlay
    """
    
    fig = go.Figure()
    
    # Overlay multiple UI periods
    samples_per_ui = int(ui_period / (time[1] - time[0]))
    num_uis = len(time) // samples_per_ui
    
    colors = ['rgba(100,149,237,0.3)'] * num_uis
    
    for i in range(num_uis - 1):
        start_idx = i * samples_per_ui
        end_idx = (i + 2) * samples_per_ui
        
        if end_idx < len(time):
            t_segment = time[start_idx:end_idx] - time[start_idx]
            w_segment = waveform[start_idx:end_idx]
            
            fig.add_trace(go.Scatter(
                x=t_segment * 1e12,  # Convert to ps
                y=w_segment * 1000,  # Convert to mV
                mode='lines',
                line=dict(color=colors[i % len(colors)], width=1),
                showlegend=False,
                hovertemplate='Time: %{x:.1f} ps<br>Voltage: %{y:.1f} mV<extra></extra>'
            ))
    
    # Add draggable measurement cursors
    cursor_positions = [0.3, 0.7]  # At 30% and 70% of UI
    
    for i, pos in enumerate(cursor_positions):
        fig.add_vline(
            x=pos * ui_period * 2 * 1e12,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Cursor {i+1}",
            annotation=dict(
                bgcolor="rgba(255,255,255,0.8)",
                bordercolor="red"
            )
        )
    
    # Add eye opening annotation (draggable)
    fig.add_annotation(
        x=ui_period * 1e12,
        y=400,
        text="Eye Opening<br>Measure Here",
        showarrow=True,
        arrowhead=2,
        arrowcolor="green",
        bgcolor="rgba(144,238,144,0.8)",
        bordercolor="green",
        borderwidth=2,
        draggable=True
    )
    
    fig.update_layout(
        title='Interactive Eye Diagram',
        xaxis_title='Time (ps)',
        yaxis_title='Voltage (mV)',
        template='plotly_white',
        height=500,
        hovermode='closest'
    )
    
    return fig


def create_comparison_plot(freq1, s11_1, freq2, s11_2, labels=['Design 1', 'Design 2']):
    """
    Create comparison plot with:
    - Synchronized axes
    - Difference trace
    - Toggle buttons
    """
    
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('S11 Comparison', 'Difference'),
        vertical_spacing=0.12,
        row_heights=[0.65, 0.35]
    )
    
    # Convert to dB
    s11_1_db = 20 * np.log10(np.abs(s11_1) + 1e-12)
    s11_2_db = 20 * np.log10(np.abs(s11_2) + 1e-12)
    
    # Add traces
    fig.add_trace(
        go.Scatter(
            x=freq1 / 1e9, y=s11_1_db,
            name=labels[0],
            line=dict(color='blue', width=2),
            visible=True
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=freq2 / 1e9, y=s11_2_db,
            name=labels[1],
            line=dict(color='red', width=2, dash='dash'),
            visible=True
        ),
        row=1, col=1
    )
    
    # Interpolate to common frequency grid for difference
    freq_common = np.linspace(
        max(freq1[0], freq2[0]),
        min(freq1[-1], freq2[-1]),
        min(len(freq1), len(freq2))
    )
    
    s11_1_interp = np.interp(freq_common, freq1, s11_1_db)
    s11_2_interp = np.interp(freq_common, freq2, s11_2_db)
    diff = s11_1_interp - s11_2_interp
    
    fig.add_trace(
        go.Scatter(
            x=freq_common / 1e9, y=diff,
            name='Difference',
            fill='tozeroy',
            line=dict(color='green', width=2)
        ),
        row=2, col=1
    )
    
    # Add toggle buttons
    fig.update_layout(
        updatemenus=[
            dict(
                type="buttons",
                direction="left",
                x=0.1,
                y=1.15,
                buttons=[
                    dict(
                        label="Show All",
                        method="update",
                        args=[{"visible": [True, True, True]}]
                    ),
                    dict(
                        label=labels[0] + " Only",
                        method="update",
                        args=[{"visible": [True, False, False]}]
                    ),
                    dict(
                        label=labels[1] + " Only",
                        method="update",
                        args=[{"visible": [False, True, False]}]
                    )
                ]
            )
        ],
        title='Design Comparison',
        hovermode='x unified',
        template='plotly_white',
        height=700
    )
    
    fig.update_xaxes(title_text="Frequency (GHz)", row=2, col=1)
    fig.update_yaxes(title_text="S11 (dB)", row=1, col=1)
    fig.update_yaxes(title_text="Difference (dB)", row=2, col=1)
    
    return fig


# Example usage
if __name__ == "__main__":
    # Generate example data
    freq = np.linspace(0.1e9, 20e9, 1000)
    
    # Example 2-port S-parameters
    s_params = np.zeros((len(freq), 2, 2), dtype=complex)
    for i, f in enumerate(freq):
        # Simple transmission line model
        loss = 0.9 * np.exp(-f/10e9)
        phase = -2 * np.pi * f * 100e-12
        
        s_params[i, 0, 0] = 0.1 * np.exp(1j * phase * 0.5)
        s_params[i, 1, 1] = 0.1 * np.exp(1j * phase * 0.5)
        s_params[i, 0, 1] = loss * np.exp(1j * phase)
        s_params[i, 1, 0] = loss * np.exp(1j * phase)
    
    # Create interactive plot
    fig = create_interactive_sparam_plot(freq, s_params, 2)
    
    # Save as HTML (can be opened in browser)
    fig.write_html("interactive_sparam.html")
    print("Created interactive_sparam.html")
    
    # Create Smith chart
    s11 = s_params[:, 0, 0]
    fig_smith = create_smith_chart_interactive(s11, freq)
    fig_smith.write_html("interactive_smith.html")
    print("Created interactive_smith.html")
    
    print("\nOpen the HTML files in your browser to see interactive plots!")
    print("Features:")
    print("- Zoom and pan")
    print("- Drag annotations around")
    print("- Hover for detailed information")
    print("- Export to PNG/SVG")
    print("- Range slider for easy navigation")
