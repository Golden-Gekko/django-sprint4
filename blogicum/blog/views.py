from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, UpdateView

from .forms import CommentForm, PostForm
from .models import Category, Comment, Post

MAX_POSTS: int = 10
User = get_user_model()


def index(request):
    template = 'blog/index.html'
    paginator = Paginator(Post.published.all(), MAX_POSTS)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, template, {'page_obj': page_obj})


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
    model = User
    fields = ('first_name', 'last_name', 'username', 'email')
    template_name = 'blog/user.html'

    def get_object(self):
        return self.request.user

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile', kwargs={'username': self.request.user.username}
        )


class PostMixin:
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'


class OnlyAuthorMixin(UserPassesTestMixin):

    def test_func(self):
        obj = self.get_object()
        return obj.author == self.request.user


class PostCreateView(LoginRequiredMixin, PostMixin, CreateView):
    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile',
            kwargs={'username': self.request.user.username})


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'

    # def get_object(self):
    #     object = super().get_object()
    #     if self.request.user == object.author or (
    #             object.is_published and object.category.is_published):
    #         raise Http404()
    #     print('6' * 100)
    #     return object

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = self.object.comments.select_related('author')
        return context


class PostEditView(
        LoginRequiredMixin,
        PostMixin,
        OnlyAuthorMixin,
        UpdateView):

    def handle_no_permission(self):
        return redirect(
            reverse_lazy('blog:post_detail', kwargs={'pk': self.object.pk})
        )

    def get_success_url(self):
        return reverse_lazy('blog:post_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_edit'] = True
        return context


class PostDeleteView(LoginRequiredMixin, PostMixin, DeleteView):
    def get_success_url(self):
        return reverse_lazy(
            'blog:profile',
            kwargs={'username': self.request.user.username})


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
        return reverse_lazy('blog:post_detail', args=(self.kwargs['post_id'],))


class CommentEditView(LoginRequiredMixin, OnlyAuthorMixin, UpdateView):
    def get_success_url(self):
        return reverse_lazy('blog:post_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_edit'] = True
        return context

    def handle_no_permission(self):
        return redirect(self.get_success_url())


class CommentDeleteView(LoginRequiredMixin, CommentMixin, DeleteView):
    def get_success_url(self):
        return reverse_lazy('blog:post_detail', kwargs={'pk': self.object.pk})
