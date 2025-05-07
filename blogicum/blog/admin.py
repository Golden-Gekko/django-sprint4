from django.contrib import admin
from django.contrib.auth.models import Group

from .models import Category, Comment, Location, Post


class PostInline(admin.TabularInline):
    model = Post
    extra = 0
    fields = (
        'title',
        'pub_date',
        'author',
        'location',
        'category',
        'is_published'
    )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    inlines = (
        PostInline,
    )
    list_display = (
        'title',
        'slug',
        'is_published',
        'created_at'
    )
    list_editable = ('is_published',)
    search_fields = ('title',)


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    inlines = (
        PostInline,
    )
    list_display = (
        'name',
        'is_published',
        'created_at'
    )
    list_editable = ('is_published',)
    search_fields = ('name',)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'pub_date',
        'author',
        'location',
        'category',
        'is_published',
        'created_at'
    )
    list_editable = (
        'location',
        'category',
        'is_published'
    )
    search_fields = ('title',)
    list_filter = (
        'category',
        'author'
    )


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = (
        'author',
        'post',
        'text',
        'created_at'
    )
    list_editable = (
        'text',
    )
    search_fields = ('text',)


admin.site.unregister(Group)
admin.site.empty_value_display = 'Не задано'
