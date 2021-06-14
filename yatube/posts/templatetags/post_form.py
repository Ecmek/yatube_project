from django import template

from posts.forms import PostForm

register = template.Library()


@register.simple_tag
def post_form(post):
    return PostForm(instance=post or None)
