"""
FandomVerse - The Ultimate Fandom Community Platform
Made by Alishba Shahid
A professional, SEO-optimized, responsive web application
"""

import os
import secrets
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, abort, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# ── App Configuration ──────────────────────────────────────────────────────
app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(32)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fandomverse.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'


# ── Database Models ────────────────────────────────────────────────────────

# Many-to-many: Users <-> Fandoms
user_fandoms = db.Table('user_fandoms',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('fandom_id', db.Integer, db.ForeignKey('fandom.id'), primary_key=True)
)

# Many-to-many: Posts <-> Tags
post_tags = db.Table('post_tags',
    db.Column('post_id', db.Integer, db.ForeignKey('post.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)


class User(UserMixin, db.Model):
    """User model with full profile support."""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    display_name = db.Column(db.String(100))
    bio = db.Column(db.Text, default='')
    avatar_url = db.Column(db.String(300), default='/static/images/default-avatar.svg')
    role = db.Column(db.String(20), default='member')  # member, moderator, admin
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    posts = db.relationship('Post', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    likes = db.relationship('Like', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    joined_fandoms = db.relationship('Fandom', secondary=user_fandoms, backref=db.backref('members', lazy='dynamic'))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


class Fandom(db.Model):
    """Fandom/Community model."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    slug = db.Column(db.String(120), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)  # anime, movies, games, tv, books, comics, music, kpop
    cover_image = db.Column(db.String(300), default='/static/images/default-fandom.svg')
    icon_emoji = db.Column(db.String(10), default='⭐')
    member_count = db.Column(db.Integer, default=0)
    is_featured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    posts = db.relationship('Post', backref='fandom', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Fandom {self.name}>'


class Post(db.Model):
    """Post/Thread model."""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    post_type = db.Column(db.String(20), default='discussion')  # discussion, theory, fanart, review, meme, cosplay
    image_url = db.Column(db.String(300))
    views = db.Column(db.Integer, default=0)
    is_pinned = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Foreign Keys
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    fandom_id = db.Column(db.Integer, db.ForeignKey('fandom.id'), nullable=False)

    # Relationships
    comments = db.relationship('Comment', backref='post', lazy='dynamic', cascade='all, delete-orphan')
    likes = db.relationship('Like', backref='post', lazy='dynamic', cascade='all, delete-orphan')
    tags = db.relationship('Tag', secondary=post_tags, backref=db.backref('posts', lazy='dynamic'))

    @property
    def like_count(self):
        return self.likes.count()

    @property
    def comment_count(self):
        return self.comments.count()

    def __repr__(self):
        return f'<Post {self.title}>'


class Comment(db.Model):
    """Comment model with nested replies."""
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Foreign Keys
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)

    # Self-referential relationship for nested comments
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')

    def __repr__(self):
        return f'<Comment {self.id}>'


class Like(db.Model):
    """Like model for posts."""
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

    __table_args__ = (db.UniqueConstraint('user_id', 'post_id', name='unique_like'),)


class Tag(db.Model):
    """Tag model for categorizing posts."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    color = db.Column(db.String(7), default='#6c5ce7')


class ContactMessage(db.Model):
    """Contact form submissions."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ContactMessage {self.subject}>'


class Newsletter(db.Model):
    """Newsletter subscriber."""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    subscribed_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)


# ── User Loader ────────────────────────────────────────────────────────────
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# ── Context Processors ────────────────────────────────────────────────────
@app.context_processor
def inject_globals():
    """Inject global variables into all templates."""
    categories = [
        {'name': 'Anime & Manga', 'slug': 'anime', 'icon': '🎌', 'color': '#e84393'},
        {'name': 'Movies & TV', 'slug': 'movies', 'icon': '🎬', 'color': '#6c5ce7'},
        {'name': 'Video Games', 'slug': 'games', 'icon': '🎮', 'color': '#00b894'},
        {'name': 'Books & Lit', 'slug': 'books', 'icon': '📚', 'color': '#fdcb6e'},
        {'name': 'Comics & DC/Marvel', 'slug': 'comics', 'icon': '💥', 'color': '#e17055'},
        {'name': 'K-Pop & Music', 'slug': 'kpop', 'icon': '🎵', 'color': '#a29bfe'},
        {'name': 'Cosplay', 'slug': 'cosplay', 'icon': '🎭', 'color': '#fd79a8'},
        {'name': 'Sci-Fi & Fantasy', 'slug': 'scifi', 'icon': '🚀', 'color': '#0984e3'},
    ]
    return dict(
        categories=categories,
        current_year=datetime.utcnow().year,
        site_name='FandomVerse'
    )


# ── Routes ─────────────────────────────────────────────────────────────────

@app.route('/')
def home():
    """Landing page with featured fandoms and trending posts."""
    featured_fandoms = Fandom.query.filter_by(is_featured=True).limit(8).all()
    if not featured_fandoms:
        featured_fandoms = Fandom.query.order_by(Fandom.member_count.desc()).limit(8).all()

    recent_posts = Post.query.order_by(Post.created_at.desc()).limit(10).all()
    trending_posts = Post.query.order_by(Post.views.desc()).limit(6).all()
    total_users = User.query.count()
    total_fandoms = Fandom.query.count()
    total_posts = Post.query.count()

    return render_template('home.html',
                           featured_fandoms=featured_fandoms,
                           recent_posts=recent_posts,
                           trending_posts=trending_posts,
                           stats={'users': total_users, 'fandoms': total_fandoms, 'posts': total_posts})


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """User registration page."""
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        display_name = request.form.get('display_name', '').strip()

        # Validation
        errors = []
        if len(username) < 3 or len(username) > 30:
            errors.append('Username must be 3-30 characters long.')
        if not email or '@' not in email:
            errors.append('Please enter a valid email address.')
        if len(password) < 8:
            errors.append('Password must be at least 8 characters.')
        if password != confirm_password:
            errors.append('Passwords do not match.')
        if User.query.filter_by(username=username).first():
            errors.append('Username already taken.')
        if User.query.filter_by(email=email).first():
            errors.append('Email already registered.')

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('signup.html')

        user = User(
            username=username,
            email=email,
            display_name=display_name or username
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash('Welcome to FandomVerse! 🎉 Your account has been created.', 'success')
        return redirect(url_for('home'))

    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page."""
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == 'POST':
        username_or_email = request.form.get('username_or_email', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)

        user = User.query.filter(
            (User.username == username_or_email) | (User.email == username_or_email)
        ).first()

        if user and user.check_password(password):
            user.last_seen = datetime.utcnow()
            db.session.commit()
            login_user(user, remember=bool(remember))
            flash(f'Welcome back, {user.display_name or user.username}! 🌟', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('home'))
        else:
            flash('Invalid username/email or password.', 'danger')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """User logout."""
    logout_user()
    flash('You have been logged out. See you soon! 👋', 'info')
    return redirect(url_for('home'))


@app.route('/explore')
def explore():
    """Explore all fandoms."""
    category = request.args.get('category', 'all')
    search = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)

    query = Fandom.query
    if category != 'all':
        query = query.filter_by(category=category)
    if search:
        query = query.filter(Fandom.name.ilike(f'%{search}%'))

    fandoms = query.order_by(Fandom.member_count.desc()).paginate(page=page, per_page=12, error_out=False)
    return render_template('explore.html', fandoms=fandoms, current_category=category, search=search)


@app.route('/fandom/<slug>')
def fandom_detail(slug):
    """View a specific fandom."""
    fandom = Fandom.query.filter_by(slug=slug).first_or_404()
    page = request.args.get('page', 1, type=int)
    sort = request.args.get('sort', 'newest')

    query = Post.query.filter_by(fandom_id=fandom.id)
    if sort == 'popular':
        query = query.order_by(Post.views.desc())
    elif sort == 'discussed':
        query = query.order_by(Post.created_at.desc())  # simplified
    else:
        query = query.order_by(Post.created_at.desc())

    posts = query.paginate(page=page, per_page=15, error_out=False)
    is_member = False
    if current_user.is_authenticated:
        is_member = fandom in current_user.joined_fandoms

    return render_template('fandom_detail.html', fandom=fandom, posts=posts, sort=sort, is_member=is_member)


@app.route('/fandom/<slug>/join', methods=['POST'])
@login_required
def join_fandom(slug):
    """Join/leave a fandom."""
    fandom = Fandom.query.filter_by(slug=slug).first_or_404()
    if fandom in current_user.joined_fandoms:
        current_user.joined_fandoms.remove(fandom)
        fandom.member_count = max(0, fandom.member_count - 1)
        flash(f'You left {fandom.name}.', 'info')
    else:
        current_user.joined_fandoms.append(fandom)
        fandom.member_count += 1
        flash(f'You joined {fandom.name}! 🎉', 'success')
    db.session.commit()
    return redirect(url_for('fandom_detail', slug=slug))


@app.route('/post/new', methods=['GET', 'POST'])
@login_required
def create_post():
    """Create a new post."""
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        fandom_id = request.form.get('fandom_id', type=int)
        post_type = request.form.get('post_type', 'discussion')

        if not title or not content or not fandom_id:
            flash('Please fill in all required fields.', 'danger')
            fandoms = Fandom.query.order_by(Fandom.name).all()
            return render_template('create_post.html', fandoms=fandoms)

        fandom = Fandom.query.get_or_404(fandom_id)
        post = Post(
            title=title,
            content=content,
            post_type=post_type,
            author_id=current_user.id,
            fandom_id=fandom.id
        )

        # Handle tags
        tags_str = request.form.get('tags', '')
        if tags_str:
            for tag_name in tags_str.split(','):
                tag_name = tag_name.strip().lower()
                if tag_name:
                    tag = Tag.query.filter_by(name=tag_name).first()
                    if not tag:
                        tag = Tag(name=tag_name)
                        db.session.add(tag)
                    post.tags.append(tag)

        db.session.add(post)
        db.session.commit()
        flash('Post created successfully! 🚀', 'success')
        return redirect(url_for('post_detail', post_id=post.id))

    fandoms = Fandom.query.order_by(Fandom.name).all()
    return render_template('create_post.html', fandoms=fandoms)


@app.route('/post/<int:post_id>')
def post_detail(post_id):
    """View a single post with comments."""
    post = Post.query.get_or_404(post_id)
    post.views += 1
    db.session.commit()

    comments = Comment.query.filter_by(post_id=post.id, parent_id=None).order_by(Comment.created_at.desc()).all()
    user_liked = False
    if current_user.is_authenticated:
        user_liked = Like.query.filter_by(user_id=current_user.id, post_id=post.id).first() is not None

    return render_template('post_detail.html', post=post, comments=comments, user_liked=user_liked)


@app.route('/post/<int:post_id>/like', methods=['POST'])
@login_required
def like_post(post_id):
    """Toggle like on a post."""
    post = Post.query.get_or_404(post_id)
    existing_like = Like.query.filter_by(user_id=current_user.id, post_id=post.id).first()

    if existing_like:
        db.session.delete(existing_like)
        liked = False
    else:
        like = Like(user_id=current_user.id, post_id=post.id)
        db.session.add(like)
        liked = True

    db.session.commit()
    return jsonify({'liked': liked, 'count': post.like_count})


@app.route('/post/<int:post_id>/comment', methods=['POST'])
@login_required
def add_comment(post_id):
    """Add a comment to a post."""
    post = Post.query.get_or_404(post_id)
    content = request.form.get('content', '').strip()
    parent_id = request.form.get('parent_id', type=int)

    if not content:
        flash('Comment cannot be empty.', 'danger')
        return redirect(url_for('post_detail', post_id=post.id))

    comment = Comment(
        content=content,
        author_id=current_user.id,
        post_id=post.id,
        parent_id=parent_id
    )
    db.session.add(comment)
    db.session.commit()
    flash('Comment added! 💬', 'success')
    return redirect(url_for('post_detail', post_id=post.id))


@app.route('/profile/<username>')
def profile(username):
    """View user profile."""
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author_id=user.id).order_by(Post.created_at.desc()).limit(20).all()
    return render_template('profile.html', profile_user=user, posts=posts)


@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit user profile."""
    if request.method == 'POST':
        current_user.display_name = request.form.get('display_name', '').strip()
        current_user.bio = request.form.get('bio', '').strip()
        db.session.commit()
        flash('Profile updated! ✨', 'success')
        return redirect(url_for('profile', username=current_user.username))

    return render_template('edit_profile.html')


@app.route('/about')
def about():
    """About page."""
    return render_template('about.html')


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact page."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()

        if not all([name, email, subject, message]):
            flash('Please fill in all fields.', 'danger')
            return render_template('contact.html')

        msg = ContactMessage(name=name, email=email, subject=subject, message=message)
        db.session.add(msg)
        db.session.commit()
        flash('Message sent successfully! We\'ll get back to you soon. 📧', 'success')
        return redirect(url_for('contact'))

    return render_template('contact.html')


@app.route('/newsletter', methods=['POST'])
def newsletter_subscribe():
    """Subscribe to newsletter."""
    email = request.form.get('email', '').strip()
    if not email or '@' not in email:
        flash('Please enter a valid email.', 'danger')
        return redirect(request.referrer or url_for('home'))

    existing = Newsletter.query.filter_by(email=email).first()
    if existing:
        flash('You\'re already subscribed! 💌', 'info')
    else:
        sub = Newsletter(email=email)
        db.session.add(sub)
        db.session.commit()
        flash('Subscribed to newsletter! 🎊', 'success')

    return redirect(request.referrer or url_for('home'))


@app.route('/search')
def search():
    """Global search across fandoms and posts."""
    query = request.args.get('q', '').strip()
    if not query:
        return render_template('search.html', results=None, query='')

    fandoms = Fandom.query.filter(Fandom.name.ilike(f'%{query}%')).limit(10).all()
    posts = Post.query.filter(
        (Post.title.ilike(f'%{query}%')) | (Post.content.ilike(f'%{query}%'))
    ).order_by(Post.created_at.desc()).limit(20).all()
    users = User.query.filter(
        (User.username.ilike(f'%{query}%')) | (User.display_name.ilike(f'%{query}%'))
    ).limit(10).all()

    return render_template('search.html', fandoms=fandoms, posts=posts, users=users, query=query)


# ── API Routes for AJAX interactions ──────────────────────────────────────

@app.route('/api/stats')
def api_stats():
    """Get live site statistics."""
    return jsonify({
        'users': User.query.count(),
        'fandoms': Fandom.query.count(),
        'posts': Post.query.count(),
        'comments': Comment.query.count()
    })


@app.route('/api/search/quick')
def api_quick_search():
    """Quick search for autocomplete."""
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify([])

    results = []
    fandoms = Fandom.query.filter(Fandom.name.ilike(f'%{q}%')).limit(5).all()
    for f in fandoms:
        results.append({'type': 'fandom', 'name': f.name, 'url': url_for('fandom_detail', slug=f.slug), 'icon': f.icon_emoji})

    posts = Post.query.filter(Post.title.ilike(f'%{q}%')).limit(5).all()
    for p in posts:
        results.append({'type': 'post', 'name': p.title, 'url': url_for('post_detail', post_id=p.id), 'icon': '📝'})

    return jsonify(results)


# ── SEO Endpoints ──────────────────────────────────────────────────────────
@app.route('/robots.txt')
def robots_txt():
    return send_from_directory(app.static_folder, 'robots.txt')

@app.route('/sitemap.xml')
def sitemap_xml():
    return send_from_directory(app.static_folder, 'sitemap.xml', mimetype='application/xml')


# ── Error Handlers ─────────────────────────────────────────────────────────
@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500


# ── Database Initialization & Seeding ──────────────────────────────────────
def seed_database():
    """Seed database with initial data."""
    if Fandom.query.first():
        return  # Already seeded

    # Create fandoms
    fandoms_data = [
        # Anime & Manga
        {'name': 'Attack on Titan', 'slug': 'attack-on-titan', 'category': 'anime', 'icon_emoji': '⚔️',
         'description': 'Dive into the world of Titans! Discuss episodes, manga chapters, theories about the Founding Titan, character arcs of Eren, Mikasa, and Levi, and everything from the Walls of Paradis to the rumbling. Share your fan art, cosplay, and deepest AOT theories with fellow Scouts!',
         'is_featured': True, 'member_count': 15420},
        {'name': 'Jujutsu Kaisen', 'slug': 'jujutsu-kaisen', 'category': 'anime', 'icon_emoji': '👹',
         'description': 'Welcome to the domain of curses! Talk about Gojo\'s Infinite Void, Sukuna\'s reign, the Culling Game, and all the intense battles. Share theories, fan art, and discuss the latest manga chapters with the JJK community.',
         'is_featured': True, 'member_count': 12800},
        {'name': 'One Piece', 'slug': 'one-piece', 'category': 'anime', 'icon_emoji': '🏴‍☠️',
         'description': 'Set sail with the Straw Hat Pirates! The world\'s greatest anime and manga series with over 1000 episodes. Discuss Devil Fruits, Haki, the mystery of the One Piece, Luffy\'s Gear 5, and everything Grand Line!',
         'is_featured': True, 'member_count': 18900},
        {'name': 'Demon Slayer', 'slug': 'demon-slayer', 'category': 'anime', 'icon_emoji': '🗡️',
         'description': 'Join the Demon Slayer Corps! Discuss Tanjiro\'s journey, breathing techniques, the Hashira, Muzan Kibutsuji, and the stunning animation by Ufotable. Share your favorite moments and fan creations!',
         'is_featured': True, 'member_count': 11200},

        # Movies & TV
        {'name': 'Marvel Cinematic Universe', 'slug': 'mcu', 'category': 'movies', 'icon_emoji': '🦸',
         'description': 'Everything MCU! From the Infinity Saga to the Multiverse Saga, discuss all Marvel movies, Disney+ shows, theories about Kang, the X-Men integration, Secret Wars, and the future of the MCU. Avengers assemble!',
         'is_featured': True, 'member_count': 22100},
        {'name': 'Star Wars', 'slug': 'star-wars', 'category': 'movies', 'icon_emoji': '⭐',
         'description': 'May the Force be with you! Discuss the Skywalker Saga, The Mandalorian, Ahsoka, Andor, lightsaber duels, Sith vs Jedi lore, and everything from a galaxy far, far away. Share your collections and theories!',
         'is_featured': True, 'member_count': 19500},
        {'name': 'Stranger Things', 'slug': 'stranger-things', 'category': 'movies', 'icon_emoji': '🔮',
         'description': 'Welcome to the Upside Down! Discuss Eleven\'s powers, the Mind Flayer, Vecna, Hawkins adventures, and all the 80s nostalgia. Theories, fan art, and everything Stranger Things!',
         'member_count': 8900},

        # Video Games
        {'name': 'Genshin Impact', 'slug': 'genshin-impact', 'category': 'games', 'icon_emoji': '🌟',
         'description': 'Explore Teyvat together! Discuss characters, builds, team compositions, lore theories, Archon quests, events, and share your adventures across the seven nations. Pull rates, leaks, and beautiful fan art welcome!',
         'is_featured': True, 'member_count': 16700},
        {'name': 'Valorant', 'slug': 'valorant', 'category': 'games', 'icon_emoji': '🎯',
         'description': 'Tactical shooter fans unite! Discuss agents, maps, strategies, esports tournaments, patch updates, ranked tips, and clutch moments. Share your aces and support fellow players!',
         'member_count': 9800},
        {'name': 'Minecraft', 'slug': 'minecraft', 'category': 'games', 'icon_emoji': '⛏️',
         'description': 'Block by block! Share your builds, redstone contraptions, survival worlds, modded adventures, and creative masterpieces. Tips, tricks, seeds, and community projects welcome!',
         'member_count': 14200},

        # Books
        {'name': 'Harry Potter', 'slug': 'harry-potter', 'category': 'books', 'icon_emoji': '⚡',
         'description': 'Welcome to the Wizarding World! Discuss Hogwarts houses, spells, magical creatures, fan theories, the Marauders era, Fantastic Beasts, and everything J.K. Rowling created. Which house are you? 🏰',
         'is_featured': True, 'member_count': 20500},
        {'name': 'Lord of the Rings', 'slug': 'lord-of-the-rings', 'category': 'books', 'icon_emoji': '💍',
         'description': 'One Ring to rule them all! Discuss Tolkien\'s masterwork, the movies, Rings of Power, Middle-earth lore, languages, maps, and the epic journey from the Shire to Mount Doom.',
         'member_count': 11800},

        # K-Pop & Music
        {'name': 'BTS ARMY', 'slug': 'bts-army', 'category': 'kpop', 'icon_emoji': '💜',
         'description': 'BTS and ARMY forever! Discuss music, concerts, lyrics analysis, dance practices, variety shows, solo projects, and the impact of BTS on global culture. Purple you! 보라해! 💜',
         'member_count': 25000},
        {'name': 'BLACKPINK', 'slug': 'blackpink', 'category': 'kpop', 'icon_emoji': '🖤',
         'description': 'BLACKPINK in your area! Discuss comebacks, performances, fashion, solo activities of Jisoo, Jennie, Rosé, and Lisa. Share fan edits, concert experiences, and BLINK moments!',
         'member_count': 17300},

        # Comics
        {'name': 'DC Universe', 'slug': 'dc-universe', 'category': 'comics', 'icon_emoji': '🦇',
         'description': 'Welcome to Gotham and beyond! Discuss Batman, Superman, Wonder Woman, The Flash, Aquaman, comics, animated series, movies, and the entire DC multiverse. Share your comic collections!',
         'member_count': 13600},

        # Cosplay
        {'name': 'Cosplay Central', 'slug': 'cosplay-central', 'category': 'cosplay', 'icon_emoji': '🎭',
         'description': 'Show off your cosplay skills! Share WIP photos, completed costumes, tutorials, prop-making tips, convention experiences, and get feedback from fellow cosplayers. All fandoms welcome!',
         'member_count': 7500},
    ]

    for data in fandoms_data:
        fandom = Fandom(**data)
        db.session.add(fandom)

    # Create a demo user
    demo_user = User(
        username='alishba_shahid',
        email='marinacaipher09@gmail.com',
        display_name='Alishba Shahid',
        bio='Creator of FandomVerse 🌟 | Anime enthusiast | Gamer | K-Pop stan | Bringing all fandoms together!',
        role='admin'
    )
    demo_user.set_password('FandomVerse2024!')
    db.session.add(demo_user)

    # Create some sample posts
    db.session.flush()  # Get IDs

    sample_posts = [
        Post(title='🔥 Top 10 Anime Battles That Broke the Internet!',
             content='Let\'s discuss the most iconic anime battles of all time! From Goku vs Frieza to Naruto vs Sasuke, from Luffy\'s Gear 5 transformation to Gojo vs Sukuna - which battle gave you the most chills? Drop your top 10 list below and let\'s debate! Remember, every anime fan has a different perspective, and that\'s what makes this community amazing. I\'ll start: My #1 pick is the Gojo vs Sukuna fight in JJK - the animation, the stakes, the raw power display was absolutely unmatched! What\'s yours?',
             post_type='discussion', author_id=demo_user.id, fandom_id=1, views=2450),
        Post(title='My Demon Slayer Tanjiro Cosplay - 6 Months in the Making!',
             content='Finally finished my Tanjiro Kamado cosplay and I\'m so proud of it! The hanafuda earrings were hand-painted, the haori pattern was custom printed on fabric, and the Nichirin blade was 3D printed and hand-painted with color-changing paint. Took me 6 months from concept to completion. Swipe through to see the progress photos! If you have any questions about the materials or techniques I used, feel free to ask. I love helping fellow cosplayers bring their favorite characters to life!',
             post_type='cosplay', author_id=demo_user.id, fandom_id=4, views=1890),
        Post(title='MCU Phase 7 Predictions - The Mutant Saga Begins!',
             content='With Secret Wars wrapping up the Multiverse Saga, I think Phase 7 will fully introduce the X-Men. Here\'s my theory: The incursion between universes will merge the Fox X-Men timeline with the MCU, bringing a new version of the characters. Professor X and Magneto will be younger, played by new actors, but we might get Patrick Stewart for a cameo. Wolverine (Hugh Jackman?) could be the bridge character. The first movie might be "Uncanny X-Men" introducing the team at the Xavier School. What do you think? Share your predictions!',
             post_type='theory', author_id=demo_user.id, fandom_id=5, views=3200),
        Post(title='Genshin Impact Team Building Guide for Beginners 🌟',
             content='New to Genshin? Here\'s a comprehensive guide on building your first team! Understanding elemental reactions is KEY. Start with: 1) Main DPS (your damage dealer), 2) Sub-DPS (supports with off-field damage), 3) Support (shields, heals, buffs), 4) Flex (elemental resonance). Best free characters: Xiangling (Pyro DPS queen), Kaeya (Cryo support), Barbara (healer), Noelle (shield). Don\'t waste primogems on standard banner! Save for limited character banners. Artifacts matter more than weapons at higher levels. Feel free to ask questions!',
             post_type='discussion', author_id=demo_user.id, fandom_id=8, views=5100),
        Post(title='BTS Discography Deep Dive: Hidden Gems You Might Have Missed 💜',
             content='Everyone knows Dynamite, Butter, and Boy With Luv, but let\'s talk about the B-sides and deep cuts that deserve more attention! "134340" is an absolute masterpiece with its jazzy vibes. "Pied Piper" has lyrics that are both self-aware and catchy. "House of Cards" showcases their vocal line beautifully. "Outro: Tear" is RM at his most raw and emotional. "Sea" (the hidden track from Love Yourself: Her) is one of the most beautiful songs about hope I\'ve ever heard. What are YOUR favorite underrated BTS songs? Let\'s create the ultimate hidden gems playlist!',
             post_type='review', author_id=demo_user.id, fandom_id=13, views=4200),
    ]

    for post in sample_posts:
        db.session.add(post)

    # Create some tags
    tag_names = ['theory', 'discussion', 'fanart', 'cosplay', 'review', 'meme', 'spoilers', 'newbie-friendly',
                 'hot-take', 'recommendation', 'guide', 'news', 'event', 'contest']
    colors = ['#e84393', '#6c5ce7', '#00b894', '#fdcb6e', '#e17055', '#a29bfe', '#fd79a8',
              '#0984e3', '#00cec9', '#fab1a0', '#55efc4', '#74b9ff', '#dfe6e9', '#ffeaa7']
    for name, color in zip(tag_names, colors):
        db.session.add(Tag(name=name, color=color))

    db.session.commit()
    print('[OK] Database seeded successfully!')


# ── Main ───────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_database()
    app.run(debug=True, port=5000)
