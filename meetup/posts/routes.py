from flask import render_template, url_for, flash, redirect, request, abort, Blueprint
from meetup import db
from meetup.posts.forms import PostForm
from meetup.models import Post
from flask_login import current_user, login_required


posts = Blueprint('posts', __name__)


@posts.route('/posts/new', methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(message=form.message.data, owner=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Post created successfully', 'success')
        return redirect(url_for('main.index'))
    return render_template('new_post.html', form=form, legend='New Post')


@posts.route('/posts/<int:post_id>')
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', post=post)


@posts.route('/posts/<int:post_id>/update', methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.owner != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.message = form.message.data
        db.session.commit()
        flash('Post updated successfully', 'success')
        return redirect(url_for('posts.post', post_id=post.id))
    elif request.method == 'GET':
        form.message.data = post.message
    return render_template('new_post.html', form=form, legend='Update Post')


@posts.route('/posts/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.owner != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Post deleted successfully', 'success')
    return redirect(url_for('main.index'))
