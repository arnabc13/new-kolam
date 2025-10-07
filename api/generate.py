# api/generate.py - WITH EMBEDDED SIMPLE ALGORITHM
import os
import tempfile
from http.server import BaseHTTPRequestHandler
import json

# Configure matplotlib BEFORE importing it
os.environ['MPLCONFIGDIR'] = tempfile.mkdtemp()
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import io
import base64
import warnings
warnings.filterwarnings('ignore')

class SimpleKolamDraw:
    """Simplified Kolam generator for serverless deployment"""
    
    def __init__(self, ND):
        self.ND = ND
        self.boundary_type = 'diamond'
    
    def set_boundary(self, boundary_type):
        self.boundary_type = boundary_type
    
    def generate_simple_pattern(self):
        """Generate a simple geometric pattern"""
        ND = self.ND
        
        # Create simple grid pattern
        angles = np.linspace(0, 4 * np.pi, ND * 8)
        radius = np.linspace(1, ND/2, len(angles))
        
        # Generate spiral pattern
        x = radius * np.cos(angles) 
        y = radius * np.sin(angles)
        
        # Add boundary-specific modifications
        if self.boundary_type == 'diamond':
            x = x * (1 + 0.3 * np.sin(4 * angles))
            y = y * (1 + 0.3 * np.cos(4 * angles))
        elif self.boundary_type == 'fish':
            x = x * (1 + 0.5 * np.sin(2 * angles))
        elif self.boundary_type == 'waves':
            y = y + 0.5 * np.sin(8 * angles)
        elif self.boundary_type == 'fractal':
            x = x + 0.2 * np.sin(6 * angles)
            y = y + 0.2 * np.cos(6 * angles)
        elif self.boundary_type == 'organic':
            x = x * (1 + 0.4 * np.sin(3 * angles))
            y = y * (1 + 0.4 * np.cos(5 * angles))
        
        return np.column_stack([x, y])

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
            
            # Extract parameters
            ND = int(data.get('ND', 19))
            sigmaref = float(data.get('sigmaref', 0.65))
            boundary_type = data.get('boundary_type', 'diamond')
            theme = data.get('theme', 'light')
            kolam_color = data.get('kolam_color')
            one_stroke = bool(data.get('one_stroke', False))
            
            # Generate Kolam
            result = self.generate_kolam_base64(
                ND, sigmaref, boundary_type, theme, kolam_color, one_stroke
            )
            
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
        """Generate kolam using embedded simple algorithm"""
        
        try:
            # Set default colors
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
            
            bg_color = '#1a1a1a' if theme.lower() == 'dark' else 'white'
            
            # Generate pattern using simplified algorithm
            kolam_gen = SimpleKolamDraw(ND)
            kolam_gen.set_boundary(boundary_type)
            pattern_points = kolam_gen.generate_simple_pattern()
            
            # Create plot
            plt.ioff()
            fig, ax = plt.subplots(figsize=(8, 8), facecolor=bg_color, dpi=100)
            ax.set_facecolor(bg_color)
            
            # Plot pattern
            ax.plot(pattern_points[:, 0], pattern_points[:, 1], 
                   color=kolam_color, linewidth=2.5, alpha=0.9)
            
            # Set axis
            max_coord = ND/2 + 2
            ax.set_xlim(-max_coord, max_coord)
            ax.set_ylim(-max_coord, max_coord)
            ax.set_aspect('equal')
            ax.axis('off')
            
            # Convert to base64
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', facecolor=bg_color,
                       bbox_inches='tight', pad_inches=0.1)
            plt.close(fig)
            plt.clf()
            
            img_buffer.seek(0)
            img_base64 = base64.b64encode(img_buffer.read()).decode()
            
            return {
                'success': True,
                'image': f'data:image/png;base64,{img_base64}',
                'path_count': len(pattern_points),
                'is_one_stroke': True
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Pattern generation failed: {str(e)}'
            }