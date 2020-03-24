from django import forms
from .models import FileWithUrls, Settings, ParserName
from django.core.exceptions import ValidationError


def choice_files():
    all_files = FileWithUrls.objects.all()
    choices = []
    for file in all_files:
        file_name = file.file.name.split('/')[-1]
        choices.append((file_name, f'{file_name} Количество сайтов : {file.file_len}'))
    return choices


class SearchInputForm(forms.Form):

    # class Meta:
    #     model = ParserName
    #     fields = '__all__'
    #
    #     field_classes = {
    #         'search_file': forms.ChoiceField(
    #             label='Файл для поиска',
    #             choices=choice_files(),
    #         ),
    #         'search_name': forms.CharField(
    #             label='Название парсинга',
    #         ),
    #         'start_row': forms.CharField(
    #             label='Начальное значение для парсинга',
    #         ),
    #         'end_row': forms.CharField(
    #             label='Конечное значение для парсинга',
    #         ),
    #     }
    #
    #     widgets = {
    #         'search_file': forms.Select(
    #             attrs={
    #                 'class': 'form-control',
    #                 'placeholder': 'Файл для поиска',
    #             }
    #         ),
    #         'search_name': forms.TextInput(
    #             attrs={
    #                 'class': 'form-control',
    #                 'placeholder': 'Название парсинга',
    #             }
    #         ),
    #         'start_row': forms.NumberInput(
    #             attrs={
    #                 'class': 'form-control',
    #                 'placeholder': 'Первая строка для парсинга',
    #             }
    #         ),
    #         'end_row': forms.NumberInput(
    #             attrs={
    #                 'class': 'form-control',
    #                 'placeholder': 'Последняя строка для парсинга',
    #             }
    #         )
    #     }

    # def clean(self):
    #     cleaned_data = super(SearchInputForm, self).clean()
    #     if cleaned_data.get('search_name') in ['test1']:
    #         raise ValidationError(u'Нужно выбрать что-то одно')
    #     return cleaned_data

    search_file = forms.ChoiceField(
        label='Файл для поиска',
        choices=choice_files,
        widget=forms.Select(
            attrs={
                'class': 'form-control',
                'placeholder': 'Файл для поиска',
            }
        )
    )

    search_name = forms.CharField(
        label='Название парсинга',
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Название парсинга',
            }
        )
    )

    start_value = forms.CharField(
        label='Начальное значение для парсинга',
        widget=forms.NumberInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Первая строка для парсинга',
            }
        )
    )

    end_value = forms.CharField(
        label='Конечное значение для парсинга',
        widget=forms.NumberInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Последняя строка для парсинга',
                # 'max': 1000,
            }
        )
    )


class LoadNewSearchFile(forms.ModelForm):
    class Meta:
        model = FileWithUrls
        fields = ('file',)

        field_classes = {
            'file': forms.CharField,
        }

        widgets = {
            'file': forms.FileInput(attrs={'class': 'form-control-file'}),
        }


class ParserSettingsForm(forms.ModelForm):
    class Meta:
        model = Settings
        fields = '__all__'

        field_classes = {
            'pool_workers': forms.CharField,
            'number_of_requests': forms.CharField,
            'waiting_time': forms.CharField,
        }
        widgets = {
            'pool_workers': forms.NumberInput(attrs={'class': 'form-control'}),
            'number_of_requests': forms.NumberInput(attrs={'class': 'form-control'}),
            'waiting_time': forms.NumberInput(attrs={'class': 'form-control'}),
        }
