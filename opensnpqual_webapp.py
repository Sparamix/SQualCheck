#!/usr/bin/env python3
"""
OpenSNPQual Web-Based GUI
Modern web interface using Flask + Plotly.js for S-parameter quality analysis

SPDX-License-Identifier: BSD-3-Clause
"""

from flask import Flask, render_template, request, jsonify
import plotly.graph_objs as go
import plotly.express as px
from plotly.subplots import make_subplots
import json
import numpy as np
import skrf as rf
from pathlib import Path
import tempfile
import os

# Your existing modules
from ieee370_implementation.ieee_p370_quality_freq_domain import quality_check_frequency_domain, quality_check_frequency_domain_detailed
from ieee370_implementation.ieee_p370_quality_time_domain import quality_check

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

OPENSNPQUAL_VERSION = "v0.2-web"


@app.route('/')
def index():
    """Main page"""
    return render_template('index.html', version=OPENSNPQUAL_VERSION)


@app.route('/api/analyze', methods=['POST'])
def analyze_snp_file():
    """Analyze uploaded S-parameter file"""
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Get analysis options
    include_time_domain = request.form.get('includeTimeDomain', 'false') == 'true'
    data_rate = float(request.form.get('dataRate', 25.0))
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
            file.save(tmp.name)
            tmp_path = tmp.name
        
        # Load S-parameters
        network = rf.Network(tmp_path)
        freq = network.f
        sdata = np.transpose(network.s, (1, 2, 0))
        nf = len(freq)
        port_num = network.nports
        
        # Frequency domain analysis (always performed)
        causality_freq, reciprocity_freq, passivity_freq = quality_check_frequency_domain(
            sdata, nf, port_num
        )
        
        # Get detailed metrics
        detailed = quality_check_frequency_domain_detailed(sdata, nf, port_num)
        
        results = {
            'filename': file.filename,
            'nports': port_num,
            'nfreq': nf,
            'freq_range': [float(freq[0]), float(freq[-1])],
            'metrics': {
                'causality_freq': float(100 - causality_freq) / 100,
                'reciprocity_freq': float(100 - reciprocity_freq) / 100,
                'passivity_freq': float(100 - passivity_freq) / 100,
            }
        }
        
        # Time domain analysis (optional)
        if include_time_domain:
            sample_per_ui = 64
            rise_per = 0.35
            pulse_shape = 1
            extrapolation_method = 1
            
            causality_time_mv, reciprocity_time_mv, passivity_time_mv = quality_check(
                freq, sdata, port_num, data_rate, sample_per_ui,
                rise_per, pulse_shape, extrapolation_method
            )
            
            results['metrics'].update({
                'causality_time': float(causality_time_mv / 2),
                'reciprocity_time': float(reciprocity_time_mv / 2),
                'passivity_time': float(passivity_time_mv / 2)
            })
        
        # Generate interactive plots
        plots = generate_interactive_plots(network, detailed, freq, sdata, port_num)
        results['plots'] = plots
        
        # Clean up temp file
        os.unlink(tmp_path)
        
        return jsonify(results)
    
    except Exception as e:
        if 'tmp_path' in locals():
            os.unlink(tmp_path)
        return jsonify({'error': str(e)}), 500


