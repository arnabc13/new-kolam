// public/app.js
// Kolam Pattern Generator App
// ============================================================================
// 🔧 CONFIGURATION SECTION - UPDATE FOR VERCEL DEPLOYMENT  
// ============================================================================
const CONFIG = {
    API_BASE_URL: '', // Empty for same domain (Vercel functions)
    API_ENDPOINTS: {
        GENERATE: '/api/generate',
        HEALTH: '/api/health'
    }
};
// ============================================================================

class KolamApp {
    constructor() {
        // Default color schemes for each boundary type
        this.defaultColors = {
            diamond: '#e377c2',
            corners: '#1f77b4',
            fish: '#ff7f0e',
            waves: '#2ca02c',
            fractal: '#9467bd',
            organic: '#8c564b'
        };
        
        this.currentImageData = null;
        this.isGenerating = false;
        
        this.initializeElements();
        this.bindEvents();
        this.updateInitialValues();
    }

    initializeElements() {
        // Form elements
        this.form = document.getElementById('kolamForm');
        this.ndSlider = document.getElementById('ndSlider');
        this.ndValue = document.getElementById('ndValue');
        this.sigmaSlider = document.getElementById('sigmaSlider');
        this.sigmaValue = document.getElementById('sigmaValue');
        this.boundaryType = document.getElementById('boundaryType');
        this.kolamColor = document.getElementById('kolamColor');
        this.colorValue = document.getElementById('colorValue');
        this.oneStroke = document.getElementById('oneStroke');
        this.themeRadios = document.querySelectorAll('input[name="theme"]');
        
        // Buttons
        this.generateBtn = document.getElementById('generateBtn');
        this.downloadBtn = document.getElementById('downloadBtn');
        
        // Preview area
        this.previewArea = document.getElementById('previewArea');
    }

    bindEvents() {
        // Slider events
        this.ndSlider.addEventListener('input', (e) => this.updateNDValue(e.target.value));
        this.sigmaSlider.addEventListener('input', (e) => this.updateSigmaValue(e.target.value));
        
        // Boundary type change
        this.boundaryType.addEventListener('change', (e) => this.updateDefaultColor(e.target.value));
        
        // Color picker
        this.kolamColor.addEventListener('input', (e) => this.updateColorValue(e.target.value));
        
        // Form submission
        this.form.addEventListener('submit', (e) => this.handleGenerate(e));
        
        // Generate button
        this.generateBtn.addEventListener('click', (e) => this.handleGenerate(e));
        
        // Download button
        this.downloadBtn.addEventListener('click', () => this.handleDownload());
        
        // Theme change
        this.themeRadios.forEach(radio => {
            radio.addEventListener('change', () => this.updateTheme());
        });
    }

    updateNDValue(value) {
        this.ndValue.textContent = value;
    }

    updateSigmaValue(value) {
        this.sigmaValue.textContent = value;
    }

    updateDefaultColor(boundaryType) {
        const defaultColor = this.defaultColors[boundaryType] || '#1f77b4';
        this.kolamColor.value = defaultColor;
        this.updateColorValue(defaultColor);
    }

    updateColorValue(color) {
        this.colorValue.textContent = color;
    }

    updateInitialValues() {
        this.updateNDValue(this.ndSlider.value);
        this.updateSigmaValue(this.sigmaSlider.value);
        this.updateDefaultColor(this.boundaryType.value);
    }

    updateTheme() {
        const selectedTheme = document.querySelector('input[name="theme"]:checked').value;
        document.body.setAttribute('data-theme', selectedTheme);
    }

    async handleGenerate(e) {
        e.preventDefault();
        if (this.isGenerating) return;

        const params = this.getFormParameters();
        await this.generateKolam(params);
    }

    getFormParameters() {
        const selectedTheme = document.querySelector('input[name="theme"]:checked')?.value || 'light';
        return {
            ND: parseInt(this.ndSlider.value),
            sigmaref: parseFloat(this.sigmaSlider.value),
            boundary_type: this.boundaryType.value,
            theme: selectedTheme,
            kolam_color: this.kolamColor.value,
            one_stroke: this.oneStroke.checked
        };
    }

