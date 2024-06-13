from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import re
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    login_required,
    current_user,
    login_user,
    logout_user,
    UserMixin,
)
from datetime import datetime, timezone
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_manager

from config import SQLALCHEMY_DATABASE_URI, SECRET_KEY

# AUTHOR change config.py for accesing mysql. Default is sqlite3

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SECRET_KEY"] = SECRET_KEY
db = SQLAlchemy(app)

migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    role = db.Column(db.Integer, nullable=False, default=0)
    comments = db.relationship("Comment", back_populates="user")


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    content = db.Column(db.Text)
    author = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    date_posted = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    author_name = db.relationship("User", backref=db.backref("posts", lazy="dynamic"))
    likes = db.relationship("Like", back_populates="liked_post")
    post_comments = db.relationship("Comment", back_populates="post")
    # deleted_posts = db.relationship(
    #     "DeletedPosts", cascade="all,delete", backref="post", lazy=True
    # )

class DeletedPosts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_posted_id = db.Column(db.Integer)
    original_post_id = db.Column(db.Integer)
    content = db.Column(db.Text)
    title = db.Column(db.String(255))
    deletion_date = db.Column(
        db.DateTime, index=True, default=lambda: datetime.now(timezone.utc)
    )



class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"), nullable=False)
    timestamp = db.Column(
        db.DateTime, index=True, default=lambda: datetime.now(timezone.utc)
    )
    liked_post = db.relationship("Post", back_populates="likes")


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    content = db.Column(db.Text)
    timestamp = db.Column(
        db.DateTime, index=True, default=lambda: datetime.now(timezone.utc)
    )
    post = db.relationship("Post", back_populates="post_comments")
    user = db.relationship("User", back_populates="comments")


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def _get_posts():
    posts = Post.query.order_by(Post.date_posted.desc()).all()
    posts_with_likes_and_comments = []
    for post in posts:
        likes_count = Like.query.filter_by(post_id=post.id).count()
        comments = Comment.query.filter_by(post_id=post.id).all()
        comment_count = len(comments)
        posts_with_likes_and_comments.append(
            (post, likes_count, comments, comment_count)
        )
    return posts_with_likes_and_comments


@app.route("/")
def home():
    posts_with_likes_and_comments = _get_posts()
    return render_template("index.html", posts_with_likes_and_comments=posts_with_likes_and_comments)

@app.route("/best")
def sortbylikes():
    posts_with_likes_and_comments = _get_posts()
    sorted_posts = sorted(posts_with_likes_and_comments, key=lambda x: x[1], reverse=True)

    return render_template("index.html", posts_with_likes_and_comments=sorted_posts)

@app.route("/newest")
def sortbynewest():
    posts_with_likes_and_comments = _get_posts()
    return render_template("index.html", posts_with_likes_and_comments=posts_with_likes_and_comments)

@app.route("/commented")
def sortbyauthor():
    posts_with_likes_and_comments = _get_posts()
    sorted_posts = sorted(posts_with_likes_and_comments, key=lambda x: x[3], reverse=True)
    return render_template("index.html", posts_with_likes_and_comments=sorted_posts)


@login_manager.unauthorized_handler
def unauthorized():
    return redirect(url_for('signin'))

@app.route("/like/<int:post_id>", methods=["POST"])
@login_required
def like(post_id):
    post = Post.query.get_or_404(post_id)
    like = Like.query.filter_by(user_id=current_user.id, post_id=post_id).first()
    if like:
        db.session.delete(like)
        db.session.commit()
        return jsonify({"status": "unliked"})
    else:
        like = Like(user_id=current_user.id, post_id=post_id)
        db.session.add(like)
        db.session.commit()
        return jsonify({"status": "liked"})


@app.route("/likes/<int:post_id>")
def likes(post_id):
    likes = Like.query.filter_by(post_id=post_id).count()
    return jsonify({"likes": likes})


@app.route("/comment/<int:post_id>", methods=["POST"])
@login_required
def comment(post_id):
    post = Post.query.get_or_404(post_id)
    content = request.json.get("content")
    if content:
        comment = Comment(content=content, post_id=post_id, user_id=current_user.id)
        db.session.add(comment)
        db.session.commit()
        return jsonify({"status": "success"})
    else:
        return (
            jsonify(
                {"status": "error", "message": "Комментарий не может быть пустым."}
            ),
            400,
        )


@app.route("/send-comment/<int:post_id>", methods=["GET", "POST"])
@login_required
def send_comment(post_id):
    post = Post.query.get_or_404(post_id)
    if request.method == "POST":
        content = request.form.get("content")
        if content:
            comment = Comment(content=content, post_id=post_id, user_id=current_user.id)
            db.session.add(comment)
            db.session.commit()
            return render_template(
                "send_comment.html",
                post_id=post_id,
                comments=Comment.query.filter_by(post_id=post_id).all(),
            )

    comments = Comment.query.filter_by(post_id=post_id).all()
    return render_template("send_comment.html", post_id=post_id, comments=comments)


@app.route("/get-comments/<int:post_id>", methods=["GET"])
@login_required
def get_comments(post_id):
    post = Post.query.get_or_404(post_id)
    comments = Comment.query.filter_by(post_id=post.id).all()
    return jsonify(
        [
            {
                "id": comment.id,
                "content": comment.content,
                "timestamp": comment.timestamp.isoformat(),
                "username": comment.user.username,
            }
            for comment in comments
        ]
    )


