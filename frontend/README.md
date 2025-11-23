# Frontend Applications

This directory contains all web-based user interfaces for the DOMINO platform.

## Applications

### 1. Patient Portal (`patient-portal/`)
**Purpose**: Interface for patients to complete check-ins and assessments

**Features**:
- Patient ID entry
- Clinical questionnaire
- Video recording for emotion analysis
- Medication compliance verification (6-phase protocol)
- Session completion and summary

**Access**: http://localhost:3000/index-new.html

**Key Files**:
- `index-new.html` - Main application interface
- `app-new.js` - Application logic and API integration
- `styles-new.css` - Modern UI styling

### 2. Clinician Dashboard (`clinician-dashboard/`)
**Purpose**: Interface for clinicians to review patient assessments

**Features**:
- Auto-loading patient list (real-time updates every 30s)
- Patient assessment visualization
- Emotion analysis breakdown (audio, facial, multimodal)
- Risk assessment display
- Clinical recommendations
- Full session data review

**Access**: http://localhost:3001/index-new.html

**Key Files**:
- `index-new.html` - Dashboard interface
- `app-new.js` - Data fetching and display logic
- `styles-new.css` - Professional clinical UI styling

### 3. Legacy (`legacy/`)
Contains older versions of frontends for reference

## Development

### Running Patient Portal
```bash
cd patient-portal
python -m http.server 3000
# Or use any static server
```

### Running Clinician Dashboard
```bash
cd clinician-dashboard
python -m http.server 3001
```

## Architecture

Both applications are:
- **Framework-free**: Pure HTML/CSS/JavaScript
- **API-driven**: Connect to backend at `http://localhost:8000/api/v1`
- **Responsive**: Work on desktop and tablet devices
- **Real-time**: Auto-refresh and live updates

## API Integration

Both frontends communicate with:
- **Backend API**: Video upload, results retrieval
- **Emotion Service**: Audio/facial emotion analysis
- **Pill Compliance Service**: Medication verification

## Styling Guidelines

- **Design System**: Cyberpunk/tech aesthetic
- **Color Palette**: Dark navy background, cyan accents
- **Typography**: IBM Plex Mono (monospace), Epilogue (headings)
- **Animations**: Subtle glows and transitions
- **Components**: Cards, gradients, technical UI elements

## Testing

1. Start backend services:
   ```bash
   docker-compose up -d
   ```

2. Open patient portal in browser
3. Complete full check-in flow
4. Open clinician dashboard
5. Verify patient data displays correctly

## File Structure

```
frontend/
├── patient-portal/
│   ├── index-new.html      # Main interface
│   ├── app-new.js          # Application logic
│   ├── styles-new.css      # Styling
│   └── README.md           # Portal-specific docs
│
├── clinician-dashboard/
│   ├── index-new.html      # Dashboard interface
│   ├── app-new.js          # Data handling
│   ├── styles-new.css      # Clinical styling
│   └── README.md           # Dashboard-specific docs
│
└── legacy/
    └── [old versions]
```

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Common Issues

**Problem**: API calls fail
**Solution**: Ensure backend is running on port 8000

**Problem**: Video recording not working
**Solution**: Grant camera/microphone permissions

**Problem**: Compliance iframe not loading
**Solution**: Ensure pill compliance service is running on port 5001

## Future Enhancements

- [ ] Mobile app versions
- [ ] Offline mode support
- [ ] Multi-language support
- [ ] Accessibility improvements (WCAG 2.1 AA)
