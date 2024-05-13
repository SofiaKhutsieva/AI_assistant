import logging
import os
import fpdf
import datetime

from typing import Any, Text, Dict, List, Optional
from rasa_sdk.events import SlotSet, FollowupAction, EventType, Restarted
from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
from fpdf import FPDF

# from utils.utils import compare_payloads
from utils.utils_documents import convert_file_to_base64
from utils.t2s.t2s import t2s_silero_model_ru_v3
from utils.utils_buttons import compare_payloads

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# -------------Сценарий "Отпуск"---------------

class ActionVacationInitialSlotSet(Action):
    def name(self) -> Text:
        return "action_vacation_init"

    def run(self, dispatcher, tracker, domain) -> List[EventType]:
        events = []

        logger.debug(f'tracker {tracker}')
        logger.debug(f'tracker.latest_message.get("text") {tracker.latest_message.get("text")}')
        logger.debug(f'tracker.get_intent_of_latest_message {tracker.get_intent_of_latest_message()}')
        logger.debug(f'tracker.latest_message.get("entities"), {tracker.latest_message.get("entities")}')
        logger.debug(
            f'tracker.get_latest_entity_values("vacation_start") {next(tracker.get_latest_entity_values("vacation_start"), None)}')
        logger.debug(
            f'tracker.get_latest_entity_values("vacation_duration") {next(tracker.get_latest_entity_values("vacation_duration"), None)}')
        logger.debug(
            f'tracker.get_latest_entity_values("vacation_type") {next(tracker.get_latest_entity_values("vacation_type"), None)}')

        # сущности
        vacation_type = next(tracker.get_latest_entity_values("vacation_type"), None) # доработать
        vacation_start = next(tracker.get_latest_entity_values("vacation_start"), None)  # доработать
        vacation_duration = next(tracker.get_latest_entity_values("vacation_duration"), None)  # доработать
        # сделать валидацию через интенты

        if vacation_type:
            events.append(SlotSet("slot_vacation_type", vacation_type))
        else:
            events.append(SlotSet("slot_vacation_type", None))
        if vacation_start:
            events.append(SlotSet("slot_vacation_start", vacation_start))
        else:
            events.append(SlotSet("slot_vacation_start", None))
        if vacation_duration and not vacation_duration.isdigit():
            events.append(SlotSet("slot_vacation_duration", vacation_duration))
        else:
            events.append(SlotSet("slot_vacation_duration", None))
        events.append(FollowupAction("vacation_form"))
        return events


class AskForSlotAction1(Action):
    def name(self) -> Text:
        return "action_ask_vacation_form_slot_vacation_type"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        text = 'В какой тип отпуска Вы хотите пойти?'
        buttons = [{"title": "оплачиваемый", "payload": "1"},
                   {"title": "неоплачиваемый", "payload": "2"},
                   {"title": "дополнительный", "payload": "3"}]
        dispatcher.utter_message(text=text, buttons=buttons)

        text = 'В какой тип о+тпуска Вы хотите пойти?'
        file_name = t2s_silero_model_ru_v3(text=text, buttons=buttons)
        encoded = convert_file_to_base64(file_name)
        dispatcher.utter_message(attachment=encoded, file_name=file_name)
        return []

class AskForSlotAction2(Action):
    def name(self) -> Text:
        return "action_ask_vacation_form_slot_vacation_start"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        text = 'С какого числа Вы планируете идти в отпуск?'
        dispatcher.utter_message(text=text)

        file_name = t2s_silero_model_ru_v3(text=text)
        encoded = convert_file_to_base64(file_name)
        dispatcher.utter_message(attachment=encoded, file_name=file_name)
        return []

class AskForSlotAction3(Action):
    def name(self) -> Text:
        return "action_ask_vacation_form_slot_vacation_duration"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        text = 'На сколько дней?'
        dispatcher.utter_message(text=text)

        file_name = t2s_silero_model_ru_v3(text=text)
        encoded = convert_file_to_base64(file_name)
        dispatcher.utter_message(attachment=encoded, file_name=file_name)
        return []

