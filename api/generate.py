# api/generate.py - FIXED VERSION
from http.server import BaseHTTPRequestHandler
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend for serverless
import matplotlib.pyplot as plt
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
            
            # Generate Kolam using FIXED algorithm
            result = self.generate_kolam_base64(
                ND, sigmaref, boundary_type, theme, kolam_color, one_stroke
            )
            
            # Send response
            self.wfile.write(json.dumps(result).encode())
            
        except Exception as e:
            error_response = {
                "success": False,
                "error": str(e)
            }
            self.wfile.write(json.dumps(error_response).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def generate_kolam_base64(self, ND, sigmaref, boundary_type='diamond', theme='light', kolam_color=None, one_stroke=False):
        """Generate kolam and return as base64 encoded image - FIXED VERSION"""
        
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
            
            # Algorithm parameters
            if one_stroke:
                Kp, Ki, ksh, Niter, Nthr = 0.01, 0.0001, 0.5, 80, 10
                max_attempts = 100
            else:
                Kp, Ki, ksh, Niter, Nthr = 0.01, 0.0001, 0.5, 40, 10
                max_attempts = 20
            
            krRef = 1 - sigmaref
            
            # Generate gate matrix
            A2, F2, A2max, isx, ithx, ismax, Flag1, Flag2, krx2 = KD.Dice(krRef, Kp, Ki, Nthr)
            
            # Optimize path
            best_ncx = 0
            for attempt in range(max_attempts):
                Ncx = KD.PathCount()
                Nx2x = int((ND + 1) / 2)
                Ncx, GM, GF = KD.IterFlipTestSwitch(ksh, Niter, 1, Nx2x)
                
                if Ncx > best_ncx:
                    best_ncx = Ncx
                
                # For one-stroke, try to get a single path
                if one_stroke and Ncx >= (2 * (ND ** 2) + 1) * 4:
                    break
                elif not one_stroke and Ncx > 100:
                    break
            
            # Generate the path
            Ns = (2 * (ND ** 2) + 1) * 5
            ijng, ne, ijngp = KD.XNextSteps(1, 1, 1, Ns)
            
            # Create the plot
            fig, ax = plt.subplots(figsize=(10, 10), facecolor=bg_color, dpi=150)
            ax.set_facecolor(bg_color)
            
            # Transform coordinates for display
            ijngpx = (ijngp[:, 0] + ijngp[:, 1]) / 2
            ijngpy = (ijngp[:, 0] - ijngp[:, 1]) / 2
            
            # Plot the kolam pattern
            ax.plot(ijngpx[:-1], ijngpy[:-1], color=kolam_color, linewidth=2.0, alpha=0.9)
            
            # Set axis properties
            max_coord = int(np.max(np.abs(ijngp))) + 2
            ax.set_xlim(-max_coord-1, max_coord+1)
            ax.set_ylim(-max_coord-1, max_coord+1)
            ax.set_aspect('equal')
            ax.axis('off')
            plt.tight_layout()
            
            # Convert to base64
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', facecolor=bg_color,
                       bbox_inches='tight', pad_inches=0.1)
            img_buffer.seek(0)
            img_base64 = base64.b64encode(img_buffer.read()).decode()
            plt.close(fig)
            
            return {
                'success': True,
                'image': f'data:image/png;base64,{img_base64}',
                'path_count': best_ncx,
                'is_one_stroke': best_ncx >= (2 * (ND ** 2) + 1) * 4
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Kolam generation failed: {str(e)}'
            }