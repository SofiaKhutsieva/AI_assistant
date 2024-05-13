import logging
import string
import nltk
import pymorphy2
import numpy as np
import re


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

nltk.download('punkt')
# nltk.download('punkt', download_dir=os.path.join('conf', 'service'))
# нормальная форма

morph = pymorphy2.MorphAnalyzer()


def tokenize_text(raw_text: str) :
    """Функция для токенизации текста, извлечения только русских букв и приведения всех слов к нормальной форме, - заменяем на ' '
    пример: 'при1вет, как твои-дел13а' -> 'привет как твои дело'

    :param raw_text: исходная текстовая строка
    """
    tokenized_str = nltk.word_tokenize(raw_text)  # разбиение по словам
    reg = re.compile('[^а-яёА-ЯЁ-]')
    tokenized_str = [reg.sub('', word) for word in tokenized_str]  # оставляем только русские буквы

    tokens = [i.lower() for i in tokenized_str if
              (i not in string.punctuation)]  # приведение к нижнему регистру и удаление пунктуации
    normal_form = [morph.parse(word)[0].normal_form for word in tokens]  # приведение к нормальной форме
    return ' '.join(normal_form).replace('-', ' ')


def payloads_validate(sen) :
    # Функция перевода предложения в список слов в нормальной форме
    """
    вход:
    sen - строка без орфографических ошибок
    выход:
    norm_form_1 - список из слов в нормальной форме и с цифрами

    """

    sen = sen.lower()
    # удаление пунктуации
    for p in string.punctuation:
        if p in sen:
            sen = sen.replace(p, ' ')

    norm_form_1 = sen
    # Токенизация по словам
    sentence = nltk.sent_tokenize(norm_form_1)
    # print(sentence)
    words = [nltk.word_tokenize(word) for word in sentence]
    # print('words:', words)
    # Приведение к нормальной форме
    if len(words):
        norm_form_1 = [morph.parse(word)[0].normal_form for word in words[0]]
    return (norm_form_1)


title_dict = {1 : 'Первый вариант, Один', 2 : 'Второй вариант, Два', 3 : 'Третий вариант, Три',
              4 : 'Четвертый вариант, Четыре', 5 : 'Пятый вариант, Пять', 6 : 'Шестой вариант, Шесть',
              7 : 'Седьмой вариант, Семь', 8 : 'Восьмой вариант, Восемь', 9 : 'Девятый вариант, Девять',
              10 : 'Десятый вариант, Десять', 11 : 'Одиннадцатый вариант, Одиннадцать',
              12 : 'Двенадцатый вариант, Двенадцать', 13 : 'Тринадцатый вариант, Тринадцать',
              14 : 'Четырнадцатый вариант, Четырнадцать', 15 : 'Пятнадцатый вариант, Пятнадцать',
              16 : 'Шестнадцатый вариант, Шестнадцать', 17 : 'Семнадцатый вариант, Семнадцать',
              18 : 'Восемнадцатый вариант, Восемнадцать', 19 : 'Девятнадцатый вариант, Девятнадцать',
              20 : 'Двадцатый вариант, Двадцать', 21 : 'Двадцать первый вариант, Двадцать один',
              22 : 'Двадцать второй вариант, Двадцать два', 23 : 'Двадцать третий вариант, Двадцать три',
              24 : 'Двадцать четвертый вариант, Двадцать четыре', 25 : 'Двадцать пятый вариант, Двадцать пять',
              26 : 'Двадцать шестой вариант, Двадцать шесть', 27 : 'Двадцать седьмой вариант, Двадцать семь',
              28 : 'Двадцать восьмой вариант, Двадцать восемь', 29 : 'Двадцать девятый вариант, Двадцать девять',
              30 : 'Тридцатый вариант, Тридцать', 31 : 'Тридцать первый вариант, Тридцать один',
              32 : 'Тридцать второй вариант, Тридцать два', 33 : 'Тридцать третий вариант, Тридцать три',
              34 : 'Тридцать четвертый вариант, Тридцать четыре', 35 : 'Тридцать пятый вариант, Тридцать пять',
              36 : 'Тридцать шестой вариант, Тридцать шесть', 37 : 'Тридцать седьмой вариант, Тридцать семь',
              38 : 'Тридцать восьмой вариант, Тридцать восемь', 39 : 'Тридцать девятый вариант, Тридцать девять',
              40 : 'Сороковой вариант, Сорок', 41 : 'Сорок первый вариант, Сорок один',
              42 : 'Сорок второй вариант, Сорок два', 43 : 'Сорок третий вариант, Сорок три',
              44 : 'Сорок четвертый вариант, Сорок четыре', 45 : 'Сорок пятый вариант, Сорок пять',
              46 : 'Сорок шестой вариант, Сорок шесть', 47 : 'Сорок седьмой вариант, Сорок семь',
              48 : 'Сорок восьмой вариант, Сорок восемь', 49 : 'Сорок девятый вариант, Сорок девять',
              50 : 'Пятидесятый вариант, Пятьдесят'}


