from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):

    @classmethod
    def setUpClass(cls):
        """ Создаем тестовые экземпляры моделей."""
        super().setUpClass()
        cls.user = User.objects.create(username='auth')
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='Тестовый слаг',
            description='Тестовое описание',

        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Хороший длинный тестовый текст поста'
        )

    def test_models_have_correct_object_names(self):
        """ Проверка на корректность работы у моделей __str__."""
        self.assertEqual(self.post.__str__(), self.post.text[:15])
        self.assertEqual(self.group.__str__(), self.group.title)

    def test_title_verb_help(self):
        """ Проверка verbose_name и help_text модели Post """
        post = self.post
        verb_name_av = post._meta.get_field('author').verbose_name
        verb_name_gr = post._meta.get_field('group').verbose_name
        help_text = post._meta.get_field('group').help_text
        self.assertEqual(verb_name_av, 'Автор')
        self.assertEqual(verb_name_gr, 'Группа')
        self.assertEqual(help_text, 'Группа, к которой будет относиться пост')
