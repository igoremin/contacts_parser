from django.db import models
from django.core.validators import URLValidator
import datetime
import time
import shutil
import os


def generate_path(instance, filename):
    today = datetime.datetime.today()
    date = today.strftime("%d-%m-%Y__%H-%M-%S")
    new_name = f"{instance.file.name.split('/')[-1]}"
    return f"main_files/{date}__{new_name}"


def generate_path_to_file(instance, filename):
    return f"results_files/{instance.search_name}/{filename}"


def get_len_from_file(path):
    with open(path, 'r') as f:
        all_urls = [row.strip() for row in f.readlines()]
        return len(all_urls)


class FileWithUrls(models.Model):
    file = models.FileField(upload_to=generate_path)
    file_len = models.IntegerField(blank=True, verbose_name='Количество сайтов в файле', default=0)

    class Meta:
        verbose_name = 'Файлы с данными'
        verbose_name_plural = 'Файлы с данными для поиска'

    def __str__(self):
        return self.file.name.split('/')[-1]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.file_len = get_len_from_file(self.file.path)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.file:
            shutil.rmtree(str(self.file.path).rsplit(os.sep, 1)[0])
        super().delete(*args, **kwargs)


class ParserName(models.Model):
    main_file = models.ForeignKey(FileWithUrls, on_delete=models.PROTECT, related_name='parser_names')
    search_name = models.CharField(max_length=200, verbose_name='Название поиска', db_index=True, unique=True)
    start_row = models.IntegerField(blank=True, null=True, verbose_name='Начальная строка для парсинга')
    end_row = models.IntegerField(blank=True, null=True, verbose_name='Конечная строка для парсинга')
    done_urls = models.IntegerField(blank=True, null=True, verbose_name='Количество пройденых сайтов', default=0)
    status = models.BooleanField(verbose_name='True если работа закончена', default=False)
    start_time = models.IntegerField(verbose_name='Время начала', default=time.time)
    result_file = models.FileField(blank=True, verbose_name='Итоговый файл', upload_to=generate_path_to_file)

    class Meta:
        verbose_name = 'Парсинги'
        verbose_name_plural = 'Список парсингов'
        ordering = ['-id']

    def __str__(self):
        return self.search_name

    def save(self, *args, **kwargs):
        if self.pk is None:
            today = datetime.datetime.today()
            date = today.strftime("%d-%m-%Y__%H:%M:%S")
            if ParserName.objects.filter(search_name__iexact=f'{self.search_name}__{date}'):
                self.search_name = f'{self.search_name}__{date}_{int(time.time())}'
            else:
                self.search_name = f'{self.search_name}__{date}'
        super().save(*args, **kwargs)

    def change_result_file(self, *args, **kwargs):
        if self.id:
            old_file = ParserName.objects.get(search_name__iexact=self.search_name).result_file
            if old_file:
                old_file.delete(save=False)
        super().save(*args, **kwargs)

    def add_done_url(self):
        self.done_urls += 1
        super().save()

    def set_done_urls(self, value):
        self.done_urls = value
        super().save()

    def change_status(self, new_status):
        print('CHANGE STATUS')
        self.status = new_status
        super().save()

    def change_start_time(self):
        self.start_time = time.time()
        super().save()

    def delete(self, *args, **kwargs):
        if self.result_file:
            shutil.rmtree(str(self.result_file.path).rsplit(os.sep, 1)[0])
        super().delete(*args, **kwargs)


class PageData(models.Model):
    search_name = models.ForeignKey(ParserName, on_delete=models.CASCADE, related_name='page_dates')
    page_url = models.TextField(validators=[URLValidator()], verbose_name='URL')
    emails = models.TextField(blank=True, verbose_name='Список email')
    phones = models.TextField(blank=True, verbose_name='Список телефонов')
    inn = models.TextField(blank=True, verbose_name='ИНН')
    kpp = models.TextField(blank=True, verbose_name='КПП')
    ogrn = models.TextField(blank=True, verbose_name='ОГРН')
    title = models.TextField(blank=True, verbose_name='Заголовок')
    description = models.TextField(blank=True, verbose_name='Описание')

    class Meta:
        verbose_name = 'Результат'
        verbose_name_plural = 'Результат поиска'
        ordering = ['id']

    def __str__(self):
        return self.page_url


class NoResponseUrls(models.Model):
    search_name = models.ForeignKey(ParserName, on_delete=models.CASCADE, related_name='no_response_urls')
    page_url = models.TextField(validators=[URLValidator()], verbose_name='URL')

    class Meta:
        verbose_name = 'Сайты'
        verbose_name_plural = 'Сайты без ответа'

    def __str__(self):
        return self.page_url


class DoneUrls(models.Model):
    search_name = models.ForeignKey(ParserName, on_delete=models.CASCADE, related_name='response_urls')
    page_url = models.TextField(validators=[URLValidator()], verbose_name='URL')

    class Meta:
        verbose_name = 'Сайты'
        verbose_name_plural = 'Сайты с ответом'

    def __str__(self):
        return self.page_url


class Settings(models.Model):
    pool_workers = models.IntegerField(default=30, verbose_name='Количество потоков')
    number_of_requests = models.IntegerField(default=1, verbose_name='Количество запросов к сайту если нет ответа')
    waiting_time = models.IntegerField(default=5, verbose_name='Время ожидания ответа от сайта')

    class Meta:
        verbose_name = 'Настройки'
        verbose_name_plural = 'Настройки для парсинга контактов'

    def __str__(self):
        return 'Settings'
