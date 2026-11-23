# Exam Prep Tracker

A Flask web app to track exam preparation progress with:
- User registration and login
- Subject/topic tracking with Prep % and Hopefull %
- Circular progress meters
- Positive affirmations that rotate every 5 minutes
- Exam logo upload
- Exam date countdown (days to go)
- Preparation-based suggestions
- Visitor counter

## Local Setup

```bash
cd /home/nanopore/todo_app
pip install -r requirements.txt
python app.py
```

Open http://localhost:5000 in your browser.

## Deploy to PythonAnywhere

1. Sign up at https://www.pythonanywhere.com
2. Open a Bash console
3. Clone the repo:
   ```bash
   git clone https://github.com/chau-mau/hope.git
   cd hope
   ```
4. Create a virtual environment and install dependencies:
   ```bash
   mkvirtualenv --python=/usr/bin/python3.8 hope-env
   pip install -r requirements.txt
   ```
5. Go to **Web** tab → **Add a new web app** → Select **Manual configuration** → **Python 3.8**
6. In the WSGI configuration file, set:
   ```python
   import sys
   sys.path.insert(0, '/home/YOUR_USERNAME/hope')
   from app import app as application
   ```
   Or simply point it to the provided `wsgi.py` file.
7. Set the source code directory to `/home/YOUR_USERNAME/hope`
8. Set the working directory to `/home/YOUR_USERNAME/hope`
9. Set the virtualenv to `hope-env`
10. Reload the web app
11. Visit `https://YOUR_USERNAME.pythonanywhere.com`

## Deploy to Render (easiest)

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/chau-mau/hope)

1. Click the **Deploy to Render** button above
2. Sign up or log in to Render (you can use GitHub login)
3. Give the service a name (default: `hope`)
4. Click **Create Web Service**
5. Render will build and deploy automatically
6. Visit the URL shown on the dashboard

## Environment Variables

- `SECRET_KEY` — Flask secret key (set a fixed value for production)
- `FLASK_DEBUG` — Set to `true` only for local development
