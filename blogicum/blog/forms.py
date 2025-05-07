from django import forms
from django.contrib.auth import get_user_model

from blog.models import Comment, Post

User = get_user_model()
COMMENT_FIELD_ROW_COUNT = 4
COMMENT_FIELD_COLS_COUNT = 60


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        exclude = ('author',)
        widgets = {
            'pub_date': forms.DateInput(
                format='%d-%m-%Y',
                attrs={'type': 'date'}
            )
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        widgets = {
            'text': forms.Textarea(attrs={
                'rows': COMMENT_FIELD_ROW_COUNT,
                'cols': COMMENT_FIELD_COLS_COUNT
            })
        }