    async generateKolam(params) {
        try {
            this.setGenerating(true);
            
            // Show loading state
            this.previewArea.innerHTML = `
                <div class="loading">
                    <div class="loading-spinner"></div>
                    <p>Generating kolam pattern...</p>
                </div>
            `;

            // API CALL TO VERCEL SERVERLESS FUNCTION
            console.log(`Making API call to: ${CONFIG.API_BASE_URL}${CONFIG.API_ENDPOINTS.GENERATE}`);
            
            const response = await fetch(`${CONFIG.API_BASE_URL}${CONFIG.API_ENDPOINTS.GENERATE}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(params)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();

            if (result.success) {
                this.displayKolam(result);
                this.currentImageData = result.image;
                this.downloadBtn.disabled = false;
            } else {
                throw new Error(result.error || 'Failed to generate kolam');
            }

        } catch (error) {
            console.error('Error generating kolam:', error);
            this.showError(`Failed to generate kolam: ${error.message}`);
        } finally {
            this.setGenerating(false);
        }
    }

    displayKolam(result) {
        const img = document.createElement('img');
        img.src = result.image;
        img.alt = 'Generated Kolam Pattern';
        img.style.maxWidth = '100%';
        img.style.height = 'auto';
        img.style.borderRadius = '8px';

        const info = document.createElement('div');
        info.className = 'kolam-info';
        info.innerHTML = `
            <p><strong>Paths:</strong> ${result.path_count}</p>
            <p><strong>Type:</strong> ${result.is_one_stroke ? 'One-stroke' : 'Multi-stroke'}</p>
        `;

        this.previewArea.innerHTML = '';
        this.previewArea.appendChild(img);
        this.previewArea.appendChild(info);
    }

    showError(message) {
        this.previewArea.innerHTML = `
            <div class="error-message" style="padding: 20px; text-align: center; border: 2px dashed #ff6b6b; border-radius: 8px; background: #ffe0e0;">
                <h3 style="color: #d63031; margin-top: 0;">Generation Failed</h3>
                <p style="color: #2d3436;">${message}</p>
                <p style="color: #636e72; font-size: 0.9em;">
                    <strong>Troubleshooting:</strong><br>
                    1. Check internet connection<br>
                    2. Try refreshing the page<br>
                    3. Verify all parameters are valid
                </p>
            </div>
        `;
    }

    setGenerating(isGenerating) {
        this.isGenerating = isGenerating;
        this.generateBtn.disabled = isGenerating;
        this.generateBtn.textContent = isGenerating ? '🎨 Generating...' : '🎨 Generate Kolam';
    }

    handleDownload() {
        if (!this.currentImageData) {
            alert('No image to download. Please generate a kolam pattern first.');
            return;
        }

        const params = this.getFormParameters();
        const filename = `kolam-${params.boundary_type}-${params.ND}-${Date.now()}.png`;
        const link = document.createElement('a');
        link.download = filename;
        link.href = this.currentImageData;
        link.click();
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('🎨 Initializing Kolam Generator App...');
    console.log(`📡 Backend configured for: ${CONFIG.API_BASE_URL || 'same domain (Vercel functions)'}`);
    new KolamApp();
});

// Test backend connection on load
document.addEventListener('DOMContentLoaded', async () => {
    try {
        console.log(`🔍 Testing backend connection to: ${CONFIG.API_BASE_URL}${CONFIG.API_ENDPOINTS.HEALTH}`);
        const response = await fetch(`${CONFIG.API_BASE_URL}${CONFIG.API_ENDPOINTS.HEALTH}`, {
            method: 'GET'
        });

        if (response.ok) {
            const result = await response.json();
            console.log('✅ Backend connection successful!', result);
        } else {
            console.warn('⚠️ Backend responded with error:', response.status);
        }

    } catch (error) {
        console.error('❌ Backend not accessible:', error.message);
        console.log('🔧 Troubleshooting steps:');
        console.log('1. Check if Vercel functions are deployed');
        console.log('2. Verify the app is accessed via the correct domain');
        console.log('3. Check for any function errors in Vercel dashboard');
    }
});