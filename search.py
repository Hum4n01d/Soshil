from flask import Blueprint, render_template, request

import models
import forms

search_blueprint = Blueprint('search', __name__, url_prefix='/search')

@search_blueprint.route('/')
def search():
    form = forms.SearchForm()

    query = request.args.get('query', '')

    form.query.data = query

    scope = request.args.get('scope', 'posts')

    if scope == 'users':
        results = models.User.select().where(
            (models.User.username.contains(query))
        )
    else:
        results = models.Post.select().where(
            (models.Post.content.contains(query)) |
            (models.Post.title.contains(query))
        )

    return render_template('search.html', results=results, query=query, form=form, scope=scope)