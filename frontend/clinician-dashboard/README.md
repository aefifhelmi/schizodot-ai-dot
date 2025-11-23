# 🏥 DOMINO Clinician Dashboard

## Overview

Professional web dashboard for healthcare providers to view and analyze patient compliance data from the DOMINO system.

## Features

### 📊 Dashboard Statistics
- **Total Patients**: Unique patient count
- **Sessions Today**: Today's assessment sessions
- **Pending Reviews**: Completed sessions awaiting review
- **High Risk Alerts**: Patients flagged with high risk

### 🔍 Patient Session Management
- **Search**: Filter by Patient ID, Job ID, or date
- **Status Filters**: All, Completed, Processing, Failed
- **Sortable Table**: View all patient sessions
- **Export Data**: Download results as JSON

### 📋 Detailed Analysis View
For each patient session, clinicians can view:

1. **Patient Information**
   - Patient ID
   - Job ID
   - Analysis date/time
   - Processing time
   - Status

2. **Emotion Analysis**
   - Audio emotion detection (with confidence scores)
   - Facial emotion detection (with confidence scores)
   - All emotion scores breakdown

3. **Transcript**
   - Full text transcript of patient responses
   - Language code
   - Word count
   - Confidence level

4. **Clinical Summary (LLM Analysis)**
   - Emotional state assessment
   - Verbal content analysis
   - Medication adherence evaluation
   - Risk assessment (Low/Moderate/High)
   - AI-generated recommendations

5. **Medication Compliance**
   - Compliance score (%)
   - Protocol status
   - Phases completed (0-6)
   - Full detection data

6. **Raw Data**
   - Complete JSON response for technical review

## Quick Start

### 1. Ensure Backend is Running

```bash
# Backend should be running on port 8000
curl http://localhost:8000/api/v1/results/
```

### 2. Start Clinician Dashboard

```bash
cd clinician-webapp
python3 -m http.server 8080
```

### 3. Access Dashboard

Open in browser:
```
http://localhost:8080
```

## API Integration

The dashboard connects to the DOMINO backend API:

**Base URL**: `http://localhost:8000/api/v1`

**Endpoints Used**:
- `GET /results/` - Fetch all patient results
- `GET /results/job/{job_id}` - Fetch specific session
- `GET /jobs/{job_id}/status` - Check job status

## Technology Stack

- **Frontend**: HTML5, CSS3 (vanilla)
- **JavaScript**: ES6+
- **Fonts**: Inter (Google Fonts)
- **Icons**: SVG
- **Data Format**: JSON
- **Server**: Python HTTP Server (development)

## Dashboard Sections

### Stats Cards
- Real-time statistics updated every 30 seconds
- Color-coded by importance
- Clickable for detailed views

### Search & Filter
- Real-time search across all fields
- Multiple status filters
- Persistent filter state

### Results Table
- Patient ID
- Job ID (truncated)
- Date/Time
- Status badge
- Risk level badge
- Compliance indicator
- Action button (View Details)

### Detail Modal
- Full-screen overlay
- Scrollable content
- Organized sections
- JSON viewer for technical data
- Close on outside click

## Features by Role

### For Clinicians
- ✅ Quick patient overview
- ✅ Risk assessment at a glance
- ✅ Detailed clinical summaries
- ✅ Compliance tracking
- ✅ Export for records

### For Administrators
- ✅ System monitoring
- ✅ Session statistics
- ✅ Data export
- ✅ Technical debugging (raw JSON)

## Color Coding

### Status
- **Green**: Completed
- **Yellow**: Processing
- **Red**: Failed
- **Blue**: Queued

### Risk Level
- **Green**: Low risk
- **Yellow**: Moderate risk
- **Red**: High risk

### Compliance
- **✅**: Compliant (≥80%)
- **⚠️**: Partial (60-79%)
- **❌**: Non-compliant (<60%)

## Data Refresh

- **Auto-refresh**: Every 30 seconds
- **Manual refresh**: Click refresh icon
- **On-demand**: View Details always fetches latest

## Export Format

Exported JSON includes:
- All filtered results
- Complete data structure
- Timestamp in filename
- Ready for analysis tools

## Browser Support

- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

## Responsive Design

- Desktop: Full table view
- Tablet: Stacked cards
- Mobile: Simplified layout

## Security Notes

1. **Local Development**: Currently configured for localhost
2. **Production**: Update API_BASE_URL in app.js
3. **CORS**: Backend must allow clinician dashboard origin
4. **Authentication**: Add auth layer before production use

## Troubleshooting

### Dashboard shows "Loading..."
- ✅ Check backend is running on port 8000
- ✅ Verify CORS is enabled
- ✅ Check browser console for errors

### No data displayed
- ✅ Ensure patients have completed sessions
- ✅ Check API endpoint returns data
- ✅ Verify results table structure matches expected format

### Modal won't open
- ✅ Check browser console for JavaScript errors
- ✅ Verify result object structure
- ✅ Clear browser cache

## Development

### File Structure
```
clinician-webapp/
├── index.html      # Main dashboard page
├── styles.css      # All styling
├── app.js          # Application logic
└── README.md       # This file
```

### Customization
1. **Colors**: Edit `:root` variables in styles.css
2. **API URL**: Change API_BASE_URL in app.js
3. **Refresh interval**: Modify setInterval in app.js
4. **Table columns**: Edit renderTable() in app.js

## Ports

- **Patient Portal**: 3000
- **Backend API**: 8000
- **Proto.py**: 5002
- **Clinician Dashboard**: 8080

## Future Enhancements

- [ ] User authentication
- [ ] Real-time notifications
- [ ] Patient history timeline
- [ ] Comparative analytics
- [ ] PDF report generation
- [ ] Advanced filtering options
- [ ] Chart visualizations
- [ ] Multi-language support

## Support

For issues or questions:
1. Check browser console for errors
2. Verify backend connectivity
3. Review API response format
4. Check CORS configuration

## License

Part of the DOMINO system - Direct Object Medication Intake Neuro Output

---

**Version**: 1.0.0  
**Last Updated**: November 2025
