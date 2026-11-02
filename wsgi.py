import os
from app import app, db, seed_database

with app.app_context():
    db.create_all()
    seed_database()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
