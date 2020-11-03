from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from posts.models import Post, Group
from django.urls import reverse

User = get_user_model()


class StaticURLTests(TestCase):
    PRESETS = {
        'username': 'StasBasov',
        'based_urls': {
            'auth': '/auth/login/?next=/new/',
        },
        'text': 'Это текст публикации',
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

    def test_homepage(self):
        response = self.unauthorized_client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)

    def test_force_login(self):
        response = self.authorized_client.get(reverse("new_post"))
        self.assertEqual(response.status_code, 200)

    def test_new_post(self):
        current_posts_count = Post.objects.count()
        response = self.authorized_client.post(
            reverse("new_post"), {
                'text': self.PRESETS['text'], 'group': self.group.pk},
            follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Post.objects.count(), current_posts_count + 1)

    def test_unauthorized_user_newpage(self):
        response = self.unauthorized_client.get(reverse("new_post"))
        self.assertRedirects(response, self.PRESETS['based_urls']['auth'],
                             status_code=302, target_status_code=200)

    def test_profile_page(self):
        response = self.authorized_client.get(
            reverse('profile', args=[self.user]))
        self.assertEqual(response.status_code, 200)
