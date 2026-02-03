#!/usr/bin/env python3
"""
OpenSNPQual Desktop Application
Packages the web interface as a native desktop application using PyWebView

SPDX-License-Identifier: BSD-3-Clause
"""

import webview
import threading
from opensnpqual_webapp import app
import socket
import sys


def find_free_port():
    """Find a free port to run Flask on"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port


def run_flask(port):
    """Run Flask in a separate thread"""
    app.run(host='localhost', port=port, debug=False, use_reloader=False)


def create_desktop_app():
    """Create desktop application window"""
    
    # Find available port
    port = find_free_port()
    
    # Start Flask in background thread
    flask_thread = threading.Thread(target=run_flask, args=(port,), daemon=True)
    flask_thread.start()
    
    # Wait a moment for Flask to start
    import time
    time.sleep(1)
    
    # Create desktop window
    window = webview.create_window(
        'OpenSNPQual - S-Parameter Quality Checker',
        f'http://localhost:{port}',
        width=1400,
        height=900,
        resizable=True,
        fullscreen=False,
        min_size=(800, 600),
        confirm_close=False
    )
    
    webview.start(debug=False)


if __name__ == '__main__':
    create_desktop_app()
