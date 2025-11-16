# Digital Inspector

Web application for automatic detection and analysis of signatures, stamps, and QR codes on documents.

## 🎯 Features

- **Signature Recognition** - Detect handwritten signatures
- **Stamp Detection** - Find round and rectangular organizational stamps
- **QR Code Scanning** - Detect and decode QR codes
- **Results Visualization** - Interactive display of detected elements
- **Data Export** - Save results in JSON format
- **Modern UI** - Clean and responsive web interface

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/Y-not-devs/phototype-innovate-x.git
cd phototype-innovate-x

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### Run Application

```bash
python app.py
```

Open browser at `http://localhost:5000`

## 💡 Usage

1. **Upload Document** - Drag & drop image or click to select file
2. **Run Analysis** - Click "Analyze" button to detect objects
3. **View Results** - Review detected elements with coordinates and confidence
4. **Export Data** - Save results in JSON for further processing

## 📡 API Endpoints

### POST `/api/analyze`

Analyzes uploaded image and returns detected objects.

**Request:**

- Content-Type: `multipart/form-data`
- Body: `image` (JPEG/PNG file)

**Response (200):**

```json
{
  "success": true,
  "timestamp": "2025-11-15T10:30:00.000Z",
  "image_dimensions": { "width": 1920, "height": 1080 },
  "detections": [
    {
      "type": "signature",
      "label": "Signature",
      "confidence": 0.953,
      "bounding_box": { "x": 0.245, "y": 0.678, "width": 0.156, "height": 0.089 }
    }
  ],
  "summary": {
    "total_detections": 3,
    "signatures": 1,
    "stamps": 1,
    "qr_codes": 1
  }
}
```

**Detection Types:**

- `signature` - Handwritten signatures
- `stamp` - Round and rectangular stamps
- `qr-code` - QR codes

**Coordinates:** Normalized (0.0-1.0) relative to image dimensions.

### GET `/api/health`

Health check endpoint.

**Response:** `{ "status": "healthy", "message": "Digital Inspector API is running" }`

## 🔧 Technology Stack

**Frontend:** HTML5 Canvas, CSS3 (dark theme), Vanilla JavaScript

**Backend:** Python Flask, OpenCV, NumPy

## 📋 Project Structure

```text
phototype-innovate-x/
├── app.py                 # Flask backend server
├── requirements.txt       # Python dependencies
├── static/
│   ├── styles.css        # Dark theme styling
│   └── script.js         # Client-side logic
└── templates/
    └── index.html        # Main page
```

## 🐳 Docker Deployment

```dockerfile
FROM python:3.13-slim
WORKDIR /app
RUN apt-get update && apt-get install -y libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "app.py"]
```

```bash
docker build -t digital-inspector .
docker run -p 5000:5000 digital-inspector
```

## 🌐 Production Deployment

### Using Gunicorn

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Nginx Configuration

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /static {
        alias /path/to/phototype-innovate-x/static;
    }
    
    client_max_body_size 16M;
}
```

## 🔐 Security Recommendations

- Disable debug mode in production: `app.run(debug=False)`
- Use environment variables for secrets
- Limit file upload size (default: 16MB)
- Enable HTTPS/SSL
- Configure CORS properly: `CORS(app, origins=['https://your-domain.com'])`
- Add rate limiting with `flask-limiter`

## 🧪 API Usage Examples

### JavaScript

```javascript
const formData = new FormData();
formData.append('image', fileInput.files[0]);

const response = await fetch('/api/analyze', {
    method: 'POST',
    body: formData
});

const data = await response.json();
console.log(data.detections);
```

### Python

```python
import requests

with open('document.jpg', 'rb') as f:
    files = {'image': f}
    response = requests.post('http://localhost:5000/api/analyze', files=files)

data = response.json()
print(data['detections'])
```

### cURL

```bash
curl -X POST -F "image=@document.jpg" http://localhost:5000/api/analyze
```

## 🆘 Troubleshooting

**Port already in use:**

```bash
netstat -ano | findstr :5000  # Find PID
taskkill /PID <pid> /F         # Kill process
```

**OpenCV issues:**

```bash
pip uninstall opencv-python
pip install opencv-python-headless
```

**Installation errors:**

```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

## 🎨 Design Features

This project focuses on creating a modern, user-friendly interface for document analysis:

- **Dark Theme** - Modern dark color scheme with gradient accents
- **Responsive Design** - Works seamlessly on desktop, tablet, and mobile
- **Drag & Drop** - Intuitive file upload with visual feedback
- **Interactive Canvas** - Real-time visualization of detected objects
- **Smooth Animations** - Polished transitions and hover effects
- **Color-Coded Results** - Easy identification of different object types
- **Clean Typography** - Readable and professional interface

## 🔮 Future Enhancements

- Real Computer Vision model integration
- PDF document support
- Batch processing for multiple files
- Advanced detection settings
- Analysis history
- Document comparison
- Dark/light theme toggle
- Mobile app version

## 📝 Notes

- Current version uses mock detection for demonstration
- Replace `generate_mock_detections()` with real CV model
- Maximum file size: 16MB
- Supported formats: JPEG, PNG

---

**Developed for construction document verification automation** 🏗️
