# Telegram Personal Assistant & Services Bot 🤖

A lightweight, asynchronous Telegram bot designed to automate client introductions, showcase your freelance services and portfolio, present pricing tiers, answer questions with intelligent keyword matching, and connect clients directly with you.

---

## 🚀 Features

- **Interactive Main Menu**: Quick access to services, pricing, contact details, and direct messaging.
- **Dynamic Services & Portfolio**: Service descriptions, deliverables, turnaround times, and rates loaded dynamically from `services.json`.
- **Pricing & Rates Overview**: Consolidated view of all your services and pricing tiers with quick action buttons.
- **Intelligent Keyword Matching**: Detects client intent from free-form messages (e.g. *"how much for web design?"*, *"tell me about AI bots"*, *"contact info"*) and serves relevant details immediately.
- **Direct Client Routing**: One-click Telegram direct messaging and contact links to hire you or discuss projects.
- **Easy Customization**: Update services, rates, or your bio directly in `services.json` without modifying any code.
- **Ready for Deployment**: Includes `Dockerfile` and `docker-compose.yml` for 1-click cloud or VPS deployment.

---

## 📁 Project Structure

```
tele-sales-bot/
├── .env                  # Private secrets (ignored by Git — never commit!)
├── .env.example          # Environment variables template
├── .gitignore            # Git exclusions
├── .dockerignore         # Docker exclusions
├── Dockerfile            # Container build specification
├── docker-compose.yml    # Docker Compose setup
├── requirements.txt      # Python dependencies
├── services.json         # Services, pricing, and personal profile
├── bot.py                # Main bot implementation & handlers
└── README.md             # Documentation
```

---

## ⚙️ Installation & Local Setup

### 1. Prerequisites
- Python 3.10+
- A Telegram account to create a bot via [@BotFather](https://t.me/BotFather)

### 2. Clone the Repository
```bash
git clone https://github.com/<your-username>/tele-sales-bot.git
cd tele-sales-bot
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
# Windows
copy .env.example .env

# Linux / macOS
cp .env.example .env
```

Edit `.env` and paste your bot token from `@BotFather`:
```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ

# Optional overrides (will fall back to services.json if left default)
CONTACT_EMAIL=you@example.com
CONTACT_PHONE=+1 (555) 019-2834
CONTACT_TELEGRAM=@your_telegram_handle
CONTACT_WEBSITE=https://yourportfolio.com
```

### 5. Run Locally
```bash
python bot.py
```

---

## 🐳 Running with Docker

You can run the bot in an isolated Docker container:

```bash
# Build and run in background
docker compose up -d --build

# View live logs
docker compose logs -f

# Stop container
docker compose down
```

---

## ☁️ Cloud Deployment Options

Because this bot uses **Long Polling**, it requires **no open ports, no public IP, and no domain/SSL**. You can host it anywhere:

1. **Railway / Render / Fly.io / Koyeb**:
   - Create a new project pointing to your GitHub repository.
   - Choose Python or Docker deployment.
   - Add `TELEGRAM_BOT_TOKEN` in the service's **Environment Variables** dashboard.
2. **Ubuntu / Debian VPS**:
   - Clone repo, copy `.env`, and run with `systemd` or `docker compose up -d`.

---

## 🛠️ Bot Commands

| Command | Description |
| :--- | :--- |
| `/start` | Open the welcome greeting and main interactive menu |
| `/services` | Browse all available service offerings & skills |
| `/pricing` | View pricing guide and turnaround times |
| `/contact` | View contact channels and portfolio links |
| `/help` | Display command usage and guidance |

---

## ✏️ Customizing Services & Details

To edit your name, bio, services, deliverables, or rates, edit `services.json`:
- `company`: Your personal name, title/tagline, email, and handles.
- `services`: Each service item with `title`, `pricing`, `turnaround`, `deliverables`, and `keywords`.