def compare_payloads(dispatcher, value, buttons, title=None, text=None, var=True, flag_text=True,
                     buttons_layout_num=None, buttons_layout_auto=False, buttons_=None,
                     parser_default=True, num=50, buttons_output=True) :
    """
    Проверка value на вхождение в buttons.title

    :param dispatcher:
    :param value:
    :param buttons:
    :param title: список, используемый вместо buttons.title (если передан)
    :param text: текст, добавляемый к выводу в случае, если value не входит в buttons.title
    :param var: параметр, отвечающий за необходимость вывода сообщений пользователю
    :param flag_text: параметр, отвечающий за необходимость вывода дополнительного текста,
        такого как "Напишите подробнее", "Извините, я Вас не понял" и т.д.
    :param buttons_layout_num: параметр, отвечающий за раскладку кнопок
    :param buttons_layout_auto: параметр, указывающий на необходимость автоматического форматирования раскладки кнопок
    :param buttons_: дублирует параметр buttons. Если он указан - параметр button будет проигнорирован
    :param parser_default: параметр, указывающий на необходимость использования
        не измененного date_and_numbers_processor.Text2NumbersParser
    :param num: параметр, отвечающий за макисмальное количество отображаемых кнопок
    :param buttons_output: параметр, отвечающий за вывод кнопок
    :return:
    """

    if buttons_ is None :
        buttons_ = buttons

    if buttons_layout_num is None :
        buttons_layout_num = [1]
    orig_value = value[:]
    # print('buttons:', buttons)
    # print('value:', value)
    inds = [button['payload'] for button in buttons]

    if title == None :
        title = [button['title'] for button in buttons_]
    value = value.lower()
    res1, res2 = [], []

    for i in range(len(title)) :
        res1.append(payloads_validate(title[i]))
        res2.append(payloads_validate(title_dict[i + 1]))

    print(f'res1 = {res1}')
    print(f'res2 = {res2}')
    value = payloads_validate(value)
    print(f'value = {value}')
    value_ = value

    counter = 0
    ind = -1

    for i in range(len(title)) :
        if orig_value.lower() == title[i].lower() :
            return (inds[i], counter, ind, value_)

    for i in range(len(res1)) :
        one, two = res1[i], res2[i]
        if (sum(np.in1d(value, one)) == len(value)) or (sum(np.in1d(value, one)) == len(one)) \
                or (sum(np.in1d(value, two)) == len(value)) :
            counter += 1
            ind = i
    print(counter)
    if orig_value in inds :
        return (orig_value, counter, ind, value_)

    if len(inds) <= num :
        if counter == 1 :
            # print(ind)
            return (inds[ind], counter, ind, value_)
    return (None, counter, ind, value_)
    #     elif counter > 1 :
    #         if var :  # общий случай
    #             if text != None :
    #                 if flag_text :
    #                     text_init = f"Напишите подробнее. " + text
    #                 else :
    #                     text_init = text
    #             else :
    #                 if flag_text :
    #                     text_init = f"Напишите подробнее."
    #                 else :
    #                     text_init = ''
    #             if buttons_output :
    #                 if not buttons_layout_auto :
    #                     dispatcher.utter_message(text=text_init, buttons=buttons,
    #                                              json_message={"buttons_layout" : buttons_layout_num})
    #                 else :
    #                     dispatcher.utter_message(text=text_init, buttons=buttons)
    #             else :
    #                 dispatcher.utter_message(text=text_init)
    #
    #         return (None, counter, ind, value_)
    #     elif counter < 1 :
    #         if var :  # общий случай
    #             if text != None :
    #                 if flag_text :
    #                     text_init = f"Извините, я Вас не понял. " + text
    #                 else :
    #                     text_init = text
    #             else :
    #                 if flag_text :
    #                     text_init = f"Извините, я Вас не понял."
    #                 else :
    #                     text_init = ''
    #             if buttons_output :
    #                 dispatcher.utter_message(text=text_init, buttons=buttons)
    #             else :
    #                 dispatcher.utter_message(text=text_init)
    #         return (None, counter, ind, value_)
    # else :
    #     text_init = f"Извините, я Вас не понял."
    #     dispatcher.utter_message(text=text_init, buttons=buttons)
    #     return (None, counter, ind, value_)