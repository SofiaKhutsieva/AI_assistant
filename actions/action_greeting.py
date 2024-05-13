import logging
import os

from typing import Any, Text, Dict, List, Optional
from rasa_sdk.events import SlotSet, FollowupAction, EventType, Restarted
from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict

# from utils.utils import compare_payloads
from utils.t2s.t2s import t2s_silero_model_ru_v3
from utils.utils_documents import convert_file_to_base64

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# -------------Сценарий "Приветствие"---------------

class AskForGreetingForm(Action):
    def __init__(self):
        self.orders = [f'✅ 1. Оформить отпуск',
                       f'✅ 2. Получить шаблоны документов',
                       # f'✅ 3. Финансовый рынок - акции'
                       ]

    def name(self) -> Text:
        return 'action_ask_greeting_form_slot_greeting_answer'

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        events = []
        logger.debug(f'tracker.get_latest_input_channel() {tracker.get_latest_input_channel()}')
        logger.debug(f'tracker.current_state() {tracker.current_state()}')
        text = [f"Добро пожаловать!\n" # <b> </b>
                f"Я виртуальный ассистент.\n"
                f"Вы можете с помощью меня:\n"]
        text.extend(self.orders)
        result = '\n'.join(text)
        buttons = list(range(1, len(self.orders) + 1))
        buttons = [{'title' : button, 'payload' : button} for button in buttons]
        dispatcher.utter_message(text=result, buttons=buttons)

        file_name = t2s_silero_model_ru_v3(text=result)
        encoded = convert_file_to_base64(file_name)
        dispatcher.utter_message(attachment=encoded, file_name=file_name)
        return events

class ValidateGreetingForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_greeting_form"

    def validate_slot_greeting_answer(
            self,
            slot_value: Any,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: DomainDict,
    ) -> Dict[Text, Any]:
        greeting_answer = slot_value
        logger.debug(f'!!! greeting_answer {greeting_answer}')
        # title = [f'1. Оформить отпуск',
        #                f'2. Шаблоны документов',
        #                # f'3. Финансовый рынок - акции'
        #          ]
        # buttons =  list(range(1, len(title) + 1))
        # buttons = [{'title': button, 'payload': button} for button in buttons]
        # res, _, _, _ = compare_payloads(dispatcher, greeting_answer, buttons, title=title, var=False, buttons_output=False)
        res = greeting_answer
        if res and res in ['1', '2', '3']:
            logger.debug(f'res = {res}')
            return {"slot_greeting_answer": res}
        intent = tracker.get_intent_of_latest_message()
        if intent:
            logger.debug(f'intent = {intent}')
            if intent == 'Отпуск':
                return {"slot_greeting_answer" : '1'}
            if intent == 'Шаблоны':
                return {"slot_greeting_answer" : '2'}
        else:
            return {"slot_greeting_answer" : None}


class SubmitGreetingForm(Action):
    def __init__(self):
        self.forms = ['action_vacation_init',
                      'action_document_tmpl_init',
                      # 'stocks_form'
                      ]

    def name(self) -> Text:
        return 'action_submit_greeting_form'

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
            ) -> List[EventType]:
        res = tracker.get_slot("slot_greeting_answer")
        if res and res in ['1', '2']:
            return [FollowupAction(self.forms[int(res) - 1])]
        else:
            logger.debug(f'tracker.get_intent_of_latest_message {tracker.get_intent_of_latest_message()}')
            dispatcher.utter_message(text='Извините, я Вас не понял')
            return [SlotSet("slot_greeting_answer", None), Restarted()]
