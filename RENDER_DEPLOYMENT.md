# Render Deployment Configuration Guide

## 📋 Deployment Steps

### 1. Push to GitHub
```bash
git add .
git commit -m "Add Render deployment configuration"
git push origin main
```

### 2. Deploy Backend (Python Flask API)

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository: `prashant847/4WAY.AI`
4. Configure:
   - **Name**: `traffic-backend-api`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn --bind 0.0.0.0:$PORT app:app`
   - **Instance Type**: Free

5. Add Environment Variables:
   - `PYTHON_VERSION` = `3.10.11`
   - `FLASK_ENV` = `production`
   - `GEMINI_API_KEY` = `your_gemini_api_key_here`
   - `PORT` = `5000` (auto-set by Render)

6. Click "Create Web Service"

### 3. Deploy Frontend (Static Site)

1. Click "New +" → "Static Site"
2. Connect same repository: `prashant847/4WAY.AI`
3. Configure:
   - **Name**: `traffic-dashboard`
   - **Build Command**: Leave empty
   - **Publish Directory**: `.`
   - **Auto-Deploy**: Yes

4. After deployment, get your backend URL and update:
   - Copy your backend URL: `https://traffic-backend-api.onrender.com`
   - Update `script.js` line 3 with your actual backend URL

### 4. Important Configuration

#### Backend CORS Settings
Your backend `app.py` already has CORS enabled. Verify it allows your frontend domain:
```python
CORS(app)  # This allows all origins in development
```

For production, update to specific domain:
```python
CORS(app, origins=['https://your-frontend-domain.onrender.com'])
```

#### Static Files & Videos
- Video files in `/videos/` folder will be deployed with static site
- If videos are large (>100MB), consider using cloud storage:
  - Cloudflare R2 (Free tier available)
  - AWS S3
  - Google Cloud Storage

### 5. Environment Variables Reference

**Backend (.env or Render dashboard):**
```env
FLASK_ENV=production
GEMINI_API_KEY=your_api_key_here
PORT=5000
DEBUG=False
```

**Frontend (Render Environment Variables):**
```env
API_BASE_URL=https://traffic-backend-api.onrender.com/api
```

## 🔧 Troubleshooting

### Backend Issues:
- Check Render logs: Dashboard → Your Service → Logs
- Verify Python version: Should be 3.10+
- Check memory usage: Free tier has 512MB limit
- YOLO model might be too large for free tier - consider lighter model

### Frontend Issues:
- Check API URL in browser console
- Verify CORS headers from backend
- Check video file paths and sizes

### Performance Optimization:
1. Use lightweight YOLO model (yolov8n.pt)
2. Reduce video processing frequency
3. Implement caching for API responses
4. Use CDN for static assets

## 📊 Monitoring

- **Backend Health Check**: `https://your-backend.onrender.com/api/health`
- **Frontend**: `https://your-frontend.onrender.com`
- **Logs**: Available in Render dashboard

## 🚀 Auto-Deployment

With `render.yaml` in your repository:
- Push to `main` branch → Automatic deployment
- Pull requests → Preview deployments (Pro plan)

## 💡 Free Tier Limitations

- Backend spins down after 15 minutes of inactivity
- First request after spin-down takes ~30 seconds
- 512MB RAM limit
- 750 hours/month free

## 🔐 Security

1. Never commit `.env` file (already in `.gitignore`)
2. Use Render's environment variables for secrets
3. Add rate limiting for API endpoints
4. Use HTTPS (automatic with Render)

## 📱 Custom Domain (Optional)

1. Go to your service → Settings → Custom Domain
2. Add your domain
3. Update DNS records as instructed
4. SSL certificate auto-configured

---

Need help? Check Render documentation: https://render.com/docs
