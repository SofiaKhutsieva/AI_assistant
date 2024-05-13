import time
import logging
import aiohttp
import os

from base64 import b64decode, b64encode
from io import BytesIO
from typing import Text, Dict, Any, Optional, Callable, Awaitable, List, Union
from aiogram.types import InlineKeyboardButton, KeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, InputFile, \
    ReplyKeyboardRemove
from sanic import Blueprint, response
from sanic.request import Request
from sanic.response import HTTPResponse
from rasa.core.channels.channel import InputChannel, OutputChannel, UserMessage
from aiogram.bot.bot import Bot
from aiogram.types.update import Update
from aiogram.utils.exceptions import TelegramAPIError
from rasa.shared.exceptions import RasaException
from asyncio import CancelledError

from utils.s2t.s2t import s2t_rus_whisper_transformers
from utils.s2t.utils_s2t import convert_to_file_1, convert_to_file_2

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


# os.environ["SANIC_RESPONSE_TIMEOUT"] = "360"
# os.environ["SANIC_REQUEST_TIMEOUT"] = "360"
# os.environ["SANIC_BACKLOG"] = "30000"

# windows
# set SANIC_BACKLOG=30000
# set SANIC_RESPONSE_TIMEOUT=360
# set SANIC_REQUEST_TIMEOUT=360
# set SANIC_WORKERS=1

class CustomTelegramOutput(Bot, OutputChannel):

    def __init__(self, access_token: Optional[Text], **kwargs) -> None:
        super().__init__(access_token, **kwargs)

    async def send_text_message(self, recipient_id: Text, text: Text, **kwargs: Any) -> None:
        text = text.strip()
        # кнопки
        reply_markup_ = ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = KeyboardButton('Выйти')
        button2 = KeyboardButton('Меню')
        # button3 = KeyboardButton('Назад')
        reply_markup_.row(button1, button2)

        await self.send_message(recipient_id, text, reply_markup=reply_markup_)

    async def send_text_with_buttons(
            self,
            recipient_id: Text,
            text: Text,
            buttons: List[Dict[Text, Any]],
            **kwargs: Any
    ) -> None:

        keyboard_type = kwargs.get('keyboard_type')
        keyboard_layout = kwargs.get('keyboard_layout')
        reply_markup = self._generate_reply_markup_from_buttons(buttons, keyboard_type, keyboard_layout)
        text = text.strip()
        await self.send_message(recipient_id, text, reply_markup=reply_markup)


    async def send_attachment(self, recipient_id: Text, attachment: Text, **kwargs: Any) -> None:
        file_name = kwargs.get('file_name')
        attachment_init = attachment
        if 'base64' in attachment:
            attachment = attachment.split('base64')[1]
        data = BytesIO(b64decode(attachment))
        document = InputFile(data, filename=file_name)
        if attachment_init.startswith('data:application/ogg;base64,'):
            await self.send_voice(recipient_id, document)
        else:
            await self.send_document(recipient_id, document)

    @staticmethod
    def _generate_buttons_markup_according_layout(
            buttons: List[Union[InlineKeyboardButton, KeyboardButton]],
            keyboard_layout: List[int]) -> List[List[Union[InlineKeyboardButton, KeyboardButton]]]:
        result = []
        button_index = 0

        for buttons_number_in_row in keyboard_layout:
            row = [
                buttons[button_in_row_index]
                for button_in_row_index in range(button_index, button_index + buttons_number_in_row)
            ]
            result.append(row)
            button_index += buttons_number_in_row
        return result

    @staticmethod
    def _generate_reply_markup_from_buttons(
            buttons: List[Dict[Text, Any]], keyboard_type: Optional[Text] = None,
            keyboard_layout: Optional[List[int]] = None
    ) -> Union[InlineKeyboardMarkup, ReplyKeyboardMarkup]:
        if keyboard_type and keyboard_type not in ['inline', 'reply']:
            logger.debug(f'keyboard_type parameter must be one of ["inline", "reply"], but got {keyboard_type}')
            raise ValueError(f'keyboard_type parameter must be one of ["inline", "reply"], but got {keyboard_type}')
        elif not keyboard_type:
            if 'Поделиться номером' in [button['title'] for button in buttons]:
                keyboard_type = 'reply'
            else:
                keyboard_type = 'inline'

        if keyboard_layout and sum(keyboard_layout) != len(buttons):
            logger.error(f'Sum of keyboard_layout must be equal to buttons count, '
                         f'but got {len(buttons)} and keyboard_layout: {keyboard_layout}')
            raise ValueError(f'Sum of keyboard_layout must be equal to buttons count, '
                             f'but got {len(buttons)} and keyboard_layout: {keyboard_layout}')
        else:
            keyboard_layout = [1] * len(buttons)

        if keyboard_type == 'inline':
            buttons = [
                InlineKeyboardButton(button['title'], callback_data=button.get('payload'))
                for button in buttons
            ]
            buttons = CustomTelegramOutput._generate_buttons_markup_according_layout(buttons, keyboard_layout)

            reply_markup = InlineKeyboardMarkup()
            for row in buttons:
                reply_markup.row(*row)
        elif keyboard_type == 'reply':
            buttons = [KeyboardButton(button['title'], request_contact=True) if button['title'] == 'Поделиться номером'
                       else KeyboardButton(button['title']) for button in buttons]
            buttons = CustomTelegramOutput._generate_buttons_markup_according_layout(buttons, keyboard_layout)

            reply_markup = ReplyKeyboardMarkup(resize_keyboard=False, one_time_keyboard=True)
            for row in buttons:
                reply_markup.row(*row)
        else:
            logger.error(f'Trying to send text with buttons for unknown button type {keyboard_type}')
            raise ValueError(f'Trying to send text with buttons for unknown button type {keyboard_type}')

        return reply_markup


