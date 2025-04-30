from django.shortcuts import get_object_or_404, render

from .models import Category, Post

MAX_POSTS: int = 5


def index(request):
    template = 'blog/index.html'
    post_list = Post.published.all()[:MAX_POSTS]
    return render(request, template, {'post_list': post_list})


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

    return render(
        request,
        template,
        {
            'category': category,
            'post_list': category.posts(manager='published').all()
        }
    )
