from user_agent import generate_user_agent
from bs4 import BeautifulSoup
from bs4.element import Comment
from bs4.dammit import EncodingDetector
import requests
from requests.exceptions import HTTPError
import re
import csv
import time
import datetime
import random
import os
from openpyxl import Workbook
from openpyxl.styles import NamedStyle, Font, Border, Side, Alignment, colors
from openpyxl.utils.exceptions import IllegalCharacterError
import concurrent.futures
from .models import PageData, NoResponseUrls, DoneUrls, Settings
from site_engine.settings import BASE_DIR, DEBUG
import gc


def parsing(
        all_urls,
        new_search,
        done_urls_from_page_data=None,
        done_urls_from_done_urls=None,
        no_response_urls=None
):

    class Parser:
        def __init__(self, url_from_file):
            self.site_url = url_from_file
            self.main_url = ''
            self.headers = ''

            main_page_data = self.get_soup(self.site_url)
            new_search.add_done_url()

            if main_page_data is not False:
                self.main_page_soup, self.main_page_url = main_page_data[0], main_page_data[1]
                self.parser_main_page()

        def get_soup(self, site_url):
            if site_url in done_urls_from_page_data\
                    or site_url in done_urls_from_done_urls or site_url in no_response_urls:
                # print(f'Данный url уже использовался!!! : {site_url}')
                return False
            else:
                status = True
                count = 1
                while count <= settings.number_of_requests or status is False:
                    try:
                        if count > 1 and DEBUG:
                            print(f'Сайт {site_url} , проход {count}')
                        response = requests.get(
                            site_url,
                            headers=self.headers,
                            timeout=settings.waiting_time,
                        )

                        http_encoding = response.encoding if 'charset' in response.headers.get('content-type',
                                                                                               '').lower() else None
                        html_encoding = EncodingDetector.find_declared_encoding(response.content, is_html=True)
                        encoding = html_encoding or http_encoding or 'cp1252' or 'cp1251'

                        rez_soup = BeautifulSoup(response.content.decode(encoding, 'ignore'), 'lxml')

                        done_urls_from_page_data.add(site_url)

                        done_url = DoneUrls(
                            search_name=new_search,
                            page_url=self.site_url,
                        )
                        done_url.save()

                        status = False
                        return [rez_soup, response.url]

                    except HTTPError as http_err:
                        # print(http_err)
                        pass

                    except Exception as err:
                        # print(err)
                        pass

                    except:
                        # print('BROKEN')
                        pass

                    finally:
                        count += 1
                if count > settings.number_of_requests:
                    # print(f'От сайта {self.site_url} нет ответа!')

                    no_response_url = NoResponseUrls(
                        search_name=new_search,
                        page_url=self.site_url,
                    )
                    no_response_url.save()

                    return False

        def get_headers(self):
            user_agent = generate_user_agent(device_type=('desktop'))
            headers = {
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;'
                          'q=0.8,application/signed-exchange;v=b3;q=0.9',
                'accept-encoding': 'gzip, deflate, br',
                'accept-language': 'ru,ru-RU;q=0.9,kk-RU;q=0.8,kk;q=0.7,uz-RU;q=0.6,uz;q=0.5,en-RU;q=0.4,en-US;q=0.3,en;q=0.2',
                'cache-control': 'max-age=0',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-site': 'none',
                'sec-fetch-user': '?1',
                'upgrade-insecure-requests': '1',
                'user-Agent': user_agent,
            }
            self.headers = headers

        def parser_main_page(self):
            # print(f'ПАРСИНГ : {self.main_page_url}')
            description = self.main_page_soup.select_one("meta[name$='description']")
            if description:
                try:
                    description_text = str(description['content']).replace('\n', '')
                except KeyError:
                    description_text = ''
            else:
                description_text = ''

            title = self.main_page_soup.title
            if title:
                title_text = str(title.string).replace('\n', '')
            else:
                title_text = ''

            contacts_urls = self.search_contact_page(self.main_page_soup)
            rez_phones = []
            rez_emails = []
            rez_inn = []
            rez_ogrn = []
            rez_kpp = []
            status = False
            if self.main_page_url[-1] == '/':
                self.main_page_url = self.main_page_url[:-1]
            if len(contacts_urls) > 0:
                for contact_url in contacts_urls:
                    time.sleep(random.uniform(0.5, 1.5))
                    if 'http' in contact_url or 'www.' in contact_url:
                        data = self.search_contact_data(contact_url)
                    else:
                        if contact_url[0] == '/':
                            data = self.search_contact_data(f'{self.main_page_url}{contact_url}')
                        else:
                            data = self.search_contact_data(f'{self.main_page_url}/{contact_url}')

                    if data:
                        status = True
                        for phone in data['phones']:
                            if phone.replace('\n', '') not in rez_phones and len(phone.replace('\n', '')) > 0:
                                rez_phones.append(phone.replace('\n', ''))
                        for email in data['emails']:
                            email = email.replace('\n', '')
                            if email.replace('\n', '') not in rez_emails and len(email) > 0:
                                rez_emails.append(email)
                        for inn in data['all_inn']:
                            if len(inn) > 0:
                                rez_inn.append(inn)
                        for kpp in data['all_kpp']:
                            if len(kpp) > 0:
                                rez_kpp.append(kpp)
                        for ogrn in data['all_ogrn']:
                            if len(ogrn) > 0:
                                rez_ogrn.append(ogrn)

            if status is False:
                data = self.search_contact_data(contact_page_url='', page_soup=self.main_page_soup)
                if data:
                    for phone in data['phones']:
                        if phone.replace('\n', '') not in rez_phones and len(phone.replace('\n', '')) > 0:
                            rez_phones.append(phone.replace('\n', ''))
                    for email in data['emails']:
                        email = email.replace('\n', '')
                        if email.replace('\n', '') not in rez_emails and len(email) > 0:
                            rez_emails.append(email)
                    for inn in data['all_inn']:
                        if len(inn) > 0:
                            rez_inn.append(inn)
                    for kpp in data['all_kpp']:
                        if len(kpp) > 0:
                            rez_kpp.append(kpp)
                    for ogrn in data['all_ogrn']:
                        if len(ogrn) > 0:
                            rez_ogrn.append(ogrn)

            new_data = PageData(
                search_name=new_search,
                page_url=self.main_page_url,
                title=title_text,
                description=description_text,
                phones=', '.join(list(set(rez_phones))),
                emails=', '.join(list(set(rez_emails))),
                inn=', '.join(list(set(rez_inn))),
                ogrn=', '.join(list(set(rez_ogrn))),
                kpp=', '.join(list(set(rez_kpp)))
            )
            new_data.save()

        @staticmethod
        def search_contact_page(main_page_soup):
            contacts_url = []

            all_links = main_page_soup.find_all('a')
            for link in all_links:
                link_text = link.get_text(strip=True)
                if len(link_text) > 0 and re.search(r'о нас|контакт|связаться', str(link_text).lower()):
                    try:
                        if re.search(r'(contact|about|kontakt|o-nas)/?', link['href']):
                            contacts_url.append(link['href'])
                    except KeyError:
                        pass

            return set(contacts_url)

        def search_contact_data(self, contact_page_url, page_soup=False):
            if page_soup is False:
                request_data = self.get_soup(contact_page_url)
            else:
                request_data = [page_soup]

            if request_data:
                soup = request_data[0]
                phones = []
                emails = []

                all_links = soup.find_all('a')
                all_href = set()
                for link in all_links:
                    try:
                        href = link['href']
                        all_href.add(href)
                    except KeyError:
                        pass

                for link in all_href:
                    if re.search(r"tel:", link):
                        phones.append(link.replace('tel:', ''))
                    elif re.search(r"mailto:", link):
                        emails.append(link.replace('mailto:', ''))

                re_phones = []
                re_emails = []

                # body = soup.body.get_text(strip=False)
                texts = soup.findAll(text=True)
                visible_texts = filter(self.tag_visible, texts)
                visible_texts_str = ''

                for t in visible_texts:
                    visible_texts_str = visible_texts_str + t
                    search_phones = re.findall(r"[^\d.](?:\+7|8)[\d\-\(\) ]{9,}\d", t)
                    search_emails = re.findall(r'[\w.-]+@[\w.-]+\.?[\w]+?', t)

                    if search_phones:
                        for phone in search_phones:
                            re_phones.append(phone)

                    if search_emails:
                        for email in search_emails:
                            re_emails.append(email)

                # re_emails = re_emails + re.findall(r'[\w.-]+@[\w.-]+\.?[\w]+?', body)

                rez_phones = []
                rez_emails = []
                for phone in re_phones + phones:
                    # print(phone)
                    phone = re.sub(r'\D', '', phone)
                    # for s in ['tel:', ' ', '-', ':', '(', ')', '"', "'", ' ']:
                    #     phone = phone.replace(s, '')
                    if 0 < len(phone) <= 12:
                        rez_phones.append(phone)

                for email in re_emails + emails:
                    if 0 < len(email) <= 30:
                        rez_emails.append(email)

                visible_texts_str = visible_texts_str.replace('\n', '')

                if len(rez_phones) == 0:
                    search_phones = re.findall(r"(?:\+7|8)\-?[\d\-\(\) ]{9,}\d", visible_texts_str)
                    for phone in search_phones:
                        phone = re.sub(r'\D', '', phone)
                        # for s in ['tel:', ' ', '-', ':', '(', ')', '"', "'", ' ']:
                        #     phone = phone.replace(s, '')
                        if 0 < len(phone) <= 12:
                            rez_phones.append(phone)
                    # rez_phones = re.findall(r"[^\d.](?:\+7|8)[\d\-\(\) ]{9,}\d", body)
                    # print(type(body))
                    # new_body = re.sub(r'\<script.*script\>', '', body, re.S)
                    # print(new_body)

                if 'инн' in visible_texts_str.lower():
                    all_inn = re.findall(r"\D\d{12}\D|\D\d{10}\D", visible_texts_str)
                else:
                    all_inn = []
                if 'кпп' in visible_texts_str.lower():
                    all_kpp = re.findall(r"\D\d{9}\D", visible_texts_str)
                else:
                    all_kpp = []
                if 'инн' in visible_texts_str.lower():
                    all_ogrn = re.findall(r"\D\d{13}\D", visible_texts_str)
                else:
                    all_ogrn = []

                rez_inn = []
                if len(all_inn) > 0:
                    for inn in all_inn:
                        if re.search(r'\d{12}', inn):
                            rez_inn.append(re.search(r'\d{12}', inn)[0])
                        elif re.search(r'\d{10}', inn):
                            rez_inn.append(re.search(r'\d{10}', inn)[0])

                rez_kpp = []
                if len(all_kpp) > 0:
                    for kpp in all_kpp:
                        kpp_value = re.search(r'\d{9}', kpp)[0]
                        if kpp_value[:2] == '04':
                            pass
                        else:
                            rez_kpp.append(kpp_value)

                rez_ogrn = []
                if len(all_ogrn) > 0:
                    for ogrn in all_ogrn:
                        rez_ogrn.append(re.search(r'\d{13}', ogrn)[0])

                rez_dict = {'phones': set(rez_phones), 'emails': set(rez_emails), 'all_inn': set(rez_inn),
                            'all_kpp': set(rez_kpp), 'all_ogrn': set(rez_ogrn)}
                return rez_dict
            else:
                return False

        @staticmethod
        def tag_visible(element):
            if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
                return False
            if isinstance(element, Comment):
                return False
            # if re.match(r"[\s\r\n]+", str(element)):
            #     return False
            return True

    if no_response_urls is None:
        no_response_urls = set(NoResponseUrls.objects.filter(search_name=new_search).values_list('page_url', flat=True))
    else:
        no_response_urls = no_response_urls

    if done_urls_from_page_data is None:
        done_urls_from_page_data = set(PageData.objects.filter(search_name=new_search).values_list('page_url', flat=True))
    else:
        done_urls_from_page_data = done_urls_from_page_data

    if done_urls_from_done_urls is None:
        done_urls_from_done_urls = set(DoneUrls.objects.filter(search_name=new_search).values_list('page_url', flat=True))
    else:
        done_urls_from_done_urls = done_urls_from_done_urls

    settings = Settings.objects.all()[0]

    def chunk_data(data, chunk_size):
        for i in range(0, len(data), chunk_size):
            yield data[i:i + chunk_size]

    if len(all_urls) > 100000:
        for lines in chunk_data(all_urls, 50000):
            with concurrent.futures.ThreadPoolExecutor(max_workers=settings.pool_workers) as executor:
                rez = executor.map(Parser, lines)
                rez = None
                executor.shutdown()
                del executor
            lines = None
            gc.collect()
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=settings.pool_workers) as executor:
            executor.map(Parser, all_urls)
        gc.collect()

    new_search.change_status(True)

    write_xlsx_file(new_search)