def generate_interactive_plots(network, detailed, freq, sdata, port_num):
    """Generate interactive Plotly figures"""
    
    plots = {}
    
    # 1. S-Parameter Magnitude Plot
    fig_mag = go.Figure()
    for i in range(port_num):
        for j in range(port_num):
            s_ij = network.s[:, i, j]
            mag_db = 20 * np.log10(np.abs(s_ij) + 1e-12)
            fig_mag.add_trace(go.Scatter(
                x=freq / 1e9,
                y=mag_db,
                mode='lines',
                name=f'S{i+1}{j+1}',
                hovertemplate='<b>S%d%d</b><br>Freq: %%{x:.2f} GHz<br>Mag: %%{y:.2f} dB<extra></extra>' % (i+1, j+1)
            ))
    
    fig_mag.update_layout(
        title='S-Parameter Magnitude',
        xaxis_title='Frequency (GHz)',
        yaxis_title='Magnitude (dB)',
        hovermode='x unified',
        template='plotly_white',
        height=400
    )
    plots['magnitude'] = json.loads(fig_mag.to_json())
    
    # 2. S-Parameter Phase Plot
    fig_phase = go.Figure()
    for i in range(port_num):
        for j in range(port_num):
            s_ij = network.s[:, i, j]
            phase_deg = np.angle(s_ij, deg=True)
            fig_phase.add_trace(go.Scatter(
                x=freq / 1e9,
                y=phase_deg,
                mode='lines',
                name=f'S{i+1}{j+1}',
                hovertemplate='<b>S%d%d</b><br>Freq: %%{x:.2f} GHz<br>Phase: %%{y:.1f}°<extra></extra>' % (i+1, j+1)
            ))
    
    fig_phase.update_layout(
        title='S-Parameter Phase',
        xaxis_title='Frequency (GHz)',
        yaxis_title='Phase (degrees)',
        hovermode='x unified',
        template='plotly_white',
        height=400
    )
    plots['phase'] = json.loads(fig_phase.to_json())
    
    # 3. Passivity Metric (Singular Values over frequency)
    fig_passivity = go.Figure()
    singular_values = np.zeros((port_num, len(freq)))
    
    for i, f_idx in enumerate(range(len(freq))):
        s_matrix = sdata[:, :, f_idx]
        sv = np.linalg.svd(s_matrix, compute_uv=False)
        singular_values[:, i] = sv
    
    for i in range(port_num):
        fig_passivity.add_trace(go.Scatter(
            x=freq / 1e9,
            y=singular_values[i, :],
            mode='lines',
            name=f'σ{i+1}',
            hovertemplate=f'<b>σ{i+1}</b><br>Freq: %{{x:.2f}} GHz<br>Value: %{{y:.4f}}<extra></extra>'
        ))
    
    # Add passivity limit line
    fig_passivity.add_hline(y=1.0, line_dash="dash", line_color="red", 
                           annotation_text="Passivity Limit (1.0)")
    
    fig_passivity.update_layout(
        title='Passivity Check (Singular Values)',
        xaxis_title='Frequency (GHz)',
        yaxis_title='Singular Value',
        hovermode='x unified',
        template='plotly_white',
        height=400
    )
    plots['passivity'] = json.loads(fig_passivity.to_json())
    
    # 4. Causality Quality Matrix Heatmap
    cqm = detailed['causality_matrix']
    fig_causality = go.Figure(data=go.Heatmap(
        z=cqm,
        x=[f'Port {j+1}' for j in range(port_num)],
        y=[f'Port {i+1}' for i in range(port_num)],
        colorscale='RdYlGn',
        text=cqm,
        texttemplate='%{text:.1f}%',
        textfont={"size": 12},
        colorbar=dict(title="Quality %"),
        hovertemplate='From: %{y}<br>To: %{x}<br>Quality: %{z:.2f}%<extra></extra>'
    ))
    
    fig_causality.update_layout(
        title='Causality Quality Matrix',
        xaxis_title='To Port',
        yaxis_title='From Port',
        template='plotly_white',
        height=400
    )
    plots['causality_matrix'] = json.loads(fig_causality.to_json())
    
    # 5. Smith Chart for S11 (if 2-port)
    if port_num == 2:
        fig_smith = go.Figure()
        
        # Add Smith chart circles and radials (simplified)
        # In practice, you'd use a proper Smith chart library or pre-computed coordinates
        
        s11 = network.s[:, 0, 0]
        fig_smith.add_trace(go.Scatter(
            x=np.real(s11),
            y=np.imag(s11),
            mode='lines+markers',
            name='S11',
            marker=dict(
                size=4,
                color=freq / 1e9,
                colorscale='Viridis',
                colorbar=dict(title="Freq (GHz)"),
                showscale=True
            ),
            hovertemplate='Freq: %{marker.color:.2f} GHz<br>Real: %{x:.3f}<br>Imag: %{y:.3f}<extra></extra>'
        ))
        
        # Add unit circle
        theta = np.linspace(0, 2*np.pi, 100)
        fig_smith.add_trace(go.Scatter(
            x=np.cos(theta),
            y=np.sin(theta),
            mode='lines',
            line=dict(color='gray', dash='dash'),
            showlegend=False,
            hoverinfo='skip'
        ))
        
        fig_smith.update_layout(
            title='S11 on Complex Plane',
            xaxis_title='Real',
            yaxis_title='Imaginary',
            template='plotly_white',
            height=400,
            yaxis=dict(scaleanchor="x", scaleratio=1)
        )
        plots['smith'] = json.loads(fig_smith.to_json())
    
    return plots


@app.route('/api/batch', methods=['POST'])
def batch_analyze():
    """Batch analysis of multiple files"""
    
    if 'files' not in request.files:
        return jsonify({'error': 'No files uploaded'}), 400
    
    files = request.files.getlist('files')
    include_time_domain = request.form.get('includeTimeDomain', 'false') == 'true'
    data_rate = float(request.form.get('dataRate', 25.0))
    
    results = []
    
    for file in files:
        try:
            # Save temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
                file.save(tmp.name)
                tmp_path = tmp.name
            
            # Load and analyze
            network = rf.Network(tmp_path)
            freq = network.f
            sdata = np.transpose(network.s, (1, 2, 0))
            nf = len(freq)
            port_num = network.nports
            
            # Frequency domain
            causality_freq, reciprocity_freq, passivity_freq = quality_check_frequency_domain(
                sdata, nf, port_num
            )
            
            result = {
                'filename': file.filename,
                'status': 'success',
                'causality_freq': float(100 - causality_freq) / 100,
                'reciprocity_freq': float(100 - reciprocity_freq) / 100,
                'passivity_freq': float(100 - passivity_freq) / 100,
            }
            
            # Time domain if requested
            if include_time_domain:
                causality_time_mv, reciprocity_time_mv, passivity_time_mv = quality_check(
                    freq, sdata, port_num, data_rate, 64, 0.35, 1, 1
                )
                result.update({
                    'causality_time': float(causality_time_mv / 2),
                    'reciprocity_time': float(reciprocity_time_mv / 2),
                    'passivity_time': float(passivity_time_mv / 2)
                })
            
            results.append(result)
            os.unlink(tmp_path)
            
        except Exception as e:
            results.append({
                'filename': file.filename,
                'status': 'error',
                'error': str(e)
            })
            if 'tmp_path' in locals():
                os.unlink(tmp_path)
    
    return jsonify({'results': results})


if __name__ == '__main__':
    print(f"OpenSNPQual {OPENSNPQUAL_VERSION} - Web Interface")
    print("Starting server at http://localhost:5000")
    print("Press Ctrl+C to stop")
    app.run(debug=True, host='localhost', port=5000)
