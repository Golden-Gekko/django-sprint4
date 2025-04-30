from django import forms

from django.contrib.auth import get_user_model

from blog.models import Post

User = get_user_model()


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        exclude = ('author',)
        widgets = {'pub_date': forms.DateInput(attrs={'type': 'date'})}
