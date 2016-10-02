from flask import render_template, Blueprint, flash, abort, redirect, url_for, g

import models
import forms

comments_blueprint = Blueprint('comments', __name__, url_prefix='/comments')

@comments_blueprint.route('/<int:comment_id>', methods=['GET', 'POST'])
def view(comment_id):
    comment = models.Comment.get(models.Comment.id == comment_id)

    return render_template('comment.html', comment=comment)

@comments_blueprint.route('/<int:comment_id>/edit', methods=['GET', 'POST'])
def edit(comment_id):
    form = forms.CommentForm()
    comment = models.Comment.get(models.Comment.id == comment_id)

    if form.validate_on_submit():
        models.Comment.update(content=form.content.data).where(models.Comment.id == comment_id).execute()

        return redirect(url_for('posts.view', post_id=comment.post.id))

    form.content.data = comment.content

    return render_template('post_editor.html', form=form, comment=True, edit=True)

@comments_blueprint.route('/<int:comment_id>/delete')
def delete(comment_id):
    try:
        comment = models.Comment.get(models.Comment.id == comment_id)
    except models.DoesNotExist:
        flash('That comment doesn\'t exist', 'error')
        abort(404)

    user = g.user._get_current_object()

    if user.is_authenticated:
        if comment.user == user or user.is_admin:
            comment.delete_instance()

            flash('Comment deleted!', 'sucess')
            return redirect(url_for('index'))

    flash('You can\'t delete that comment', 'error')
    abort(401)
    return redirect(url_for('view_post', post_id=comment.post.id))