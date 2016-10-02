from flask import Blueprint, render_template, flash, abort, url_for, redirect, g, request
from flask_login import login_required

import models
import forms

posts_blueprint = Blueprint('posts', __name__, url_prefix='/posts')

@posts_blueprint.route('/stream')
@login_required
def stream():
    stream = g.user._get_current_object().get_stream().limit(100)

    return render_template('stream.html', stream=stream)

@posts_blueprint.route('/all')
def all():
    stream = models.Post.select().limit(100)

    return render_template('stream.html', stream=stream, public=True)

@posts_blueprint.route('/<int:post_id>', methods=['GET', 'POST'])
def view(post_id):
    form = forms.CommentForm()

    try:
        post = models.Post.select().where(models.Post.id == post_id).get()
    except models.DoesNotExist:
        flash('That post doesn\'t exist', 'error')
        abort(404)

    comments = models.Comment.select().where(models.Comment.post == post)
    user = g.user._get_current_object()

    if form.validate_on_submit():
        content = models.parse_post(form.content.data, page=url_for('posts.view', post_id=post_id))

        models.Comment.create(
            user=user,
            post=post,
            content=content
        )

        if not g.user._get_current_object() == post.user:
            models.Notification.create_notification(
                title='@{} commented on your post!'.format(g.user._get_current_object().username),
                link=url_for('posts.view', post_id=post_id),
                user=post.user
            )

        return redirect(url_for('posts.view', post_id=post_id))

    return render_template('post.html', post=post, comments=comments, form=form)

@posts_blueprint.route('/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(post_id):
    try:
        post = models.Post.get(models.Post.id == post_id)

    except models.DoesNotExist:
        flash('That post doesn\'t exist', 'error')
        abort(404)

    user = g.user._get_current_object()

    if user.is_admin or post.user == user:
        form = forms.PostForm()

        if form.validate_on_submit():
            raw_content = form.content.data.strip()

            q = models.Post.update(
                title=form.title.data,
                raw_content=raw_content,
                content=models.parse_post(raw_content, page=url_for('posts.view', post_id=post_id), edit=True)
            ).where(models.Post.id == post_id)
            q.execute()

            return redirect(url_for('posts.view', post_id=post_id))

        else:
            form.title.data = post.title
            form.content.data = post.raw_content
    else:
        flash('That post isn\'t yours', 'error')
        abort(401)

    return render_template('post_editor.html', form=form, edit=True)

@posts_blueprint.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    form = forms.PostForm()

    if form.validate_on_submit():
        raw_content = form.content.data.strip()

        p = models.Post.create(
            user=g.user._get_current_object(),
            title=form.title.data.strip(),
            raw_content=raw_content,
            content=''
        )

        models.Post.update(
            content=models.parse_post(raw_content, page=url_for('posts.view', post_id=p.id))
        ).where(models.Post.id == p.id).execute()

        flash('Message successfully posted!', 'success')
        return redirect(url_for('index'))

    return render_template('post_editor.html', form=form)

@posts_blueprint.route('/<int:post_id>/like')
@login_required
def like(post_id):
    try:
        post = models.Post.get(models.Post.id == post_id)
    except models.DoesNotExist:
        flash('That post does\'nt exist')
        abort(404)

    user = g.user._get_current_object()

    try:
        models.Like.get(
            models.Like.user == user,
            models.Like.post == post
        ).delete_instance()
    except:
        models.Like.create(
            post=post,
            user=g.user._get_current_object()
        )

        if not post.user == user:
            models.Notification.create_notification(
                title='@{} liked your post!'.format(user.username),
                user=post.user,
                link=url_for('posts.view', post_id=post_id)
            )

    return redirect(request.referrer)

@posts_blueprint.route('/<int:post_id>/delete')
def delete(post_id):
    try:
        post = models.Post.get(models.Post.id == post_id)
    except models.DoesNotExist:
        flash('That post doesn\'t exist', 'error')
        abort(404)

    user = g.user._get_current_object()

    if user.is_authenticated:
        if post.user == user or user.is_admin:
            if models.Comment.select().where(models.Comment.post == post).exists():
                models.Comment.delete().where(models.Comment.post == post).execute()

            if models.Like.select().where(models.Like.post == post).exists():
                models.Like.delete().where(models.Like.post == post).execute()

            post.delete_instance()

            flash('Post deleted!', 'sucess')
            return redirect(url_for('index'))

    flash('You can\'t delete that post', 'error')
    abort(401)