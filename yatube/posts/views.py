from django.shortcuts import render, get_object_or_404
from .models import Post, Group


def index(request):
    latest = Post.objects.all()[:11]
    return render(request, "index.html", {"posts": latest})


def group_posts(request, group_var):
    group = get_object_or_404(Group, slug=group_var)
    posts = Post.objects.filter(group=group)[:12]
    return render(request, "group.html", {"group": group, "posts": posts})
