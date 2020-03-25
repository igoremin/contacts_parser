from django import forms
from contacts_parser.models import ParserName
from .models import RusprofileSettings


def choice_contact_parser():
    all_files = ParserName.objects.all()
    choices = []
    for file in all_files:
        choices.append((file.search_name, file.search_name))
    return choices


class NewRusprofileParserForm(forms.Form):
    search_file = forms.ChoiceField(
        label='Данные для поиска',
        choices=choice_contact_parser,
        widget=forms.Select(
            attrs={
                'class': 'form-control',
                'placeholder': 'Данные для поиска',
            }
        )
    )

    file_name = forms.CharField(
        label='Название поиска',
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Введите название',
            }
        )
    )

    use_key_words = forms.ChoiceField(
        label='Использовать ключевые слова',
        choices=[('True', 'Да'), ('False', 'Нет')],
        widget=forms.Select(
            attrs={
                'class': 'form-control',
            }
        )
    )

    key_words = forms.CharField(
        label='Ключевые слова',
        required=False,
        widget=forms.Textarea(
            attrs={
                'class': 'form-control',
                'placeholder': 'Ключевые слова и фразы для поиска, через запятую',
            }
        )
    )

    number_of_coincidences = forms.CharField(
        label='Количество совпадений по ключевым словам',
        required=False,
        widget=forms.NumberInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Минимальное количество совпадений по ключевым словам для начала поиска',
            }
        )
    )


class RusprofileSettingForm(forms.ModelForm):
    class Meta:
        model = RusprofileSettings
        fields = '__all__'

        field_classes = {
            'pool_workers': forms.CharField,
            'proxy_file': forms.CharField,
            'waiting_time': forms.CharField,
        }
        widgets = {
            'pool_workers': forms.NumberInput(attrs={'class': 'form-control'}),
            'proxy_file': forms.FileInput(attrs={'class': 'form-control-file'}),
            'waiting_time': forms.NumberInput(attrs={'class': 'form-control'}),
        }
