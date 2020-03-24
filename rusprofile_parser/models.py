from django.db import models
from contacts_parser.models import PageData, ParserName
import time
import datetime


def generate_path_to_file(instance, filename):
    return f"results_files/rusprofile/{instance.parser_name}/{filename}"


class RusprofileParser(models.Model):
    search_file = models.ForeignKey(ParserName, on_delete=models.SET_NULL, related_name='rusprofile_parser',
                                    verbose_name='Исходные данные для парсинга', null=True)
    file_name = models.CharField(max_length=100, verbose_name='Название парсинга', unique=True)
    result_file = models.FileField(blank=True, verbose_name='Итоговый файл', upload_to=generate_path_to_file)
    key_words = models.TextField(verbose_name='Ключевые слова для поиска')
    number_of_coincidences = models.IntegerField(verbose_name='Количество совпадений', default=2)
    target = models.IntegerField(verbose_name='Количество сайтов для поиска совпадений с кулючами', default=0)
    done_urls = models.IntegerField(blank=True, null=True, verbose_name='Количество пройденых сайтов', default=0)
    start_time = models.IntegerField(blank='Время начала работы', default=time.time)
    status = models.BooleanField(verbose_name='Статус', default=False)

    class Meta:
        verbose_name = 'Парсинги'
        verbose_name_plural = 'Парсинги сайта Rusprofile'
        ordering = ['-id']

    def __str__(self):
        return self.file_name

    def save(self, *args, **kwargs):
        if self.file_name and not self.id:
            today = datetime.datetime.today()
            date = today.strftime("%d-%m-%Y__%H:%M:%S")

            if RusprofileParser.objects.filter(file_name__iexact=f'{self.file_name}__{date}'):
                self.file_name = f'{self.file_name}__{date}_{int(time.time())}'
            else:
                self.file_name = f'{self.file_name}__{date}'
        super().save(*args, **kwargs)

    def change_result_file(self, *args, **kwargs):
        if self.id:
            old_file = RusprofileParser.objects.get(pk=self.pk).result_file
            if old_file:
                old_file.delete(save=False)
        super().save(*args, **kwargs)

    def add_done_url(self):
        self.done_urls += 1
        super().save()

    def change_status(self, new_status):
        self.status = new_status
        super().save()

    def delete(self, *args, **kwargs):
        if self.result_file:
            self.result_file.delete(save=False)
        super().delete(*args, **kwargs)


class RusprofileParserData(models.Model):
    parser_name = models.ForeignKey(RusprofileParser, on_delete=models.CASCADE, related_name='rusprofile_data',
                                    verbose_name='Название парсинга')
    search_data = models.ForeignKey(PageData, on_delete=models.SET_NULL, related_name='rusprofile_data',
                                    verbose_name='Исходные данные', blank=True, null=True)
    company_name = models.TextField(verbose_name='Название компании', blank=True)
    st = models.TextField(verbose_name='Статус компании : активна или закрыта', blank=True)
    ogrn = models.CharField(verbose_name='ОГРН', blank=True, max_length=20)
    inn = models.CharField(verbose_name='ИНН', blank=True, max_length=20)
    kpp = models.CharField(verbose_name='КПП', blank=True, max_length=20)
    reg_date = models.TextField(verbose_name='Дата рагистрации', blank=True)
    address = models.TextField(verbose_name='Адрес', blank=True)
    kap = models.TextField(verbose_name='Капитал', blank=True)
    supervisor = models.TextField(verbose_name='Руководитель', blank=True)
    workers = models.TextField(verbose_name='Количество сотрудников', blank=True)
    nalog_rezhim = models.TextField(verbose_name='Налоговый режим', blank=True)
    company_type = models.TextField(verbose_name='Основной вид деятельности', blank=True)
    status = models.TextField(verbose_name='Статус', blank=True)
    all_founders = models.TextField(verbose_name='Учредители', blank=True)
    revenue = models.TextField(verbose_name='Выручка', blank=True)
    profit = models.TextField(verbose_name='Прибыль', blank=True)
    nalog = models.TextField(verbose_name='Налог', blank=True)

    class Meta:
        verbose_name = 'Данные'
        verbose_name_plural = 'Итоговые данные парсинга Rusprofile'

    def __str__(self):
        return self.company_name


class RusprofileSettings(models.Model):
    pool_workers = models.IntegerField(default=30, verbose_name='Количество потоков')
    waiting_time = models.IntegerField(default=5, verbose_name='Время ожидания ответа от сайта')
    proxy_file = models.FileField(upload_to='proxy_file/', blank=True, verbose_name='Файл с прокси')

    class Meta:
        verbose_name = 'Настройки'
        verbose_name_plural = 'Настройки для парсинга Rusprofile'

    def __str__(self):
        return 'Settings'

    def update(self, *args, **kwargs):
        if self.id:
            old_proxies_file = RusprofileSettings.objects.get(pk=self.pk).proxy_file
            if old_proxies_file:
                old_proxies_file.delete(save=False)
        super().save(*args, **kwargs)
