# Automation Dashboard

A comprehensive social media automation platform with AI-powered content generation and auto-reply capabilities.

---

## Features

### AI Auto-Reply System
The platform now includes an intelligent auto-reply system that allows you to:

1. **Select Specific Posts**: Choose which posts from your app should have auto-reply enabled
2. **AI-Powered Responses**: Uses Groq AI to generate contextual, natural responses to comments
3. **Custom Templates**: Optionally provide a response template to guide the AI
4. **Instant Activation**: Enable/disable auto-reply for selected posts instantly

#### How to Use AI Auto-Reply:

1. **Connect Facebook**: First, connect your Facebook account and select a page
2. **Create Posts**: Make some posts using the AI Generate or Manual Post features
3. **Configure Auto-Reply**:
   - Click the "Settings" button in the AI Auto-Reply section
   - Select the posts you want to enable auto-reply for (use "Select All" or choose individually)
   - Optionally add a custom response template
   - Click "Enable" to activate auto-reply

4. **How It Works**:
   - When someone comments on your selected posts, the AI will automatically generate a contextual response
   - The AI uses the comment content and your optional template to create natural, engaging replies
   - Responses are posted automatically to Facebook

#### Technical Implementation:

- **Backend**: Uses FastAPI with SQLAlchemy for data persistence
- **AI Service**: Integrates with Groq API for natural language generation
- **Facebook Integration**: Direct API integration for posting replies
- **Database**: Stores automation rules and post selections in PostgreSQL

### Other Features

- **AI Content Generation**: Generate posts using Groq AI
- **Image Generation**: Create AI-generated images with Stability AI
- **Scheduled Posting**: Schedule posts with various frequencies
- **Multi-Platform Support**: Facebook and Instagram integration
- **Google Drive Integration**: Upload media from Google Drive
- **Manual Selection**: You can also select the image or video manually from your system


---

## Prerequisites

| Part      | Version | Notes                           |
|-----------|---------|--------------------------------|
| Python    | 3.10+   | Back-end                       |
| Node.js   | 18+     | Front-end (React + Vite)       |
| Git       | latest  | clone / version control        |
| (Optional)| PostgreSQL / Redis | switch DB / caching |

---

## Quick-start (local dev)

```bash
# 1. Clone
$ git clone https://github.com/<your-org>/automation-dashboard.git
$ cd automation-dashboard

# 2. Back-end – Python virtualenv
$ python -m venv .venv && source .venv/Scripts/activate   # Windows: .venv\Scripts\activate
$ pip install -r backend/requirements.txt

# 3. Front-end – React
$ cd frontend && npm install              # or yarn
$ cd ..                                   # back to repo root

# 4. Create a .env file (see below)
$ copy .env.sample .env   # Windows        (or)   cp .env.sample .env

# 5. Launch services (in two terminals)
## API
$ uvicorn backend.app.main:app --reload
## Front-end
$ cd frontend && npm start
```

### .env file

A **.env** file is **NOT** committed to git; you must create it locally and share it securely with teammates.  
The application root expects the file `./.env` (same folder as this README).

```dotenv
# === General ===
ENVIRONMENT=development
DEBUG=True

# === Database ===
DATABASE_URL=sqlite:///./automation_dashboard.db  # dev uses SQLite; override in prod

# === JWT ===
SECRET_KEY=change-me-please

# === Facebook ===
FACEBOOK_APP_ID=123456789012345
FACEBOOK_APP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# === Instagram ===
INSTAGRAM_APP_ID=123456789012345
INSTAGRAM_APP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# === Groq ===
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

> 🔒  **Never commit real secrets to git.**  `.env` is listed in `.gitignore` by default.

---

## Social-media OAuth configuration

Facebook & Instagram will refuse login with the error **"Feature Unavailable: Facebook Login is currently unavailable for this app"** unless each user is authorised.  Follow these steps **for every teammate or test account**:

1. **Facebook Developer Portal** → Your App → *Roles*.
   * Under **Testers**, click *Add* and enter your colleague's Facebook account email/username.
   * They will receive an invitation – they **must accept** it.
2. Repeat for **Instagram Testers** under *Instagram Basic Display* if you use Instagram integration.
3. Keep the app in **Development** mode while testing, or complete Facebook App Review if you need **Live** mode.
4. Ensure your Valid OAuth Redirect URIs match your local backend, e.g.
   * `http://localhost:8000/api/auth/facebook/callback`
5. After the tester accepts the invite, have them log out & log back in – the OAuth dialog will appear normally.

> If you still see "Feature Unavailable", double-check that:
> * The tester accepted the invitation (check under *Roles* → *Testers* → *Invited* vs *Added*).
> * The Facebook account you're using matches the invited email.
> * The app is not in Live mode without required approvals.

---

## Scripts

| Command                           | Description                   |
|----------------------------------|-------------------------------|
| `uvicorn backend.app.main:app --reload` | Start FastAPI (hot-reload) |
| `alembic revision --autogenerate` | Create DB migration           |
| `npm start` (inside `frontend/`)  | React dev server              |

---

## Production deployment (brief)

1. Build front-end: `cd frontend && npm run build` → files land in `frontend/build/`.
2. Serve static assets via Nginx / CDN; point API to a gunicorn/uvicorn server.
3. Use Postgres instead of SQLite; set `DATABASE_URL` accordingly.
4. Store secrets in a managed secret vault or environment variables (e.g., GitHub Actions secrets, Docker secrets, AWS SSM).

---

## Troubleshooting

| Problem                                   | Fix                                                          |
|-------------------------------------------|--------------------------------------------------------------|
| *Feature Unavailable* in Facebook OAuth   | Add the account as **Tester** in FB Developer portal, accept invite, check redirect URIs. |
| 401 / "Not authenticated" errors          | Verify `SECRET_KEY` matches in back-end & front-end env vars. |
| DB errors with Postgres                   | Update `DATABASE_URL` and run `alembic upgrade head`.        |

---

## Contributing
Pull requests are welcome! Please open an issue first to discuss changes you wish to make.

## License
MIT © 2024 Your Name 


