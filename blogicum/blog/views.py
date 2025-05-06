from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, UpdateView

from .forms import CommentForm, PostForm
from .models import Category, Comment, Post

MAX_POSTS: int = 10
User = get_user_model()


def index(request):
    """
    Главная страница блога, отображающая список последних публикаций.
    Функция отображает главную страницу блога, на которой показываются
    опубликованные посты с возможностью пагинации. Количество постов на
    странице определяется константой MAX_POSTS.

    Args:
        request: HTTP-запрос

    Returns:
        HttpResponse: Отрендеренный HTML-шаблон с пагинацией публикаций
    """
    template = 'blog/index.html'
    paginator = Paginator(Post.published.all(), MAX_POSTS)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, template, {'page_obj': page_obj})


def category_posts(request, category_slug):
    """
    Отображает список публикаций по указанной категории.

    Args:
        request: HTTP-запрос
        category_slug: Слаг категории для фильтрации публикаций

    Returns:
        HttpResponse: Отрендеренный HTML-шаблон с публикациями категории

    Raises:
        Http404: Если категория не найдена или не опубликована
    """
    template = 'blog/category.html'
    category = get_object_or_404(
        Category,
        is_published=True,
        slug=category_slug
    )
    paginator = Paginator(category.posts(manager='published').all(), MAX_POSTS)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(
        request,
        template,
        {
            'category': category,
            'page_obj': page_obj
        }
    )


def profile_view(request, username):
    """
    Отображает профиль пользователя с его публикациями.

    Особенности:
        - Для текущего пользователя показываются все его публикации
        - Для других пользователей показываются только опубликованные посты
        - Реализована пагинация постов

    Args:
        request: HTTP-запрос
        username: Имя пользователя, чей профиль нужно отобразить

    Returns:
        HttpResponse: Отрендеренный HTML-шаблон с профилем пользователя

    Raises:
        Http404: Если пользователь не найден
    """
    user = get_object_or_404(User, username=username)
    if request.user.username == username:
        posts = user.posts.all()
    else:
        posts = user.posts(manager='published').all()
    paginator = Paginator(posts, MAX_POSTS)
    page_obj = paginator.get_page(request.GET.get('page'))
    context = {
        'profile': user,
        'page_obj': page_obj,
    }
    return render(request, 'blog/profile.html', context)


class ProfileEditView(LoginRequiredMixin, UpdateView):
    """Представление для редактирования профиля пользователя."""

    model = User
    fields = ('first_name', 'last_name', 'username', 'email')
    template_name = 'blog/user.html'

    def get_object(self):
        """Возвращает текущий пользовательский объект для редактирования."""
        return self.request.user

    def get_success_url(self):
        """Возвращает URL для перенаправления после успешного сохранения."""
        return reverse_lazy(
            'blog:profile', kwargs={'username': self.request.user.username}
        )


class PostMixin:
    """Базовый миксин для представлений, работающих с моделями постов."""

    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'


class OnlyAuthorMixin(UserPassesTestMixin):
    """Миксин для проверки прав доступа только для автора объекта."""

    def test_func(self):
        """Проверяет, является ли текущий пользователь автором объекта."""
        obj = self.get_object()
        return obj.author == self.request.user


class PostCreateView(LoginRequiredMixin, PostMixin, CreateView):
    """Представление для создания нового поста."""

    def form_valid(self, form):
        """
        Устанавливает автора поста как текущего пользователя перед
        сохранением.
        """
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        """Возвращает URL для перенаправления после успешного создания поста."""
        return reverse_lazy(
            'blog:profile',
            kwargs={'username': self.request.user.username})


class PostDetailView(DetailView):
    """Представление для отображения детальной информации о посте."""

    model = Post
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'

    def get_object(self):
        """
        Получает объект поста и проверяет права доступа.

        Returns:
            Post: объект поста, если доступ разрешен

        Raises:
            Http404: если доступ запрещен
        """
        object = super().get_object()
        if self.request.user == object.author or (
                object.is_published and object.category.is_published):
            return object
        raise Http404()

    def get_context_data(self, **kwargs):
        """Добавляет дополнительные данные в контекст шаблона."""
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = self.object.comments.select_related('author')
        return context


