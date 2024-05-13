import logging
import os

from typing import Any, Text, Dict, List, Optional
from rasa_sdk.events import SlotSet, FollowupAction, EventType, Restarted
from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict

# from utils.utils import compare_payloads
from utils.t2s.t2s import t2s_silero_model_ru_v3
from utils.utils_buttons import compare_payloads
from utils.utils_documents import convert_file_to_base64

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# -------------Сценарий "Шаблоны документов"---------------

class ActionVacationInitialSlotSet(Action):
    def name(self) -> Text:
        return "action_document_tmpl_init"

    def run(self, dispatcher, tracker, domain) -> List[EventType]:
        events = []

        logger.debug(f'tracker {tracker}')
        logger.debug(f'tracker.latest_message.get("text") {tracker.latest_message.get("text")}')
        logger.debug(f'tracker.get_intent_of_latest_message {tracker.get_intent_of_latest_message()}')
        logger.debug(f'tracker.latest_message.get("entities"), {tracker.latest_message.get("entities")}')
        logger.debug(
            f'tracker.get_latest_entity_values("document_tmpl_type") {next(tracker.get_latest_entity_values("document_tmpl_type"), None)}')

        document_tmpl_type = next(tracker.get_latest_entity_values("document_tmpl_type"), None) # доработать
        if document_tmpl_type:
            events.append(SlotSet("slot_document_tmpl_type", document_tmpl_type))
        else:
            events.append(SlotSet("slot_document_tmpl_type", None))
        events.append(FollowupAction("document_tmpl_form"))
        return events


class AskForSlotAction1(Action):
    def name(self) -> Text:
        return "action_ask_document_tmpl_form_slot_document_tmpl_type"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        text = 'Какой шаблон заявления Вам нужен?'
        buttons = [{"title": "на отпуск", "payload": "1"},
                   {"title": "на командировку", "payload": "2"},
                   {"title": "на перевод", "payload": "3"}]
        logger.debug(f'getcwd {os.getcwd()}')
        dispatcher.utter_message(text=text, buttons=buttons)

        file_name = t2s_silero_model_ru_v3(text=text, buttons=buttons)
        encoded = convert_file_to_base64(file_name)
        dispatcher.utter_message(attachment=encoded, file_name=file_name)
        return []

class AskForSlotAction4(Action):
    def name(self) -> Text:
        return "action_document_tmpl_end"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:

        type = tracker.get_slot("slot_document_tmpl_type")
        if 'отпуск' in type:
            file_name = 'шаблон на отпуск.pdf'
        elif 'командировк' in type:
            file_name = 'шаблон на командировку.pdf'
        elif 'перевод' in type:
            file_name = 'шаблон на перевод.pdf'
        document_path = os.path.join("files", "documents_tmpl", file_name)
        encoded = convert_file_to_base64(document_path)
        dispatcher.utter_message(attachment=encoded, file_name=file_name)

        text = f'Отправляю Вам шаблон документа. '
        dispatcher.utter_message(text=text)

        file_name = t2s_silero_model_ru_v3(text=text)
        encoded = convert_file_to_base64(file_name)
        dispatcher.utter_message(attachment=encoded, file_name=file_name)
        return []

class ValidateVacationForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_document_tmpl_form"

    def validate_slot_document_tmpl_type(
            self,
            slot_value: Any,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: DomainDict,
    ) -> Dict[Text, Any]:

        if slot_value:
            logger.debug(f'slot_document_tmpl_type {slot_value}')
            buttons = [{"title": "на отпуск", "payload": "1"},
                       {"title": "на командировку", "payload": "2"},
                       {"title": "на перевод", "payload": "3"}]
            dict_button = {button["payload"] : button["title"] for button in buttons}
            # if slot_value in ['1', '2', '3']:
            #     return {"slot_document_tmpl_type" : dict_button[slot_value]}

            # доп валидация
            res, counter, _, _ = compare_payloads(dispatcher, slot_value, buttons=buttons, var=True, buttons_output=False)
            if res:
                logger.debug(f'document_tmpl_type_ {dict_button[res]}')
                return {"slot_document_tmpl_type" : dict_button[res]}

            # валидация через сущность
            if counter == 0:
                document_tmpl_type = next(tracker.get_latest_entity_values("document_tmpl_type"), None)
                logger.debug(f'document_tmpl_type_entity {document_tmpl_type}')
                if document_tmpl_type and \
                        ('отпуск' in document_tmpl_type or 'командировк' in document_tmpl_type or 'перевод' in document_tmpl_type):
                    return {"slot_document_tmpl_type": document_tmpl_type}

        # сделать валидацию через интенты
        return {"slot_document_tmpl_type" : None}