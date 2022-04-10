import tempfile
import shutil

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.models import Group, Post, Follow
from posts.forms import PostForm

User = get_user_model()
per_page = settings.PERPAGE
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostVIEWSTest(TestCase):

    @classmethod
    def setUpClass(cls):
        """ Создаем тестовые экземпляры постов."""
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='test_group',
            slug='test_slug',
            description='TestingDescription'
        )
        cls.new_group = Group.objects.create(
            title='new_group',
            slug='new_slug',
            description='NewDescription'
        )
        image_jpg = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='image.jpg',
            content=image_jpg,
            content_type='image/jpg'
        )

        post_list = [Post(author=cls.user,
                          text=f'#_{i}__OldTestTextTextTextText',
                          group=cls.group,
                          image=uploaded,
                          ) for i in range(1, 10)]
        Post.objects.bulk_create(post_list)

        Post.objects.create(author=cls.user,
                            text='NewestTestTextTextTextText',
                            group=cls.new_group,
                            )
        cls.posts = Post.objects.all().order_by('-id')
        cls.posts_gr = Post.objects.filter(group=cls.group).order_by('-id')
        cls.post_n_gr = Post.objects.filter(group=cls.new_group)
        cls.posts_prf = Post.objects.filter(author=cls.user).order_by('-id')

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        """Создаем авторизованного и неавторизованного клиента"""
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """Проверка на соответствие URL-адреса
        соответствующему шаблону.
        """
        templates_page_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html':
                reverse('posts:group_list',
                        kwargs={'slug': self.group.slug}),
            'posts/profile.html':
                reverse('posts:profile',
                        kwargs={'username': self.user.username}),
            'posts/create_post.html': reverse('posts:post_create'),
        }
        for template, reverse_name in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
        for post in self.posts:
            response_det = self.guest_client.get(
                reverse('posts:post_detail', args=[post.id]))
            self.assertTemplateUsed(response_det, 'posts/post_detail.html')
            response_aut = self.author_client.get(
                reverse('posts:post_edit', kwargs={'post_id': f'{post.id}'}))
            self.assertTemplateUsed(response_aut, 'posts/create_post.html')

    def test_index_correct_context(self):
        """Проверка контекста шаблона index.html."""
        response = self.guest_client.get(reverse('posts:index'))
        post = response.context['posts'].order_by('-id')
        for i in range(len(self.posts)):
            print(post[i].image)
            self.assertEqual(post[i].text, self.posts[i].text)
            self.assertEqual(post[i].id, self.posts[i].id)
            self.assertEqual(post[i].image, self.posts[i].image)
        self.assertEqual(response.context['page_title'],
                         'Последние обновления на сайте')

    def test_group_correct_context(self):
        """Проверка контекста шаблона group_list.html."""
        response = self.guest_client.get(reverse('posts:group_list',
                                                 kwargs={
                                                     'slug': self.group.slug}))
        post = response.context['posts'].order_by('-id')
        for i in range(len(self.posts_gr)):
            self.assertEqual(post[i].group.title,
                             self.group.title)
            self.assertEqual(post[i].text,
                             self.posts_gr[i].text)
            self.assertEqual(response.context['page_title'],
                             f'Записи сообщества {self.group.slug}')
            self.assertEqual(response.context['gr_descr'],
                             f'{self.group.description}')

    def test_profile_correct_context(self):
        """Проверка контекста шаблона profile.html."""
        response = self.guest_client. \
            get(reverse('posts:profile',
                        kwargs={'username': self.user}))
        post = response.context['posts'].order_by('-id')
        for i in range(len(self.posts)):
            self.assertEqual(post[i].author.username,
                             f'{self.posts[i].author.username}')
            self.assertEqual(post[i].text,
                             f'{self.posts[i].text}')

    def test_post_detail_correct_context(self):
        """Проверка контекста шаблона post_detail.html."""
        for i in range(len(self.posts)):
            response = self.guest_client. \
                get(reverse('posts:post_detail',
                            args=[self.posts[i].id]))
            self.assertEqual(response.context['post'], self.posts[i])
            self.assertEqual(response.context['id'], self.posts[i].id)
            self.assertEqual(response.context['post'].image,
                             self.posts[i].image)
            self.assertEqual(response.context['page_title'],
                             self.posts[i].text[:30])

    def posts_forms(self, response):
        """Модуль проверки форм постов."""
        PostForm.fields = {'text': forms.fields.CharField,
                           'group': forms.fields.ChoiceField,
                           }
        for value, expected in PostForm.fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_correct_form(self):
        """Проверка формы редактирования поста."""
        for i in range(len(self.posts)):
            response = self.author_client. \
                get(reverse('posts:post_edit',
                            args=[self.posts[i].id]))
            self.assertEqual(response.context['post'], self.posts[i])
            self.assertEqual(response.context['id'], self.posts[i].id)
            self.assertEqual(response.context['is_edit'], True)
        self.posts_forms(response)

    def test_post_create_correct_form(self):
        """Проверка формы создания поста."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        self.posts_forms(response)

    def test_new_post_correct_context(self):
        """Проверка контекста нового поста."""
        response = self.author_client.get(reverse('posts:index'))
        new_post = response.context['posts'].order_by('-id')[0]
        self.assertEqual(new_post.text, self.posts[0].text)
        self.assertEqual(new_post.id, self.posts[0].id)

        response = self.author_client. \
            get(reverse('posts:group_list',
                        kwargs={'slug': self.new_group.slug}))
        post_new_gr = response.context['page_obj'][0]
        self.assertEqual(post_new_gr.text, self.post_n_gr[0].text)
        self.assertEqual(post_new_gr.id, self.post_n_gr[0].id)
        self.assertEqual(post_new_gr.group.title,
                         self.post_n_gr[0].group.title)

        response = self.author_client. \
            get(reverse('posts:profile',
                        kwargs={'username': self.user.username}))
        post_prf = response.context['posts'].order_by('-id')[0]
        self.assertEqual(post_prf.author.username,
                         self.posts_prf[0].author.username)
        self.assertEqual(post_prf.text, self.posts_prf[0].text)

    def test_cache_index_page(self):
        """Тест для проверки кеширования главной страницы."""
        response = self.guest_client.get(reverse('posts:index'))
        self.posts[0].delete()
        response_afdel = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(response.content, response_afdel.content)
        cache.clear()
        response_cl = self.guest_client.get(reverse('posts:index'))
        self.assertNotEqual(response_cl.content, response_afdel.content)

    def sub_unsub(self, author, follower, url):
        self.authorized_client.force_login(follower)
        self.authorized_client.get(
            reverse(url, kwargs={'username': author.username}))
        return self.authorized_client.get(reverse('posts:follow_index'))

    def test_authuser_can_follow_author(self):
        """
        Тест на подписку/отписку на авторов.
        На (не)появление новой записи в ленте (не)подписчика.
        """
        new_author = User.objects.create(username='new_author')
        new_follower = User.objects.create(username='follower')

        # подписываемся на new_author
        subscr = self.sub_unsub(new_author, new_follower,
                                'posts:profile_follow')
        new_post = Post.objects.create(author=new_author,
                                       text='new_author teeeext')
        count_folauthors = Follow.objects.filter(author=new_author,
                                                 user=new_follower).count()
        self.assertEqual(subscr.context['favt'], count_folauthors)
        self.assertEqual(subscr.context['posts'][0].author, new_author)
        self.assertEqual(subscr.context['posts'][0].text, new_post.text)

        # отписываемся от new_author
        unsubscr = self.sub_unsub(
            new_author, new_follower, 'posts:profile_unfollow')
        self.assertNotEqual(unsubscr.context['favt'], count_folauthors)

        # подписываемся на self.user
        self.sub_unsub(self.user, new_follower, 'posts:profile_follow')
        self.assertNotEqual(unsubscr.context['posts'][0].author, new_author)
        self.assertNotEqual(subscr.context['posts'][0].text, new_post.text)


class PaginatorViewsTest(TestCase):

    @classmethod
    def setUpClass(cls):
        """ Создаем тестовые экземпляры постов."""
        super().setUpClass()
        cls.user = User.objects.create_user(username='Pagin')
        cls.pag_group = Group.objects.create(
            title='pag_test_group',
            slug='pag_test_slug',
            description='Pag_TestingDescription'
        )

        pag_post_list = [Post(author=cls.user,
                              text=f'#_{i}__Pag_TestTextTextTextText',
                              group=cls.pag_group,
                              ) for i in range(13)]

        Post.objects.bulk_create(pag_post_list)
        cls.pag_posts = Post.objects.all()

    def setUp(self):
        """Создаем авторизованного и неавторизованного клиента"""
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(self.user)

    def test_first_page_contains_ten_records(self):
        """Проверка: количество постов на первой странице равно 10."""
        response = self.author_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), per_page)

        response = self.author_client. \
            get(reverse('posts:group_list',
                        kwargs={'slug': self.pag_group.slug}))
        self.assertEqual(len(response.context['page_obj']), per_page)

        response = self.author_client. \
            get(reverse('posts:profile',
                        kwargs={'username': self.user}))
        self.assertEqual(len(response.context['page_obj']), per_page)

    def test_second_page_contains_three_records(self):
        """Проверка: количество постов на второй странице равно 3."""
        response = self.author_client.get(reverse('posts:index')
                                          + '?page=2')
        self.assertEqual(len(response.context['page_obj']),
                         len(self.pag_posts) - per_page)

        response = self.author_client. \
            get(reverse('posts:group_list',
                        kwargs={'slug': self.pag_group.slug})
                + '?page=2')
        self.assertEqual(len(response.context['page_obj']),
                         len(self.pag_posts) - per_page)

        response = self.author_client. \
            get(reverse('posts:profile',
                        kwargs={'username': self.user})
                + '?page=2')
        self.assertEqual(len(response.context['page_obj']),
                         len(self.pag_posts) - per_page)