class AskForSlotAction4(Action):
    def name(self) -> Text:
        return "action_ask_vacation_form_slot_vacation_submit" # action_vacation_end

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        text = f'Отпуск:\n' \
               f'✅ Тип отпуска: {tracker.get_slot("slot_vacation_type").lower()}.\n' \
               f'✅ С какого числа: {tracker.get_slot("slot_vacation_start").lower()}.\n' \
               f'✅ На сколько дней: {tracker.get_slot("slot_vacation_duration").lower()}.\n'
        dispatcher.utter_message(text=text)
        text = text.replace('отпуска', 'о+тпуска')
        file_name = t2s_silero_model_ru_v3(text=text)
        encoded = convert_file_to_base64(file_name)
        dispatcher.utter_message(attachment=encoded, file_name=file_name)

        text = f'Отправляю Вам сформированную заявку. Подтверждаете регистрацию заявки?'
        buttons = [{"title" : "да", "payload" : "1"},
                   {"title" : "нет", "payload" : "2"}]
        dispatcher.utter_message(text=text, buttons=buttons)
        file_name = t2s_silero_model_ru_v3(text=text, buttons=buttons)
        encoded = convert_file_to_base64(file_name)
        dispatcher.utter_message(attachment=encoded, file_name=file_name)

        return []

class ValidateVacationForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_vacation_form"

    def validate_slot_vacation_type(
            self,
            slot_value: Any,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: DomainDict,
    ) -> Dict[Text, Any]:
        if slot_value:
            logger.debug(f'slot_vacation_type {slot_value}')
            slot_value = slot_value.lower().replace('облачиваемый', 'оплачиваемый').replace('воплачиваемый', 'в оплачиваемый').replace('вне', 'в не').replace('не оплачиваемый', 'неоплачиваемый')
            logger.debug(f'slot_vacation_type {slot_value}')
            buttons = [{"title": "оплачиваемый", "payload": "1"},
                       {"title": "неоплачиваемый", "payload": "2"},
                       {"title": "дополнительный", "payload": "3"}]
            dict_button = {button["payload"] : button["title"] for button in buttons}
            # if slot_value in ['1', '2', '3']:
            #     return {"slot_vacation_type" : dict_button[slot_value]}

            # доп валидация
            res, counter, _, _ = compare_payloads(dispatcher, slot_value, buttons=buttons, var=True, buttons_output=False)
            if res:
                logger.debug(f'vacation_type_ {dict_button[res]}')
                return {"slot_vacation_type" : dict_button[res]}

            # валидация через сущность
            if counter == 0:
                vacation_type = next(tracker.get_latest_entity_values("vacation_type"), None)
                logger.debug(f'vacation_type_entity {vacation_type}')
                if vacation_type and \
                        ('лачиваем' in vacation_type or 'дополнительн' in vacation_type):
                    return {"slot_vacation_type": vacation_type}

        # сделать валидацию через интенты
        return {"slot_vacation_type" : None}

    def validate_slot_vacation_start(
            self,
            slot_value: Any,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: DomainDict,
    ) -> Dict[Text, Any]:
        # валидацию через сущность сделать
        logger.debug(f'slot_vacation_start {slot_value}')
        # vacation_start = next(tracker.get_latest_entity_values("vacation_start"), None)
        logger.debug(f'tracker.latest_message.get("entities") {tracker.latest_message.get("entities")}')
        vacation_start_entity_diet = [a_['value'] for a_ in tracker.latest_message.get("entities") if
                          a_['entity'] == 'vacation_start' and a_['extractor'] == 'DIETClassifier']
        logger.debug(f'vacation_start_entity_diet {vacation_start_entity_diet}')
        vacation_start_entity_regex = [a_['value'] for a_ in tracker.latest_message.get("entities") if
                          a_['entity'] == 'vacation_start' and a_['extractor'] == 'RegexEntityExtractor']
        logger.debug(f'vacation_start_entity_regex {vacation_start_entity_regex}')
        if vacation_start_entity_regex and vacation_start_entity_regex[0]:
            vacation_start = vacation_start_entity_regex[0].lower().replace('с ', '')
            logger.debug(f'slot_vacation_start {vacation_start}')
            return {"slot_vacation_start": vacation_start}
        if vacation_start_entity_diet:
            vacation_start = vacation_start_entity_diet[0].lower().replace('с ', '')
            logger.debug(f'slot_vacation_start {vacation_start}')
            return {"slot_vacation_start": vacation_start}
        # сделать валидацию через интенты
        return {"slot_vacation_start" : None}

    def validate_slot_vacation_duration(
            self,
            slot_value: Any,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: DomainDict,
    ) -> Dict[Text, Any]:
        # валидацию через сущность сделать
        logger.debug(f'slot_vacation_duration {slot_value}')
        if slot_value and slot_value.isdigit():
            return {"slot_vacation_duration" : slot_value}
        # vacation_duration = next(tracker.get_latest_entity_values("vacation_duration"), None)
        logger.debug(f'tracker.latest_message.get("entities") {tracker.latest_message.get("entities")}')
        vacation_duration_entity_diet = [a_['value'] for a_ in tracker.latest_message.get("entities") if
                          a_['entity'] == 'vacation_duration' and a_['extractor'] == 'DIETClassifier']
        logger.debug(f'vacation_duration_entity_diet {vacation_duration_entity_diet}')
        vacation_duration_entity_regex = [a_['value'] for a_ in tracker.latest_message.get("entities") if
                          a_['entity'] == 'vacation_duration' and a_['extractor'] == 'RegexEntityExtractor']
        logger.debug(f'vacation_duration_entity_regex {vacation_duration_entity_regex}')
        if vacation_duration_entity_regex and vacation_duration_entity_regex[0]:
            vacation_duration = vacation_duration_entity_regex[0].lower().replace('на ', '')
            logger.debug(f'slot_vacation_duration {vacation_duration}')
            return {"slot_vacation_duration": vacation_duration}
        if vacation_duration_entity_diet and vacation_duration_entity_diet[0] and not vacation_duration_entity_diet[0].isdigit():
            vacation_duration = vacation_duration_entity_diet[0].lower().replace('на ', '')
            logger.debug(f'slot_vacation_duration {vacation_duration}')
            return {"slot_vacation_duration": vacation_duration}
        # сделать валидацию через интенты
        return {"slot_vacation_duration" : None}

    def validate_slot_vacation_submit(
            self,
            slot_value: Any,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: DomainDict,
    ) -> Dict[Text, Any]:
        # валидацию через сущность сделать
        logger.debug(f'slot_vacation_submit {slot_value}')
        slot_value = slot_value.lower()
        if ('да' in slot_value or 'подтвержадаю' in slot_value or slot_value == '1') and ('не' not in slot_value):
            text = 'Ваша заявка зарегистрирована.'
            dispatcher.utter_message(text=text)
            file_name = t2s_silero_model_ru_v3(text=text)
            encoded = convert_file_to_base64(file_name)
            dispatcher.utter_message(attachment=encoded, file_name=file_name)
            return {"slot_vacation_submit" : "1"}
        elif 'не' in slot_value or slot_value == '2':
            text = 'Ваша заявка не зарегистрирована.'
            dispatcher.utter_message(text=text)
            file_name = t2s_silero_model_ru_v3(text=text)
            encoded = convert_file_to_base64(file_name)
            dispatcher.utter_message(attachment=encoded, file_name=file_name)
            return {"slot_vacation_submit" : "2"}
        return {"slot_vacation_submit" : None}