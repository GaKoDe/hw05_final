from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from posts.models import Group, Post, Follow
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from .presets import PRESETS as p

User = get_user_model()


class StaticURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=p['username'])
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.follower = User.objects.create_user(
            username=p['follower'])
        cls.authorized_client_follower = Client()
        cls.authorized_client_follower.force_login(cls.follower)
        cls.unfollower = User.objects.create_user(username=p['unfollower'])
        cls.authorized_client_unfollower = Client()
        cls.authorized_client_unfollower.force_login(cls.unfollower)
        cls.unauthorized_client = Client()
        cls.group = Group.objects.create(
            slug='test', title='test', description='test')
        cls.post = Post.objects.create(text=p['text'], group=cls.group, author=cls.user)

    def check_urls(self, user, post, group):
        return [
            reverse('index'), reverse(
                'profile', args=[user]), reverse(
                'post_view', args=[
                    user, post]), reverse(
                    'group_posts', args=[group])]

    def test_posts(self):
        response = self.authorized_client.get(reverse('post_view', args=[self.user,self.post.id]))
        self.assertEqual(response.status_code, 200)
        cache.clear()
        for page in self.check_urls(self.user, 1, self.group.slug):
            get_page = self.authorized_client.get(page)
            get_page_unauth = self.unauthorized_client.get(page)
            self.assertContains(get_page, p['text'])
            self.assertContains(get_page_unauth, p['text'])

    def test_edit_post(self):
        new_gpoup = Group.objects.create(
            slug='new', title='new', description='new')
        response = self.authorized_client.post(
            reverse(
                'post_edit', args=[
                    self.user, self.group.pk]), {
                'text': p['edited_text'], 'group': new_gpoup.pk},
            follow=True)
        self.assertEqual(response.status_code, 200)
        cache.clear()
        for page in self.check_urls(self.user, self.group.pk, new_gpoup.slug):
            get_page = self.authorized_client.get(page)
            get_page_unauth = self.unauthorized_client.get(page)
            self.assertContains(get_page, p['edited_text'])
            self.assertContains(get_page_unauth, p['edited_text'])

    def test_is_img_in_db(self):
        uploaded = SimpleUploadedFile(
            'small.gif', p['small_gif'], content_type='image/gif')
        response = self.authorized_client.post(
            reverse("new_post"), {
                'text': p['text'], 'group': self.group.pk,
                'image': uploaded},
            follow=True)
        self.assertEqual(response.status_code, 200)
        get_img = Post.objects.get(pk=2)
        self.assertNotEqual(get_img.image, '')

    def test_page_for_img(self):
        main_page = reverse('index')
        uploaded = SimpleUploadedFile(
            'small.gif', p['small_gif'], content_type='image/gif')
        response = Post.objects.create(text=p['text'], group=self.group, author=self.user, image=uploaded)
        cache.clear()
        get_page = self.authorized_client.get(main_page)
        get_page_unauth = self.unauthorized_client.get(main_page)
        self.assertContains(get_page, '<img')
        self.assertContains(get_page_unauth, '<img')

    def test_pages_for_img(self):
        uploaded = SimpleUploadedFile(
            'small.gif', p['small_gif'], content_type='image/gif')
        response = Post.objects.create(text=p['text'], group=self.group, author=self.user, image=uploaded)
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
            self.assertNotContains(response, "test_id")

    def test_index_cache(self):
        # Тест работает но я не понимаю почему так.
        # Спросить на ревью
        with self.assertNumQueries(7):
            response = self.authorized_client.get(reverse("index"))
            self.assertEqual(response.status_code, 200)
            response = self.authorized_client.get(reverse("index"))
            self.assertEqual(response.status_code, 200)

    def test_unauth_comment(self):
        response = self.authorized_client.get(reverse('post_view', args=[self.user,self.post.id]))
        self.assertEqual(response.status_code, 200)
        make_comment_response = self.unauthorized_client.get(
            reverse("add_comment", args=[self.user, self.post.pk]))
        self.assertRedirects(
            make_comment_response,
            reverse('login') +
            '?next=' +
            reverse(
                'add_comment',
                args=[
                    self.user,
                    self.post.pk]),
            status_code=302,
            target_status_code=200)

    def test_auth_comment(self):
        response = self.authorized_client.get(reverse('post_view', args=[self.user,self.post.id]))
        self.assertEqual(response.status_code, 200)
        make_comment_response = self.authorized_client.post(
            reverse("add_comment", args=[self.user, self.post.pk]), {
                'text': p['comment']},
            follow=True)
        self.assertContains(make_comment_response, p['comment'])

    def test_unauth_follow(self):
        response = self.unauthorized_client.get(
            reverse("profile_follow", args=[self.user]))
        self.assertRedirects(response, reverse('login') + '?next=' +
                             reverse('profile_follow', args=[self.user]),
                             status_code=302, target_status_code=200)

    def test_auth_follow(self):
        response = self.authorized_client_follower.get(
            reverse("profile_follow", args=[self.user]))
        self.assertRedirects(response, reverse('profile', args=[self.user]),
                             status_code=302, target_status_code=200)
        check_follower_in_db = Follow.objects.filter(
            author__username__icontains=self.user,
            user__username__icontains=self.follower)
        self.assertEqual(check_follower_in_db[0].user, self.follower)

    def test_auth_unfollow(self):
        response = self.authorized_client_follower.get(
            reverse("profile_follow", args=[self.user]))
        self.assertRedirects(response, reverse('profile', args=[self.user]),
                             status_code=302, target_status_code=200)
        unfollow = self.authorized_client_follower.get(
            reverse("profile_unfollow", args=[self.user]))
        self.assertRedirects(unfollow, reverse('profile', args=[self.user]),
                             status_code=302, target_status_code=200)
        check_follower_in_db = check_follower_in_db = Follow.objects.filter(
            author__username__icontains=self.user,
            user__username__icontains=self.follower)
        self.assertEqual(check_follower_in_db.count(), 0)

    def test_follower(self):
        response = self.authorized_client.get(reverse('post_view', args=[self.user,self.post.id]))
        follow = self.authorized_client_follower.get(
            reverse("profile_follow", args=[self.user]))
        self.assertRedirects(follow, reverse('profile', args=[self.user]),
                             status_code=302, target_status_code=200)
        check_follow = self.authorized_client_follower.get(
            reverse('follow_index'))
        self.assertContains(check_follow, p['text'])
        cache.clear()
        un_follow = self.authorized_client_unfollower.get(
            reverse('follow_index'))
        self.assertNotContains(un_follow, p['text'])
