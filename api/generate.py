# api/generate.py - MATPLOTLIB CACHE FIX
import os
import tempfile
from http.server import BaseHTTPRequestHandler
import json

# Configure matplotlib BEFORE importing it
os.environ['MPLCONFIGDIR'] = tempfile.mkdtemp()
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend for serverless
import matplotlib.pyplot as plt
import numpy as np
import io
import base64
import warnings
warnings.filterwarnings('ignore')

# Import the kolam algorithm
from kolam_algorithm_fixed import KolamDraw

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # Handle CORS
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            
            # Get request data
            content_length = int(self.headers.get('content-length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            # Extract parameters with defaults
            ND = int(data.get('ND', 19))
            sigmaref = float(data.get('sigmaref', 0.65))
            boundary_type = data.get('boundary_type', 'diamond')
            theme = data.get('theme', 'light')
            kolam_color = data.get('kolam_color')
            one_stroke = bool(data.get('one_stroke', False))
            
            # Validate parameters
            if ND % 2 == 0:
                raise ValueError('ND must be odd')
            if ND < 5:
                raise ValueError('ND must be >= 5')
            if not 0 <= sigmaref <= 1:
                raise ValueError('sigmaref must be between 0 and 1')
            
            # Generate Kolam
            result = self.generate_kolam_base64(
                ND, sigmaref, boundary_type, theme, kolam_color, one_stroke
            )
            
            # Send response
            self.wfile.write(json.dumps(result).encode())
            
        except Exception as e:
            error_response = {
                "success": False,
                "error": f"Generation failed: {str(e)}"
            }
            self.wfile.write(json.dumps(error_response).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def generate_kolam_base64(self, ND, sigmaref, boundary_type='diamond', theme='light', kolam_color=None, one_stroke=False):
        """Generate kolam and return as base64 encoded image - MATPLOTLIB CACHE FIXED"""
        
        try:
            # Set default colors based on boundary type
            default_colors = {
                'diamond': '#e377c2',
                'corners': '#1f77b4',
                'fish': '#ff7f0e',
                'waves': '#2ca02c',
                'fractal': '#9467bd',
                'organic': '#8c564b'
            }
            
            if kolam_color is None:
                kolam_color = default_colors.get(boundary_type, '#1f77b4')
            
            # Set theme colors
            bg_color = '#1a1a1a' if theme.lower() == 'dark' else 'white'
            
            # Create KolamDraw instance and generate pattern
            KD = KolamDraw(ND)
            KD.set_boundary(boundary_type)
            
            # Algorithm parameters - simplified for serverless
            Kp, Ki, ksh, Niter, Nthr = 0.01, 0.0001, 0.5, 20, 5  # Reduced iterations
            krRef = 1 - sigmaref
            
            # Generate gate matrix
            A2, F2, A2max, isx, ithx, ismax, Flag1, Flag2, krx2 = KD.Dice(krRef, Kp, Ki, Nthr)
            
            # Generate path with timeout protection
            max_attempts = 5  # Reduced for serverless
            for attempt in range(max_attempts):
                Ncx = KD.PathCount()
                Nx2x = int((ND + 1) / 2)
                Ncx, GM, GF = KD.IterFlipTestSwitch(ksh, Niter, 1, Nx2x)
                
                if Ncx > 50:  # Good enough for display
                    break
            
            # Generate the drawing path
            Ns = min((2 * (ND ** 2) + 1) * 5, 10000)  # Limit path length
            ijng, ne, ijngp = KD.XNextSteps(1, 1, 1, Ns)
            
            # Create matplotlib plot with cache fix
            plt.ioff()  # Turn off interactive mode
            fig, ax = plt.subplots(figsize=(8, 8), facecolor=bg_color, dpi=100)
            ax.set_facecolor(bg_color)
            
            # Transform coordinates for display
            if len(ijngp) > 1:
                ijngpx = (ijngp[:, 0] + ijngp[:, 1]) / 2
                ijngpy = (ijngp[:, 0] - ijngp[:, 1]) / 2
                
                # Plot the kolam pattern
                ax.plot(ijngpx[:-1], ijngpy[:-1], color=kolam_color, linewidth=2.0, alpha=0.9)
            
            # Set axis properties
            max_coord = ND + 5
            ax.set_xlim(-max_coord, max_coord)
            ax.set_ylim(-max_coord, max_coord)
            ax.set_aspect('equal')
            ax.axis('off')
            
            # Convert to base64
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', facecolor=bg_color,
                       bbox_inches='tight', pad_inches=0.1)
            plt.close(fig)  # Important: close figure to free memory
            plt.clf()       # Clear the current figure
            
            img_buffer.seek(0)
            img_base64 = base64.b64encode(img_buffer.read()).decode()
            
            return {
                'success': True,
                'image': f'data:image/png;base64,{img_base64}',
                'path_count': Ncx,
                'is_one_stroke': Ncx > 100
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Kolam generation failed: {str(e)}'
            }