class PostEditView(
        LoginRequiredMixin,
        PostMixin,
        OnlyAuthorMixin,
        UpdateView):
    """Представление для редактирования существующего поста."""

    pk_url_kwarg = 'post_id'

    def get_success_url(self):
        """Возвращает URL для перенаправления после успешного редактирования."""
        post_id = self.kwargs.get('pk') or self.request.POST.get('id')
        return reverse_lazy('blog:post_detail', kwargs={'post_id': post_id})

    def handle_no_permission(self):
        """
        Обрабатывает случай, когда у пользователя нет прав на редактирование.
        Перенаправляет на страницу детального просмотра поста.
        """
        return redirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        """Добавляет дополнительные данные в контекст шаблона."""
        context = super().get_context_data(**kwargs)
        context['is_edit'] = True
        return context


@login_required
def delete_post(request, post_id):
    """
    Функция для удаления поста.

    Особенности:
    - Требует авторизации пользователя
    - Проверяет, является ли пользователь автором поста
    - Показывает форму подтверждения удаления
    - После удаления перенаправляет на профиль пользователя

    Args:
        request: объект запроса
        post_id: идентификатор удаляемого поста

    Returns:
        HttpResponse:
        - Форма подтверждения удаления (GET запрос)
        - Перенаправление на профиль после удаления (POST запрос)
        - Ошибка 404, если пост не найден или пользователь не является автором
    """
    instance = get_object_or_404(
        Post, pk=post_id, author__username=request.user)
    if request.method == 'POST':
        instance.delete()
        return redirect('blog:profile', request.user)
    return render(
        request,
        'blog/create.html',
        {'form': PostForm(instance=instance)})


class CommentMixin:
    """Базовый миксин для работы с комментариями."""

    model = Comment
    fields = ('text',)
    template_name = 'blog/comment.html'


class CommentCreateView(LoginRequiredMixin, CommentMixin, CreateView):
    """Представление для создания нового комментария."""

    def form_valid(self, form):
        """
        Сохраняет комментарий с дополнительными данными.
        Связывает коментарий с автором комментария и записью о посте
        """
        comment = form.save(commit=False)
        comment.post = get_object_or_404(Post, id=self.kwargs.get('post_id'))
        comment.author = self.request.user
        comment.save()
        return super().form_valid(form)

    def get_success_url(self):
        """
        Возвращает URL для перенаправления после успешного создания
        комментария.
        """
        return reverse_lazy('blog:post_detail', args=(self.kwargs['post_id'],))


class CommentEditView(
        LoginRequiredMixin,
        OnlyAuthorMixin,
        CommentMixin,
        UpdateView):
    """Представление для редактирования существующего комментария."""

    pk_url_kwarg = 'comment_id'

    def get_success_url(self):
        """Возвращает URL для перенаправления после успешного редактирования."""
        post_id = (
            self.kwargs.get('post_id')
            or self.request.POST.get('post_id'))
        return reverse_lazy('blog:post_detail', kwargs={'post_id': post_id})

    def get_context_data(self, **kwargs):
        """Добавляет дополнительные данные в контекст шаблона."""
        context = super().get_context_data(**kwargs)
        context['is_edit'] = True
        return context

    def handle_no_permission(self):
        """
        Обрабатывает случай, когда у пользователя нет прав на редактирование.
        Перенаправляет на страницу детального просмотра поста.
        """
        return redirect(self.get_success_url())


@login_required
def delete_comment(request, post_id, comment_id):
    """
    Функция для удаления комментария.

    Особенности:
    - Требует авторизации пользователя
    - Проверяет, является ли пользователь автором комментария
    - Показывает форму подтверждения удаления
    - После удаления перенаправляет на страницу поста

    Args:
        request: объект запроса
        post_id: идентификатор поста, к которому привязан комментарий
        comment_id: идентификатор удаляемого комментария

    Returns:
        HttpResponse:
        - Форма подтверждения удаления (GET запрос)
        - Перенаправление на страницу поста после удаления (POST запрос)
        - 404 ошибка, если комментарий не найден или пользователь не является
          автором
    """
    instance = get_object_or_404(
        Comment,
        id=comment_id,
        author__username=request.user)
    if request.method == "POST":
        instance.delete()
        return redirect('blog:post_detail', post_id)
    return render(
        request,
        'blog/comment.html',
        {'comment': instance})
