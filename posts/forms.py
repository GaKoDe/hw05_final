from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('group', 'text', 'image')
        labels = {
            'text': 'Текст',
            'group': 'Группа',
            }
        help_texts = {
            'text': 'Напишите текст поста',
            'group': 'Выбирите группу для поста (Необизательно)',
            }

    def clean_subject(self):
        data = self.cleaned_data['text']
        if not data:
            raise forms.ValidationError("Заполните данное поле")
        return data


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        labels = {
            'text': 'Текст комментария обезателен',
            }
        help_texts = {
            'text': 'Напишите текст комментария',
            }

    def clean_subject(self):
        data = self.cleaned_data['text']
        if not data:
            raise forms.ValidationError("Заполните данное поле")
        return data
