from django.shortcuts import render, get_object_or_404, redirect
from .models import Post, Group, User
from django.contrib.auth.decorators import login_required
from .forms import CreatePostForm
from django.core.paginator import Paginator


def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'index.html',
        {'page': page, 'paginator': paginator}
    )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'group.html',
        {"group": group, 'page': page, 'paginator': paginator}
    )


@login_required
def new_post(request):
    form = CreatePostForm(request.POST or None,  files=request.FILES or None)
    if request.method == 'POST':
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            form.save()
            return redirect("index")
    return render(request, "new.html", {'form': form})


def profile(request, username):
    user = get_object_or_404(User, username=username)
    post_list = user.posts.filter(author__username=user)
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'profile.html',
        {'page': page, 'paginator': paginator, "username": user}
    )


def post_view(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, pk=post_id)
    author = post.author
    return render(
        request,
        'post.html',
        {'post': post, 'author': author}
    )


@login_required
def post_edit(request, username, post_id):
    instance = get_object_or_404(Post, author__username=username, pk=post_id)
    if instance.author != request.user:
        return redirect(
            redirect('post', username=username, post_id=instance.pk))
    form = CreatePostForm(request.POST or None, files=request.FILES or None, instance=instance)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('post', username=username, post_id=instance.pk)
    return render(
        request, "new.html", {
            'form': form, 'instance': instance, 'edit': True})


def page_not_found(request, exception):
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)
