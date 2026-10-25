# 🌌 FandomVerse - The Ultimate Fandom Community Platform

> **Made by Alishba Shahid** | Contact: marinacaipher09@gmail.com

## ✨ About

FandomVerse is a professional, full-stack web application that brings together fans from every corner of pop culture. Whether you're into anime, K-Pop, gaming, movies, comics, or cosplay — FandomVerse is your home.

## 🚀 Features

- **🔐 Full Authentication System** - Sign up, Login, Profile management
- **🌟 Fandom Communities** - Browse, join, and participate in fan communities
- **📝 Rich Post System** - Create discussions, theories, reviews, fan art posts
- **💬 Nested Comments** - Engage in threaded conversations
- **❤️ Like System** - AJAX-powered like/unlike with animations
- **🔍 Real-time Search** - Live search with autocomplete
- **📱 Fully Responsive** - Looks great on all devices
- **🎨 Dark Neon Theme** - Professional glassmorphism UI with animations
- **🗄️ SQLite Database** - Real persistent database
- **🔒 Secure** - Password hashing, CSRF protection, input validation

## 🛠️ Tech Stack

| Technology | Purpose |
|-----------|---------|
| Python 3.14 | Backend Language |
| Flask | Web Framework |
| SQLAlchemy | ORM / Database |
| SQLite | Database Engine |
| Flask-Login | Authentication |
| Jinja2 | Templating |
| HTML5/CSS3/JS | Frontend |
| Font Awesome | Icons |

## 📦 Installation

```bash
# 1. Navigate to project directory
cd fandomverse

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the application
python app.py

# 4. Open in browser
# Visit: http://localhost:5000
```

## 📁 Project Structure

```
fandomverse/
├── app.py                  # Main Flask application
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── instance/
│   └── fandomverse.db     # SQLite database (auto-created)
├── static/
│   ├── css/
│   │   └── style.css      # Main stylesheet
│   ├── js/
│   │   └── main.js        # Interactive JavaScript
│   ├── images/
│   │   ├── logo.svg       # FandomVerse logo
│   │   ├── default-avatar.svg
│   │   └── default-fandom.svg
│   └── uploads/           # User uploads
└── templates/
    ├── base.html           # Base template
    ├── home.html           # Landing page
    ├── signup.html          # Registration
    ├── login.html           # Login
    ├── explore.html         # Browse fandoms
    ├── fandom_detail.html   # Individual fandom
    ├── post_detail.html     # Single post view
    ├── create_post.html     # New post form
    ├── profile.html         # User profile
    ├── edit_profile.html    # Edit profile
    ├── about.html           # About page
    ├── contact.html         # Contact page
    ├── search.html          # Search results
    ├── 404.html             # Not found
    └── 500.html             # Server error
```

## 🎮 Default Login

After first run, a demo admin account is created:
- **Username:** alishba_shahid
- **Email:** marinacaipher09@gmail.com
- **Password:** FandomVerse2024!

## 📧 Contact

- **Email:** marinacaipher09@gmail.com
- **Developer:** Alishba Shahid

## 📄 License

© 2024 FandomVerse by Alishba Shahid. All rights reserved.
