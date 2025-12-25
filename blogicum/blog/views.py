from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render

from blog.forms import CommentForm, PostForm, ProfileForm
from blog.models import Category, Comment, Post
from blog.utils import posts_pagination, query_post


def index(request):
    """
    Отображает главную страницу блога со списком опубликованных постов.
    
    Returns:
        HttpResponse: Отрендеренный шаблон index.html с пагинированным списком постов.
    """
    page_obj = posts_pagination(request, query_post())
    context = {'page_obj': page_obj}
    return render(request, 'blog/index.html', context)


def category_posts(request, category_slug):
    """
    Отображает посты указанной категории.
    
    Args:
        category_slug (str): URL-слаг категории.
    
    Returns:
        HttpResponse: Страница категории с отфильтрованными постами.
        
    Raises:
        Http404: Если категория не существует или не опубликована.
    """
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True,
    )
    page_obj = posts_pagination(
        request,
        query_post(manager=category.posts)
    )
    context = {'category': category, 'page_obj': page_obj}
    return render(request, 'blog/category.html', context)


def post_detail(request, post_id):
    """
    Отображает детальную страницу поста.
    
    Args:
        post_id (int): Идентификатор поста.
    
    Returns:
        HttpResponse: Страница поста с комментариями и формой добавления комментария.
        
    Примечание:
        Неавторизованные пользователи видят только опубликованные посты.
        Комментарии сортируются от старых к новым.
    """
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        post = get_object_or_404(query_post(), id=post_id)
    comments = post.comments.order_by('created_at')
    form = CommentForm()
    context = {
        'post': post,
        'form': form,
        'comments': comments
    }
    return render(request, 'blog/detail.html', context)


@login_required
def create_post(request):
    """
    Создание нового поста.
    
    Returns:
        HttpResponse: При GET - форма создания поста,
                     при успешном POST - редирект на профиль автора.
    """
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('blog:profile', request.user)
    context = {'form': form}
    return render(request, 'blog/create.html', context)


@login_required
def edit_post(request, post_id):
    """
    Редактирование существующего поста.
    
    Args:
        post_id (int): Идентификатор редактируемого поста.
    
    Returns:
        HttpResponse: Форма редактирования или редирект на страницу поста.
        
    Примечание:
        Только автор поста может его редактировать.
    """
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect('blog:post_detail', post_id)
    form = PostForm(request.POST or None, instance=post)
    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', post_id)
    context = {'form': form}
    return render(request, 'blog/create.html', context)


@login_required
def delete_post(request, post_id):
    """
    Удаление поста.
    
    Args:
        post_id (int): Идентификатор удаляемого поста.
    
    Returns:
        HttpResponse: Форма подтверждения или редирект на главную страницу.
    """
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect('blog:post_detail', post_id)
    if request.method == 'POST':
        post.delete()
        return redirect('blog:index')
    context = {'form': PostForm(instance=post)}
    return render(request, 'blog/create.html', context)


def profile(request, username):
    """
    Отображение профиля пользователя.
    
    Args:
        username (str): Имя пользователя.
    
    Returns:
        HttpResponse: Страница профиля со списком постов пользователя.
    """
    profile = get_object_or_404(User, username=username)
    posts = query_post(manager=profile.posts, filters=profile != request.user)
    page_obj = posts_pagination(request, posts)
    context = {'profile': profile,
               'page_obj': page_obj}
    return render(request, 'blog/profile.html', context)


@login_required
def edit_profile(request):
    """
    Редактирование профиля текущего пользователя.
    
    Returns:
        HttpResponse: Форма редактирования или редирект на профиль.
    """
    form = ProfileForm(request.POST, instance=request.user)
    if form.is_valid():
        form.save()
        return redirect('blog:profile', request.user)
    context = {'form': form}
    return render(request, 'blog/user.html', context)


@login_required
def add_comment(request, post_id):
    """
    Добавление комментария к посту.
    
    Args:
        post_id (int): Идентификатор поста.
    
    Returns:
        HttpResponse: Редирект на страницу поста.
    """
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
    return redirect('blog:post_detail', post_id)


@login_required
def edit_comment(request, post_id, comment_id):
    """
    Редактирование комментария.
    
    Args:
        post_id (int): Идентификатор поста.
        comment_id (int): Идентификатор комментария.
    
    Returns:
        HttpResponse: Форма редактирования или редирект на страницу поста.
    """
    comment = get_object_or_404(Comment, id=comment_id)
    if request.user != comment.author:
        return redirect('blog:post_detail', post_id)
    form = CommentForm(request.POST or None, instance=comment)
    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', post_id)
    context = {'form': form, 'comment': comment}
    return render(request, 'blog/comment.html', context)


@login_required
def delete_comment(request, post_id, comment_id):
    """
    Удаление комментария.
    
    Args:
        post_id (int): Идентификатор поста.
        comment_id (int): Идентификатор комментария.
    
    Returns:
        HttpResponse: Форма подтверждения или редирект на страницу поста.
    """
    comment = get_object_or_404(Comment, id=comment_id)
    if request.user != comment.author:
        return redirect('blog:post_detail', post_id)
    if request.method == "POST":
        comment.delete()
        return redirect('blog:post_detail', post_id)
    context = {'comment': comment}
    return render(request, 'blog/comment.html', context)