from django import forms
from .models import Post


class CreatePostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group')
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
