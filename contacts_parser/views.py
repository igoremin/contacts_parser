from django.shortcuts import render, redirect, get_object_or_404
from .models import PageData, ParserName, FileWithUrls, Settings
from .forms import SearchInputForm, LoadNewSearchFile, ParserSettingsForm
from .scripts import write_xlsx_file, parsing
import time
import os
import threading
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required


# @login_required
def main_page(request):
    if request.method == 'GET':
        all_parsers = ParserName.objects.all()
        context = {
            'data': 'ТЕСТ',
            'all_parsers': all_parsers
        }
        return render(request, 'contacts_parser/parser_list.html', context)


# @login_required
def url_details(request, pk):
    if request.method == 'GET':
        url = PageData.objects.get(pk=pk)
        context = {
            'url': url
        }
        return render(request, 'contacts_parser/url_details.html', context)


# @login_required
def parser_details(request, name):
    parser = get_object_or_404(ParserName, search_name=name)

    if request.method == 'GET' and request.is_ajax():
        if request.GET.get('status') == 'get_status':
            done_url = parser.done_urls
            status = True if parser.status is True and parser.result_file else False
            if done_url > 100:

                work_time = int(((parser.end_row - parser.start_row) / done_url) * int(time.time() - parser.start_time)
                                - (time.time() - parser.start_time))

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
                 'parser_progress': 100 * parser.done_urls / (parser.end_row - parser.start_row),
                 'status': status,
                 'time': work_time_str},
                status=200
            )

    elif request.method == 'GET':
        parser_data = PageData.objects.filter(search_name__search_name__iexact=name)

        paginator = Paginator(parser_data, 1000)
        page_number = request.GET.get('page', 1)
        page = paginator.get_page(page_number)
        is_paginator = page.has_other_pages()

        if page.has_previous():
            prev_url = '?page={}'.format(page.previous_page_number())
        else:
            prev_url = ''

        if page.has_next():
            next_url = '?page={}'.format(page.next_page_number())
        else:
            next_url = ''

        last_url = '?page={}'.format(paginator.num_pages)

        context = {
            'len_parser_data': len(parser_data),
            'parser': parser,
            'parser_all_urls_target': parser.end_row - parser.start_row,
            'page_object': page,
            'is_paginator': is_paginator,
            'next_url': next_url,
            'prev_url': prev_url,
            'last_url': last_url,
        }

        return render(request, 'contacts_parser/parser_details.html', context)


# @login_required
def load_new_search_file(request):
    if request.method == 'GET':
        form = LoadNewSearchFile()
        context = {
            'form': form
        }

        return render(request, 'contacts_parser/new_main_file.html', context)
    else:
        form = LoadNewSearchFile(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            new_file_model = FileWithUrls(
                file=file
            )
            new_file_model.save()
            # form.save()
        return redirect(main_page)


# @login_required
def continue_parsing(request, name):
    if request.method == 'GET':
        con_parsing = get_object_or_404(ParserName, search_name=name)

        all_done_parsing = ParserName.objects.all()
        context = {
            'all_done_parsing': all_done_parsing,
            'parsing': con_parsing,
        }

        return render(request, 'contacts_parser/continue_parsing.html', context)
    else:
        con_parsing = get_object_or_404(ParserName, search_name=name)

        with open(con_parsing.main_file.file.path, 'r', encoding='utf-8') as all_urls_file:
            all_urls = []
            try:
                for row in all_urls_file.readlines()[con_parsing.start_row + con_parsing.done_urls:con_parsing.end_row]:
                    url = row.lower().strip().split('\t')[0]
                    all_urls.append(f"http://{url}")
            except IndexError:
                print('Диапазон значений для поиска выбран не верно!')
        if len(all_urls) > 0:
            con_parsing.change_status(False)
            con_parsing.change_start_time()

            thread = threading.Thread(target=parsing, args=[all_urls, con_parsing])
            thread.start()
        else:
            if con_parsing.result_file:
                con_parsing.change_status(True)
            else:
                write_xlsx_file(con_parsing)
                con_parsing.change_status(True)
        return redirect(parser_details, name=con_parsing.search_name)


# @login_required
def parser_settings(request):
    if request.method == 'GET':
        try:
            settings = Settings.objects.all()[0]
        except IndexError:
            settings = Settings()
            settings.save()

        context = {
            'form': ParserSettingsForm(initial={
                'number_of_requests': settings.number_of_requests,
                'pool_workers': settings.pool_workers,
                'waiting_time': settings.waiting_time,
            })
        }
        return render(request, 'contacts_parser/settings.html', context)
    else:
        form = ParserSettingsForm(request.POST)
        if form.is_valid():
            cleaned_data = form.clean()
            settings = Settings.objects.all()[0]

            settings.pool_workers = cleaned_data['pool_workers']
            settings.waiting_time = cleaned_data['waiting_time']
            settings.number_of_requests = cleaned_data['number_of_requests']

            settings.save()

            return redirect(main_page)


# @login_required
def new_parser(request):
    if request.method == 'GET':
        form = SearchInputForm()
        all_files = FileWithUrls.objects.all()
        context = {
            'form': form,
            'all_files': all_files,
        }
        return render(request, 'contacts_parser/new_parsing.html', context)

    elif request.method == 'POST':

        form = SearchInputForm(request.POST)

        if form.is_valid():
            clean_data = form.clean()

            parser_file = FileWithUrls.objects.filter(file=f"main_files/{clean_data['search_file']}")
            if parser_file:

                start = int(clean_data['start_value'])
                end = int(clean_data['end_value'])

                new_search = ParserName(
                    main_file=parser_file[0],
                    search_name=clean_data['search_name'],
                    start_row=start,
                    end_row=end,
                )
                new_search.save()

                if os.path.isfile('done_url.txt'):
                    os.remove('done_url.txt')
                if os.path.isfile('no_response_urls.txt'):
                    os.remove('no_response_urls.txt')

                with open(parser_file[0].file.path, 'r', encoding='utf-8') as all_urls_file:
                    all_urls = []
                    try:
                        for row in all_urls_file.readlines()[start:end]:
                            url = row.lower().strip().split('\t')[0]
                            all_urls.append(f"http://{url}")
                    except IndexError:
                        print('Диапазон значений для поиска выбран не верно!')

                if len(all_urls) > 0:

                    thread = threading.Thread(target=parsing, args=[all_urls, new_search])
                    thread.start()

                    # parsing(all_urls, new_search)

                    # write_xlsx_file(new_search)

                else:
                    print('Списко адресов для парсинга пуст!!!\nВыход')

                return redirect(parser_details, name=new_search.search_name)
