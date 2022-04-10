from http import HTTPStatus
import tempfile
import shutil

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.models import Post, Group, Comment

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsCreateFormTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.new_group = Group.objects.create(
            title='SuperNewGroupTitle',
            slug='super_group_slug',
            description='NewDescriptionSuperGroup'
        )

        cls.post = Post.objects.create(author=cls.user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_post_create(self):
        """Добавляем пост в базу данных."""
        posts_count = Post.objects.count()
        response = self.guest_client.post(reverse('posts:post_create'), )
        self.assertRedirects(response, '/auth/login/?next=/create/')

        image_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3b'
        )
        uploaded = SimpleUploadedFile(
            name='image.gif',
            content=image_gif,
            content_type='image/gif',
        )
        form_data = {
            'group': self.new_group.id,
            'text': '#2 Super newest testing texxxxt',
            'image': uploaded
        }

        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response,
                             reverse('posts:profile',
                                     kwargs={'username': self.user.username}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(Post.objects.all()[0].group.id,
                         form_data['group'])
        self.assertEqual(Post.objects.all()[0].image.url.split('/')[-1],
                         form_data['image'].name)
        self.assertTrue(Post.objects.filter(
            text='#2 Super newest testing texxxxt',
            image='posts/image.gif'
        ).exists())

    def test_post_edit(self):
        """Редактируем пост в базе данных."""
        print(Post.objects.all())
        post1 = Post.objects.all()[0]
        response = self.guest_client.get(
            reverse('posts:post_edit', args=[post1.id])
        )
        self.assertRedirects(response, '/auth/login/?next=/posts/1/edit/')

        response = self.authorized_client.get(
            reverse('posts:post_edit', args=[post1.id])
        )
        self.assertEqual(response.status_code, HTTPStatus.OK.value)

        form_data = {
            'text': '#2 AfterEdit--Super newest testing texxxxt',
            'group': self.new_group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', args=[post1.id]),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:post_detail',
                                               args=[post1.id]))
        self.assertEqual(form_data['text'], Post.objects.all()[0].text)

    def test_comments_create(self):
        """
        Проверка комментирования авторизованным и
        не авторизованным пользователем.
        """
        comments_count = Comment.objects.count()
        id = self.post.id

        form_data = {
            'text': '#1 Commeeeeent',
        }
        response = self.guest_client.post(
            reverse('posts:add_comment', args=[id]))
        self.assertRedirects(response,
                             '/auth/login/?next=%2Fposts%2F1%2Fcomment')

        response = self.authorized_client.post(
            reverse('posts:add_comment', args=[id]),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:post_detail', args=[id]))
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertEqual(Comment.objects.all()[0].text, form_data['text'])
