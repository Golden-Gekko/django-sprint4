from django.urls import path

from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.index, name='index'),
    path('posts/<int:post_id>/', views.post_detail, name='post_detail'),
    path(
        'category/<slug:category_slug>/',
        views.category_posts,
        name='category_posts'),
    path('profile/<username>/', views.profile_view, name='profile'),
    path('posts/create/', views.PostCreateView.as_view(), name='create_post'),
]