def write_xlsx_file(search):
    k = 0
    while k < 5:
        try:
            print('CREATE RESULT FILE')
            csv.field_size_limit(100000000)
            done_main_urls = set()

            file_name = f'{datetime.datetime.today().strftime("%d-%m-%Y_%H-%M")}.xlsx'

            wb = Workbook()

            sheet = wb['Sheet']
            wb.remove(sheet)

            wb.create_sheet('Список сайтов')
            sheet = wb['Список сайтов']

            sheet.column_dimensions['A'].width = 20
            sheet.column_dimensions['B'].width = 50
            sheet.column_dimensions['C'].width = 50
            sheet.column_dimensions['D'].width = 30
            sheet.column_dimensions['E'].width = 30
            sheet.column_dimensions['F'].width = 30
            sheet.column_dimensions['G'].width = 100
            sheet.column_dimensions['H'].width = 200

            search_results = PageData.objects.filter(search_name=search)
            r = 0
            for result in search_results:
                if r == 0:
                    header = NamedStyle(name="header")
                    header.font = Font(bold=True, color=colors.RED, size=20)
                    header.border = Border(bottom=Side(border_style="thin"))
                    header.alignment = Alignment(horizontal="center", vertical="center")
                    sheet.append(['Url', 'Email', 'Телефон', 'ИНН', 'ОГРН', 'КПП', 'Заголовок', 'Описание'])
                    header_row = sheet[1]
                    for cell in header_row:
                        cell.style = header
                    r += 1
                else:
                    data = [result.page_url, result.emails, result.phones, result.inn, result.ogrn,
                            result.kpp, result.title.strip(), result.description.strip()]

                    if result.page_url not in done_main_urls and len(result.page_url) > 4:

                        try:
                            sheet.append(data)
                            done_main_urls.add(result.page_url)
                            r += 1
                        except IllegalCharacterError:
                            pass

            path = os.path.join(BASE_DIR, f'media/results_files/{search.search_name}')
            if os.path.isdir(path) is False:
                os.makedirs(path, mode=0o777)

            wb.save(f'{path}/{file_name}')

            search.result_file = f'results_files/{search.search_name}/{file_name}'
            search.change_result_file()

            break
        except Exception as err:
            print(f'ERROR WITH WRITE RESULT FILE : {err}')
        except:
            print('ERROR WITH WRITE RESULTS')

        time.sleep(60)
        k += 1
