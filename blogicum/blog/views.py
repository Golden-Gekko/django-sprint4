from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, UpdateView

from .forms import PostForm
from .models import Category, Comment, Post

MAX_POSTS: int = 10
User = get_user_model()


def index(request):
    template = 'blog/index.html'
    paginator = Paginator(Post.published.all(), MAX_POSTS)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, template, {'page_obj': page_obj})


def post_detail(request, post_id):
    template = 'blog/detail.html'
    post = get_object_or_404(Post.published, pk=post_id)
    return render(request, template, {'post': post})


def category_posts(request, category_slug):
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
    user = get_object_or_404(User, username=username)
    if request.user.username != username:
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


class PostMixin:
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'


class OnlyAuthorMixin(UserPassesTestMixin):

    def test_func(self):
        obj = self.get_object()
        return obj.author == self.request.user


class PostCreateView(LoginRequiredMixin, PostMixin, CreateView):
    success_url = reverse_lazy(
        'blog:profile',
        kwargs={'username': User.username()})

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostEditView(
        LoginRequiredMixin,
        PostMixin,
        OnlyAuthorMixin,
        UpdateView):

    def handle_no_permission(self):
        return redirect(
            reverse_lazy('post_detail', kwargs={'pk': self.object.pk})
        )

    def get_success_url(self):
        return reverse_lazy('post_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_edit'] = True
        return context


class PostDeleteView(LoginRequiredMixin, PostMixin, DeleteView):
    success_url = reverse_lazy(
        'blog:profile',
        kwargs={'username': User.username()})


class CommentMixin:
    model = Comment
    fields = ('text',)


class CommentCreateView(LoginRequiredMixin, CommentMixin, CreateView):
    def form_valid(self, form):
        comment = form.save(commit=False)
        comment.post = Post.objects.get(pk=self.kwargs['post_id'])
        comment.author = self.request.user
        comment.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('post_detail', args=(self.kwargs['post_id'],))


class CommentEditView(LoginRequiredMixin, OnlyAuthorMixin, UpdateView):
    def handle_no_permission(self):
        return redirect(
            reverse_lazy('post_detail', kwargs={'pk': self.object.pk})
        )

    def get_success_url(self):
        return reverse_lazy('post_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_edit'] = True
        return context


class CommentDeleteView(LoginRequiredMixin, CommentMixin, DeleteView):
    def get_success_url(self):
        return reverse_lazy('post_detail', kwargs={'pk': self.object.pk})
