from django.shortcuts import render, redirect, get_object_or_404
from contacts_parser.models import ParserName, PageData
from .forms import NewRusprofileParserForm, RusprofileSettingForm
from .models import RusprofileParser, RusprofileParserData, RusprofileSettings
from .scripts import main, write_rusprofile_xlsx_file
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
import threading
import time


# @login_required
def done_parsings(request):
    if request.method == 'GET':
        all_parsings = RusprofileParser.objects.all()

        context = {
            'all_parsings': all_parsings
        }
        return render(request, 'rusprofile_parser/all_parsings.html', context)


# @login_required
def parsing_details(request, name):
    parser_info = get_object_or_404(RusprofileParser, file_name__iexact=name)
    if request.method == 'GET' and request.is_ajax():
        pass
        if request.GET.get('status') == 'get_status':
            done_url = parser_info.done_urls
            status = True if parser_info.status else False
            if done_url > 10:

                work_time = int((parser_info.target / done_url) * int(time.time() - parser_info.start_time)
                                - (time.time() - parser_info.start_time))

                h = (work_time // 3600) % 24
                m = (work_time // 60) % 60
                s = work_time % 60

                if m < 10:
                    m = str('0' + str(m))
                else:
                    m = str(m)
                if s < 10:
                    s = str('0' + str(s))
                else:
                    s = str(s)
                work_time_str = f'{h} часов, {m} минут, {s} секунд'

            else:
                work_time_str = 'Неизвестно'

            return JsonResponse(
                {'done_url': done_url,
                 'parser_progress': int(100 * parser_info.done_urls / parser_info.target),
                 'status': status,
                 'time': work_time_str},
                status=200
            )
    elif request.method == 'GET':
        all_data = RusprofileParserData.objects.filter(parser_name__file_name__iexact=name)
        context = {
            'all_data': all_data,
            'len_all_data': len(all_data),
            'parser_info': parser_info,
            'target': parser_info.target,
            'done_sites': parser_info.done_urls
        }
        return render(request, 'rusprofile_parser/rusprofile_parser_details.html', context)
    else:
        if request.POST['create_file'] == 'YES':
            write_rusprofile_xlsx_file(parser_info)

        return redirect(parsing_details, name)


# @login_required
def company_details(request, pk):
    if request.method == 'GET':
        company = get_object_or_404(RusprofileParserData, pk=pk)
        url = get_object_or_404(PageData, rusprofile_data=company)
        context = {
            'company': company,
            'url': url,
        }
        return render(request, 'rusprofile_parser/rusprofile_company_details.html', context)


# @login_required
def rusprofile_settings(request):
    try:
        settings = RusprofileSettings.objects.all()[0]
    except IndexError:
        settings = RusprofileSettings()
        settings.save()

    if request.method == 'GET':
        context = {
            'form': RusprofileSettingForm(initial={
                'proxy_file': settings.proxy_file.name,
                'pool_workers': settings.pool_workers,
                'waiting_time': settings.waiting_time,
            })
        }
        return render(request, 'rusprofile_parser/rusprofile_settings.html', context)
    else:
        form = RusprofileSettingForm(request.POST, request.FILES)
        if form.is_valid():
            cleaned_data = form.clean()

            settings.pool_workers = cleaned_data['pool_workers']
            settings.waiting_time = cleaned_data['waiting_time']
            if cleaned_data['proxy_file']:
                settings.proxy_file = request.FILES['proxy_file']
                settings.update()
            else:
                settings.save()

            return redirect(done_parsings)


# @login_required
def new_parsing(request):
    if request.method == 'GET':
        all_done_parsings = ParserName.objects.all()
        form = NewRusprofileParserForm()
        context = {
            'done_parsings': all_done_parsings,
            'form': form,
        }
        return render(request, 'rusprofile_parser/start_new_parsing.html', context)
    else:
        form = NewRusprofileParserForm(request.POST)
        if form.is_valid():
            cleaned_data = form.clean()
            search_file = ParserName.objects.filter(search_name__iexact=cleaned_data['search_file'])
            if search_file:

                new_parser = RusprofileParser(
                    search_file=search_file[0],
                    file_name=cleaned_data['file_name'],
                    key_words=cleaned_data['key_words'],
                    number_of_coincidences=cleaned_data['number_of_coincidences'],
                    target=len(PageData.objects.filter(search_name__search_name__iexact=search_file[0].search_name))
                )
                new_parser.save()

                thread = threading.Thread(target=main, args=[new_parser])
                thread.start()

                return redirect(parsing_details, new_parser.file_name)