@app.route("/delete-comment/<int:comment_id>", methods=["POST"])
@login_required
def delete_comment(comment_id):
    comment_to_delete = Comment.query.get_or_404(comment_id)
    if comment_to_delete.user_id != current_user.id:
        flash("Вы не можете удалить этот комментарий.", "error")
        return redirect(request.referrer or url_for("index"))
    db.session.delete(comment_to_delete)
    db.session.commit()
    flash("Комментарий был успешно удален!", "success")
    return redirect(request.referrer or url_for("index"))


@app.route("/sign-up", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form.get("email")
        username = request.form.get("username")
        password = request.form.get("password")
        if not email or not username or not password:
            flash("Все поля обязательны для заполнения.")
            return redirect(url_for("signup"))
        existing_email = User.query.filter_by(email=email).first()
        existing_username = User.query.filter_by(username=username).first()
        if existing_email:
            flash("Email уже используется.")
            return redirect(url_for("signup"))
        if existing_username:
            flash("Имя пользователя уже используется.")
            return redirect(url_for("signup"))
        if not re.match(r"^[a-zA-Z0-9\-._]+$", username):
            flash("Имя пользователя может содержать только буквы, цифры и - _.")
            return redirect(url_for("signup"))
        hashed_password = generate_password_hash(password)
        if username.startswith("admin"):
            new_user = User(email=email, username=username, password=hashed_password, role=1)
        else:
            new_user = User(email=email, username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash("Регистрация прошла успешно!")
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("home"))
        return redirect(url_for("signin"))
    return render_template("sign-up.html")


@app.route("/sign-in", methods=["GET", "POST"])
def signin():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("home"))
        else:
            flash("Неверный email или пароль")
            return redirect(url_for("signin"))
    return render_template("sign-in.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Вы успешно вышли из системы.")
    return redirect(url_for("signin"))


@app.route("/addPost")
@login_required
def addPost():
    return render_template("addPost.html")


@app.route("/publish_post", methods=["POST"])
@login_required
def publish_post():
    title = request.form.get("title")
    content = request.form.get("content")
    user_id = request.form.get("user_id")
    if not title.strip() or not content.strip():
        flash("Пожалуйста, заполните все поля.", "danger")
        return redirect(url_for("addPost"))
    new_post = Post(title=title, content=content, author=user_id)
    db.session.add(new_post)
    db.session.commit()
    flash("Ваш пост был опубликован успешно!", "success")
    return redirect(url_for("home"))


@app.route("/delete_post/<int:post_id>", methods=["POST"])
@login_required
def delete_post(post_id):
    post_to_delete = Post.query.get_or_404(post_id)

    if current_user.username == "Admin":
        pass
    elif post_to_delete.author != current_user.id:
        flash("Вы не можете удалить этот пост.", "error")
        return redirect(url_for("profile"))
    
    deleted_post_i = DeletedPosts(user_posted_id=post_to_delete.author, original_post_id=post_to_delete.id, title=post_to_delete.title, content=post_to_delete.content)
    db.session.add(deleted_post_i)
    db.session.commit()
    print(post_to_delete.author, post_to_delete.id, post_to_delete.title, post_to_delete.content)
    


    Like.query.filter_by(post_id=post_id).delete(synchronize_session=False)
    Comment.query.filter_by(post_id=post_id).delete(synchronize_session=False)

    # DeletedPost.query.filter_by(original_post_id=post_id).delete(
    #     synchronize_session=False
    # )

    # DeletedPost.query.filter_by(original_post_id=post_id).delete(
    #     synchronize_session=False
    # )

    db.session.delete(post_to_delete)
    db.session.commit()
    flash("Пост был успешно удален!", "success")
    return redirect(url_for("home"))


@app.route("/profile")
@login_required
def profile():
    user_posts_ids = [
        post.id for post in Post.query.filter_by(author=current_user.id).all()
    ]

    total_likes = Like.query.filter(Like.post_id.in_(user_posts_ids)).count()
    total_comments = Comment.query.filter(Comment.post_id.in_(user_posts_ids)).count()

    posts = (
        Post.query.filter_by(author=current_user.id)
        .order_by(Post.date_posted.desc())
        .all()
    )

    # deleted_posts = (
    #     DeletedPosts.query.join(Post, DeletedPosts.original_post_id == Post.id)
    #     .filter(Post.author == current_user.id)
    #     .all()
    # )

    deleted_posts = (
        DeletedPosts.query.filter_by(user_posted_id=current_user.id).all()
    )

    print(len(deleted_posts))
    deleted_posts_count = len(deleted_posts)

    return render_template(
        "profile.html",
        posts=posts,
        deleted_posts=deleted_posts,
        deleted_posts_count=deleted_posts_count,
        total_likes=total_likes,
        total_comments=total_comments,
    )


@app.route("/admin")
@login_required
def admin():
    if current_user.role == 1:
        posts = Post.query.all()
        return render_template("admin.html", posts=posts)
    flash("Access denied. Only Admin can access this page.", "error")
    return redirect(url_for("home"))

    


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="127.0.0.1", port=8082) # AUTHOR remove or change to yours if needed
