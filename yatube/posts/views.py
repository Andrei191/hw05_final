from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post

from yatube.settings import PAGE_COUNT  # isort:skip


def paginator_func(request, object, count_post):
    paginator = Paginator(object, count_post)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


User = get_user_model()


def index(request):
    post_list = Post.objects.all()
    page_obj = paginator_func(request, post_list, PAGE_COUNT)
    # Отдаем в словаре контекста
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    page_obj = paginator_func(request, posts, PAGE_COUNT)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    follow_user = request.user
    posts = author.posts.all()
    count = posts.count()
    page_obj = paginator_func(request, posts, PAGE_COUNT)
    following = False
    if not follow_user.is_anonymous:
        authors = [follower.author for follower in follow_user.follower.all()]
        following = author in authors
    context = {
        'posts': posts,
        'count': count,
        'page_obj': page_obj,
        'author': author,
        'following': following,
        'follow_user': follow_user
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    author = post.author
    posts = author.posts
    count = posts.count()
    comments = post.comments.all()
    form = CommentForm(request.POST or None)
    # Здесь код запроса к модели и создание словаря контекста
    context = {
        'post': post,
        'count': count,
        'author': author,
        'comments': comments,
        'form': form
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        new_post = form.save(commit=False)
        new_post.author = request.user
        new_post.save()
        return redirect('posts:profile', request.user.username)

    context = {
        'form': form
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    edit_post = get_object_or_404(Post, id=post_id)

    if request.user != edit_post.author:
        return redirect('posts:post_detail', edit_post.id)
    form = PostForm(request.POST or None,
                    files=request.FILES or None, instance=edit_post)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', edit_post.id)

    context = {
        'form': form,
        'is_edit': True
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    # информация о текущем пользователе доступна в переменной request.user
    # ...
    authors = [follower.author for follower in request.user.follower.all()]
    post_list = Post.objects.filter(author__in=authors)
    page_obj = paginator_func(request, post_list, PAGE_COUNT)
    # Отдаем в словаре контекста
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author =  get_object_or_404(User, username=username)
    authors = [follower.author for follower in request.user.follower.all()]
    # Подписаться на автора
    if request.user != author and author not in authors:
        Follow.objects.create(
            user=request.user,
            author=User.objects.filter(username=username)[0]
        )
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    # Дизлайк, отписка
    author = User.objects.get(username=username)
    Follow.objects.filter(author=author.id).delete()
    return redirect('posts:profile', username=username)
