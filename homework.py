import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram.ext
from dotenv import load_dotenv

import mistakes

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверяет доступность переменных окружения."""
    message_error = 'Отсутствие обязательных переменных окружения.'
    constants_existence = all([
        PRACTICUM_TOKEN,
        TELEGRAM_TOKEN,
        TELEGRAM_CHAT_ID
    ])
    if not constants_existence:
        logging.critical(message_error)
        exit(message_error)


def send_message(bot, message):
    """отправляет сообщение в Telegram чат."""
    try:
        logging.info('Начало отправки')
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
        )
    except telegram.TelegramError:
        logging.error('Cбой при отправке сообщения в Telegram.')
    else:
        logging.debug('Удачная отправка сообщения в Telegram.')


def get_api_answer(timestamp):
    """делает запрос к единственному эндпоинту API-сервиса."""
    massage_error = 'Неверный ответ.'
    massage_respons = 'Hедоступность эндпоинта.'
    params_request = {
        'url': ENDPOINT,
        'headers': HEADERS,
        'params': {'from_date': timestamp},
    }
    logging.debug('Отправка запроса к API-сервиса.')
    try:
        homework_statuses = requests.get(**params_request)
        if homework_statuses.status_code != HTTPStatus.OK:
            logging.error(massage_respons)
            raise mistakes.InvalidResponse(massage_respons)
        return homework_statuses.json()
    except requests.RequestException:
        logging.error(massage_error)
        raise mistakes.ConnectApiError(massage_error)


def check_response(response):
    """проверяет ответ API на соответствие документации."""
    error_type_api = 'Ошибка в типе ответа API.'
    empty_answer_api = 'Пустой ответ от API.'
    no_list = 'Homeworks не является списком.'
    no_int = 'Current_date не является счислом.'
    if not isinstance(response, dict):
        logging.error(error_type_api)
        raise TypeError(error_type_api)
    if 'homeworks' not in response or 'current_date' not in response:
        logging.error(empty_answer_api)
        raise KeyError(empty_answer_api)
    if not isinstance(response['homeworks'], list):
        logging.error(no_list)
        raise TypeError(no_list)
    if not isinstance(response['current_date'], int):
        logging.error(no_int)
        raise TypeError(no_int)


def parse_status(homework):
    """Извлекает из информации статус этой работы."""
    if 'homework_name' not in homework:
        logging.error('Нет homework_name в homework.')
        raise KeyError('В ответе отсутсвует ключ homework_name')
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_status not in HOMEWORK_VERDICTS:
        massage_error = 'Недокументированный статус домашней работы.'
        logging.error(massage_error)
        raise KeyError(massage_error)
    verdict = HOMEWORK_VERDICTS[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(message)s',
        stream=sys.stdout
    )
    logging.info('Начало работы Бота')
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    send_message(bot, 'Начало работы Бота')
    initial_answer = ''

    while True:
        try:
            request_new = get_api_answer(timestamp)
            check_response(request_new)
            logging.info('Запрос API прошел проверку.')
            homeworks = request_new['homeworks']
            if not homeworks:
                logging.info('Нет активной работы.')
                continue
            homework = parse_status(homeworks[0])
            if homework != initial_answer:
                send_message(bot, homework)
                logging.info(f'Отправлен новый статус: {homework}')
                initial_answer = request_new
                timestamp = request_new.get('current_date')
            else:
                logging.info('Статус не обновлен.')

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
            send_message(bot, message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
