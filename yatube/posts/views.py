from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
# from django.views.decorators.cache import cache_page
from django.http import HttpResponseRedirect

from .models import Follow, Post, Group, User, Ip
from .forms import CommentForm, PostForm

paginator_pages = 10


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# @cache_page(20)
def index(request):
    latest = Post.objects.select_related('author', 'group').prefetch_related(
        'comments')
    paginator = Paginator(latest, paginator_pages)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'index.html', {'page': page})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.group_posts.select_related('author').prefetch_related(
        'comments')
    paginator = Paginator(posts, paginator_pages)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'group.html', {'group': group, 'page': page})


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.select_related('group').prefetch_related('comments')
    paginator = Paginator(posts, paginator_pages)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    following = None
    if request.user.is_authenticated:
        following = author.following.filter(user=request.user).exists()
    context = {
        'author': author,
        'page': page,
        'following': following,
    }
    return render(request, 'profile.html', context)


def post_view(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    comments = post.comments.select_related('author')
    author = post.author
    form = CommentForm()
    ip = get_client_ip(request)
    Ip.objects.get_or_create(ip=ip)
    post.views.add(Ip.objects.get(ip=ip))
    following = None
    if request.user.is_authenticated:
        following = author.following.filter(user=request.user).exists()
    context = {
        'author': author,
        'post': post,
        'form': form,
        'comments': comments,
        'following': following,
    }
    return render(request, 'post.html', context)


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
    return redirect('posts:post', username, post_id)


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:index')
    context = {
        'header': 'Добавить запись',
        'submit_text': 'Добавить',
        'form': form,
    }
    return render(request, 'new_post.html', context)


def post_edit(request, username, post_id):
    if request.user.username != username:
        return redirect('posts:post', username, post_id)
    post = get_object_or_404(Post, author__username=username, id=post_id)
    if not post.is_recently_pub:
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    form = PostForm(
        request.POST or None, files=request.FILES or None, instance=post
    )
    if form.is_valid():
        post = form.save(commit=False)
        post.save()
        return redirect('posts:post', username, post_id)
    context = {
        'header': 'Редактировать запись',
        'submit_text': 'Сохранить',
        'form': form,
        'post': post,
    }
    return render(request, 'new_post.html', context)


@login_required
def follow_index(request):
    posts = Post.objects.filter(
        author__following__user=request.user
    ).select_related('author', 'group').prefetch_related('comments')
    paginator = Paginator(posts, paginator_pages)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'follow.html', {'page': page})


@login_required
def profile_follow(request, username):
    if request.user.username == username:
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    author = get_object_or_404(User, username=username)
    Follow.objects.get_or_create(user=request.user, author=author)
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@login_required
def post_delete(request, username, post_id):
    if request.user.username != username:
        return redirect('posts:post', username, post_id)
    post = get_object_or_404(Post, author__username=username, id=post_id)
    post.delete()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


def page_not_found(request, exception):
    return render(request, 'misc/404.html', {'path': request.path}, status=404)


def server_error(request):
    return render(request, 'misc/500.html', status=500)
