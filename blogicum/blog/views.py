from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DetailView, UpdateView

from .forms import CommentForm, PostForm
from .models import Category, Comment, Post

MAX_POSTS: int = 10
User = get_user_model()


def get_paginator_page(posts, request, max_posts=MAX_POSTS):
    paginator = Paginator(posts, max_posts)
    return paginator.get_page(request.GET.get('page'))


def index(request):
    template = 'blog/index.html'
    page_obj = get_paginator_page(posts=Post.published.all(), request=request)
    return render(request, template, {'page_obj': page_obj})


def category_posts(request, category_slug):
    template = 'blog/category.html'
    category = get_object_or_404(
        Category,
        is_published=True,
        slug=category_slug
    )
    page_obj = get_paginator_page(
        posts=category.posts(manager='published').all(),
        request=request
    )
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
    page_obj = get_paginator_page(posts=posts, request=request)
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
        return reverse(
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

    def get_object(self, queryset=None):
        object = super().get_object()
        if self.request.user == object.author or (
                object.is_published and object.category.is_published):
            return object
        raise Http404()

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
    pk_url_kwarg = 'post_id'

    def get_success_url(self):
        post_id = self.kwargs.get('pk') or self.request.POST.get('id')
        return reverse_lazy(
            'blog:post_detail',
            kwargs={self.pk_url_kwarg: post_id}
        )

    def handle_no_permission(self):
        return redirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_edit'] = True
        return context


@login_required
def delete_post(request, post_id):
    instance = get_object_or_404(Post, pk=post_id, author=request.user)
    if request.method == 'POST':
        instance.delete()
        return redirect('blog:profile', request.user)
    return render(
        request,
        'blog/create.html',
        {'form': PostForm(instance=instance)})


class CommentMixin:
    model = Comment
    fields = ('text',)
    template_name = 'blog/comment.html'


class CommentCreateView(LoginRequiredMixin, CommentMixin, CreateView):
    def form_valid(self, form):
        comment = form.save(commit=False)
        comment.post = get_object_or_404(Post, id=self.kwargs.get('post_id'))
        comment.author = self.request.user
        comment.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('blog:post_detail', args=(self.kwargs['post_id'],))


class CommentEditView(
        LoginRequiredMixin,
        OnlyAuthorMixin,
        CommentMixin,
        UpdateView):
    pk_url_kwarg = 'comment_id'

    def get_success_url(self):
        post_id = (
            self.kwargs.get('post_id')
            or self.request.POST.get('post_id'))
        return reverse_lazy('blog:post_detail', kwargs={'post_id': post_id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_edit'] = True
        return context

    def handle_no_permission(self):
        return redirect(self.get_success_url())


@login_required
def delete_comment(request, post_id, comment_id):
    instance = get_object_or_404(
        Comment,
        id=comment_id,
        author__username=request.user)
    if request.method == 'POST':
        instance.delete()
        return redirect('blog:post_detail', post_id)
    return render(
        request,
        'blog/comment.html',
        {'comment': instance})
