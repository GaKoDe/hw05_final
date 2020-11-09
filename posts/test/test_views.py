from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from posts.models import Group, Post, Follow
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

User = get_user_model()


class StaticURLTests(TestCase):
    PRESETS = {
        'username': 'StasBasov',
        'follower': 'Yebojou',
        'unfollower': 'YetAnotheUser',
        'text': 'Это текст публикации',
        'edited_text': 'Изменённый текст публикации',
        'comment': 'Очень умный и оригинальный комментарий,'
                    'который должны все увидеть',
        'small_gif': (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'),
        'error_msg': ("Загрузите правильное изображение. Файл, который вы загр"
                      "узили, поврежден или не является изображением.")
    }

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=cls.PRESETS['username'])
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.follower = User.objects.create_user(
            username=cls.PRESETS['follower'])
        cls.authorized_client_follower = Client()
        cls.authorized_client_follower.force_login(cls.follower)
        cls.unfollower = User.objects.create_user(
            username=cls.PRESETS['unfollower'])
        cls.authorized_client_unfollower = Client()
        cls.authorized_client_unfollower.force_login(cls.unfollower)
        cls.unauthorized_client = Client()
        cls.group = Group.objects.create(
            slug='test', title='test', description='test')
        cls.post = Post.objects.create(
            text=cls.PRESETS['text'], group=cls.group, author=cls.user)

    def check_urls(self, user, post, group):
        return [
            reverse('index'),
            reverse('profile', args=[user]),
            reverse('post_view', args=[user, post]),
            reverse('group_posts', args=[group])
        ]

    def test_posts(self):
        response = self.authorized_client.get(
            reverse('post_view', args=[self.user, self.post.id]))
        self.assertEqual(response.status_code, 200)
        for page in self.check_urls(self.user, self.post.pk, self.group.slug):
            get_page = self.authorized_client.get(page)
            get_page_unauth = self.unauthorized_client.get(page)
            self.assertContains(get_page, self.PRESETS['text'])
            self.assertContains(get_page_unauth, self.PRESETS['text'])

    def test_edit_post(self):
        new_gpoup = Group.objects.create(
            slug='new', title='new', description='new')
        response = self.authorized_client.post(
            reverse('post_edit', args=[self.user, self.group.pk]),
            {
                'text': self.PRESETS['edited_text'],
                'group': new_gpoup.pk
            },
            follow=True)
        self.assertEqual(response.status_code, 200)
        cache.clear()
        for page in self.check_urls(self.user, self.group.pk, new_gpoup.slug):
            get_page = self.authorized_client.get(page)
            get_page_unauth = self.unauthorized_client.get(page)
            self.assertContains(get_page, self.PRESETS['edited_text'])
            self.assertContains(get_page_unauth, self.PRESETS['edited_text'])

    def test_is_img_in_db(self):
        uploaded = SimpleUploadedFile(
            'small.gif', self.PRESETS['small_gif'], content_type='image/gif')
        response = Post.objects.create(
            text=self.PRESETS['text'],
            group=self.group,
            author=self.user,
            image=uploaded)
        get_img = Post.objects.get(pk=response.pk)
        self.assertNotEqual(get_img.image, '')

    def test_pages_for_img(self):
        uploaded = SimpleUploadedFile(
            'small.gif', self.PRESETS['small_gif'], content_type='image/gif')
        response = Post.objects.create(
            text=self.PRESETS['text'],
            group=self.group,
            author=self.user,
            image=uploaded)
        cache.clear()
        for page in self.check_urls(self.user, response.pk, self.group.slug):
            get_page = self.authorized_client.get(page)
            get_page_unauth = self.unauthorized_client.get(page)
            self.assertContains(get_page, '<img')
            self.assertContains(get_page_unauth, '<img')

    def test_load_not_img_protect(self):
        with open('yatube/urls.py', 'rb') as file:
            response = self.authorized_client.post(
                reverse('new_post'), {
                    "text": "Some text", "image": file}, follow=True)
        self.assertFormError(response, 'form', 'image',
                             self.PRESETS['error_msg']
                            )
        self.assertNotContains(response, "test_id")

    def test_index_cache(self):
        get_old_page = self.authorized_client.get(reverse('index'))
        self.assertContains(get_old_page, self.PRESETS['text'])
        get_old_page_unauth = self.unauthorized_client.get(reverse('index'))
        self.assertContains(get_old_page_unauth, self.PRESETS['text'])
        response = self.authorized_client.post(
            reverse(
                'post_edit', args=[
                    self.user, self.group.pk]), {
                'text': self.PRESETS['edited_text']},
            follow=True)
        get_new_page = self.authorized_client.get(reverse('index'))
        get_new_page_unauth = self.unauthorized_client.get(reverse('index'))
        self.assertNotContains(get_new_page, self.PRESETS['edited_text'])
        self.assertNotContains(
            get_new_page_unauth,
            self.PRESETS['edited_text'])
        cache.clear()
        get_newest_page = self.authorized_client.get(reverse('index'))
        get_newest_page_unauth = self.unauthorized_client.get(reverse('index'))
        self.assertContains(get_newest_page, self.PRESETS['edited_text'])
        self.assertContains(
            get_newest_page_unauth,
            self.PRESETS['edited_text'])

    def test_unauth_comment(self):
        response = self.authorized_client.get(
            reverse('post_view', args=[self.user, self.post.id]))
        self.assertEqual(response.status_code, 200)
        make_comment_response = self.unauthorized_client.get(
            reverse("add_comment", args=[self.user, self.post.pk]))
        self.assertRedirects(
            make_comment_response,
            reverse('login') +
            '?next=' +
            reverse('add_comment', args=[self.user, self.post.pk]),
            status_code=302,
            target_status_code=200)

    def test_auth_comment(self):
        response = self.authorized_client.get(
            reverse('post_view', args=[self.user, self.post.id]))
        self.assertEqual(response.status_code, 200)
        make_comment_response = self.authorized_client.post(
            reverse("add_comment", args=[self.user, self.post.pk]),
            {
                'text': self.PRESETS['comment']
            },
            follow=True)
        self.assertContains(make_comment_response, self.PRESETS['comment'])

    def test_unauth_follow(self):
        response = self.unauthorized_client.get(
            reverse("profile_follow", args=[self.user]))
        self.assertRedirects(response,
                             reverse('login') + '?next=' +
                             reverse('profile_follow', args=[self.user]),
                             status_code=302, target_status_code=200)

    def test_auth_follow(self):
        response = self.authorized_client_follower.get(
            reverse("profile_follow", args=[self.user]))
        self.assertRedirects(response,
                             reverse('profile', args=[self.user]),
                             status_code=302, target_status_code=200)
        check_follower_in_db = Follow.objects.filter(
            author__username__contains=self.user,
            user__username__contains=self.follower).first()
        self.assertEqual(check_follower_in_db.user, self.follower)

    def test_auth_unfollow(self):
        response = self.authorized_client_follower.get(
            reverse("profile_follow", args=[self.user]))
        self.assertRedirects(response, reverse('profile', args=[self.user]),
                             status_code=302, target_status_code=200)
        unfollow = self.authorized_client_follower.get(
            reverse("profile_unfollow", args=[self.user]))
        self.assertRedirects(unfollow, reverse('profile', args=[self.user]),
                             status_code=302, target_status_code=200)
        check_follower_in_db = Follow.objects.filter(
            author__username__contains=self.user,
            user__username__contains=self.follower).exists()
        self.assertFalse(check_follower_in_db, False)

    def test_follower(self):
        follow = self.authorized_client_follower.get(
            reverse("profile_follow", args=[self.user]))
        self.assertRedirects(follow, reverse('profile', args=[self.user]),
                             status_code=302, target_status_code=200)
        cache.clear()
        check_follow = self.authorized_client_follower.get(
            reverse('follow_index'))
        self.assertContains(check_follow, self.PRESETS['text'])

    def test_is_unauth_can_follow(self):
        follow = self.authorized_client_follower.get(
            reverse("profile_follow", args=[self.user]))
        self.assertRedirects(follow, reverse('profile', args=[self.user]),
                             status_code=302, target_status_code=200)
        cache.clear()
        un_follow = self.authorized_client_unfollower.get(
            reverse('follow_index'))
        self.assertNotContains(un_follow, self.PRESETS['text'])
