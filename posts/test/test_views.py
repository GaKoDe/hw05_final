from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from posts.models import Group
from django.urls import reverse

User = get_user_model()


class StaticURLTests(TestCase):
    PRESETS = {
        'username': 'StasBasov',
        'text': 'Это текст публикации',
        'edited_text': 'Изменённый текст публикации',
    }

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=cls.PRESETS['username'])
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.unauthorized_client = Client()
        cls.group = Group.objects.create(
            slug='test', title='test', description='test')

    def check_urls(self, user, post, group):
        return [
            reverse('index'), reverse(
                'profile', args=[user]), reverse(
                'post', args=[
                    user, post]), reverse(
                    'group_posts', args=[group])]

    def test_posts(self):
        response = self.authorized_client.post(
            reverse("new_post"), {
                'text': self.PRESETS['text'], 'group': self.group.pk},
            follow=True)
        self.assertEqual(response.status_code, 200)
        for page in self.check_urls(self.user, 1, self.group.slug):
            get_page = self.authorized_client.get(page)
            get_page_unauth = self.unauthorized_client.get(page)
            self.assertContains(get_page, self.PRESETS['text'])
            self.assertContains(get_page_unauth, self.PRESETS['text'])

    def test_edit_post(self):
        create_post = self.authorized_client.post(
            reverse("new_post"), {
                'text': self.PRESETS['text'], 'group': self.group.pk},
            follow=True)
        self.assertEqual(create_post.status_code, 200)
        new_gpoup = Group.objects.create(
            slug='new', title='new', description='new')
        response = self.authorized_client.post(
            reverse(
                'post_edit', args=[
                    self.user, 1]), {
                'text': self.PRESETS['edited_text'], 'group': new_gpoup.pk},
            follow=True)
        self.assertEqual(response.status_code, 200)
        for page in self.check_urls(self.user, 1, new_gpoup.slug):
            get_page = self.authorized_client.get(page)
            get_page_unauth = self.unauthorized_client.get(page)
            self.assertContains(get_page, self.PRESETS['edited_text'])
            self.assertContains(get_page_unauth, self.PRESETS['edited_text'])
