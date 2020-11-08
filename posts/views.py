from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from posts.forms import PostForm, CommentForm
from posts.models import Post, Group, User, Follow
from django.views.decorators.cache import cache_page


@cache_page(20, key_prefix="index_page")
def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'main_templates/index.html',
                  {'page': page, 'paginator': paginator})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.group.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'main_templates/group.html',
                  {'group': group, 'page': page, 'paginator': paginator})


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if request.method == 'POST':
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('index')
    return render(request, 'main_templates/new_post.html', {'form': form})


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.author.filter(author__username=author)
    if request.user.is_authenticated:
        following = Follow.objects.filter(user=request.user.id,
                                          author=author).exists()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, "main_templates/profile.html", {'author': author,
                  'page': page, 'paginator': paginator}
                  )


def post_view(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, pk=post_id)
    author = post.author
    comments = post.comments.all()

    form = CommentForm()
    return render(request, 'main_templates/post.html',
                  {'post': post,
                   'author': author,
                   'form': form,
                   'comments': comments})


@login_required
def post_edit(request, username, post_id):
    instance = get_object_or_404(Post, author__username=username, pk=post_id)
    if instance.author != request.user:
        return redirect(
            redirect('post', username=username, post_id=instance.pk))

    form = PostForm(request.POST or None, files=request.FILES or None,
                    instance=instance)

    if request.method == "POST":
        if form.is_valid():
            form.save()
            return redirect("post_view", username=request.user.username,
                            post_id=post_id)

    return render(request, "main_templates/new_post.html",
                  {"form": form, "post": instance}, )


def page_not_found(request, exception):
    return render(request, 'misc/404.html', {'path': request.path}, status=404)


def server_error(request):
    return render(request, 'misc/500.html', status=500)


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, pk=post_id)
    author = post.author
    comments = post.comments.all()
    form = CommentForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            new_comment = form.save(commit=False)
            new_comment.author = request.user
            new_comment.post = post
            new_comment.save()
            return redirect('post_view', username=username,
                            post_id=post_id)

    return render(request, 'main_templates/post.html',
                  {'post': post,
                   'author': author,
                   'form': form,
                   'comments': comments})


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'main_templates/follow.html',
                  {'page': page, 'paginator': paginator})


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(user=request.user, author=author)

    return redirect('profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = User.objects.get(username=username)
    follow_to_delete = Follow.objects.filter(user=request.user,
                                             author=author).delete()
    return redirect('profile', username=username)