class CustomTelegramInput(InputChannel):

    def name(self) -> Text:
        return 'telegram'

    @classmethod
    def from_credentials(cls, credentials: Optional[Dict[Text, Any]]) -> InputChannel:
        if not credentials:
            cls.raise_missing_credentials_exception()

        logger.debug('Trying to get webhooks in from_credentials()')
        logger.debug(f"access_token = {credentials.get('access_token')}")
        logger.debug(f"verify = {credentials.get('verify')}")
        logger.debug(f"webhook_url = {credentials.get('webhook_url')}")

        return cls(
            credentials.get('access_token'),
            credentials.get('verify'),
            credentials.get('webhook_url')
        )

    def __init__(
            self,
            access_token: Optional[Text],
            verify: Optional[Text],
            webhook_url: Optional[Text],
            debug_mode: bool = True,
    ) -> None:
        self.access_token = access_token
        self.verify = verify
        self.webhook_url = webhook_url
        self.debug_mode = debug_mode
        logger.debug('Trying to get webhooks in __init__()')
        logger.debug(f"access_token = {self.access_token}")
        logger.debug(f"verify = {self.verify}")
        logger.debug(f"webhook_url = {self.webhook_url}")
        try:
            import requests
            r = requests.get(f'https://api.telegram.org/bot{self.access_token}/setWebhook?url={self.webhook_url}')
            logger.debug(f'Set {self.webhook_url} as a telegram webhook ({r.text})')
        except:
            #logger.debug(f'Failed to set telegram webhook ({r.text})')
            logger.debug(f'Failed to set telegram webhook')

    def get_metadata(self, request: Request) -> Dict[Text, Any]:

        json_from_user = request.json
        logger.debug(f"json_from_user = {json_from_user}")
        return json_from_user.get('metadata', {})

    def blueprint(
            self, on_new_message: Callable[[UserMessage], Awaitable[None]]
    ) -> Blueprint:
        custom_telegram_webhook = Blueprint('telegram_webhook', __name__)
        out_channel = CustomTelegramOutput(self.access_token, parse_mode='HTML', timeout=600)
        logger.debug(f'blueprint')
        logger.debug(f'out_channel.timeout = {out_channel.timeout}')
        bot = Bot(self.access_token, timeout=600)

        @custom_telegram_webhook.route('/', methods=['GET'])
        async def health(_: Request) -> HTTPResponse:
            return response.json({'status': 'ok'})

        @custom_telegram_webhook.route('/webhook', methods=['POST'])
        async def process_user_message(request: Request) -> HTTPResponse:
            # res = False
            # while not res:
            update = Update(**request.json)
            logger.debug(f"update = {update}")
            if update.callback_query:
                sender_id = update.callback_query.message.chat.id
                text = update.callback_query.data
            elif update.message.text:
                sender_id = update.message.chat.id
                text = update.message.text
            elif update.message.voice:
                logger.debug(f"Получена аудиозапись")
                file_info = await out_channel.get_file(update.message.voice.file_id)
                downloaded_file = await out_channel.download_file(file_info.file_path)
                # S2T
                audio_file = convert_to_file_2(downloaded_file)
                text = s2t_rus_whisper_transformers(audio_file)
                logger.debug(f"text = {text}")
                text = text[0].strip()
                logger.debug(f"text = {text}")
                sender_id = update.message.chat.id
            elif update.message.document:
                sender_id = update.message.chat.id
                logger.debug(f'Получен документ')
                try:
                    doc = update.message.document
                    logger.debug(f'Получен документ')
                except:
                    doc = False

                if doc:
                    file = await bot.get_file(doc.file_id)
                    filename = f'{time.time()}.{file.file_path.split(".")[-1]}'
                    file_path = file['file_path']
                    filepath = f'files/dmk/input/{sender_id}/{filename}'

                    async with aiohttp.request('GET', f'https://api.telegram.org/file/'
                                                      f'bot{self.access_token}/{file_path}') as resp:
                        data = await resp.content.read()
                    logger.debug(f'type(data) = {type(data)}')
                    with open(filepath, 'wb') as doc:
                        doc.write(data)
                    text = ''

            else:
                logger.error(f'Got unknown message: {update}')
                return response.text('error')


            metadata = self.get_metadata(request)

            # include exception handling

            if text == '/start':
                text = 'привет'

            if text == 'Выйти' or text.lower() == 'выйти':
                text = '/restart'

            if text == 'Меню' or text.lower() == 'меню' or text.lower() == 'в начало' or text.lower() == 'на главную':
                text = '/menu'

            # if text == 'Назад' or text.lower() == 'назад' or text.lower() == 'я ошибся' or text.lower() == 'ошибся' \
            #         or text.lower() == 'вернись назад' or text.lower() == 'отставить'  or text.lower() == 'уточняю'\
            #         or text.lower() == 'скорректируй':
            #     text = '/rewind'

            metadata['text_before_correct'] = text
            # КОРРЕКТОР сюда

            try:
                message = UserMessage(
                    text,
                    out_channel,
                    sender_id,
                    input_channel=self.name(),
                    metadata=metadata
                )
                logger.debug(f'message = {message}')
                await on_new_message(message)
                res = True
            except CancelledError :
                logger.error(
                    f"Message handling timed out for " f"user message '{text}'."
                )
                res = False
            logger.debug(f'res = {res}')

            logger.debug(f"Запрос обработан!!!")
            return response.text('success')

        return custom_telegram_webhook
