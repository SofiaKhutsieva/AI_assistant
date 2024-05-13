import logging

from typing import Any, Text, Dict, List, Optional
from rasa_sdk.events import SlotSet, FollowupAction, EventType, Restarted, UserUtteranceReverted, ActionReverted, \
ConversationPaused
from rasa_sdk import Action, Tracker

from utils.t2s.t2s import t2s_silero_model_ru_v3
from utils.utils_documents import convert_file_to_base64

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class ActionRestart(Action):
    def name(self) -> Text:
        return "action_restart"

    async def run(self, dispatcher, tracker, domain) -> List[EventType]:
        text = 'Рад был помочь!'
        dispatcher.utter_message(text=text)
        file_name = t2s_silero_model_ru_v3(text=text)
        encoded = convert_file_to_base64(file_name)
        dispatcher.utter_message(attachment=encoded, file_name=file_name)
        return [Restarted()]

class ActionRestart2(Action):
    def name(self) -> Text:
        return "action_restart_without_text"

    async def run(self, dispatcher, tracker, domain) -> List[EventType]:
        return [Restarted()]

class ActionMenu(Action):
    def name(self) -> Text:
        return "action_menu"

    async def run(self, dispatcher, tracker, domain) -> List[EventType]:
        return [Restarted(), FollowupAction('greeting_form')]

class ActionRewind(Action):
    def name(self) -> Text:
        return "action_rewind"  #action_rewind action_default_fallback action_back

    def run(self, dispatcher, tracker, domain) -> List[EventType]:

        #dispatcher.utter_message(text='назад')

        def undo_till_previous(event_type: Text, done_events: List[Dict[Text, Any]]) :
            """Removes events from `done_events` until the first
            occurrence `event_type` is found which is also removed."""
            # list gets modified - hence we need to copy events!
            for e in reversed(done_events[:]) :
                del done_events[-1]
                if e["event"] == event_type :
                    break

        def logger_event_type(applied_events):
            for event in applied_events :
                event_type = event.get("event")
                logger.debug(event_type)

        def logger_event_name(applied_events):
            for event in applied_events :
                event_name = event.get("name")
                logger.debug(event_name)

        events_all = tracker.events
        logger.debug("event_type_all")
        logger_event_type(events_all)

        # applied_events = tracker.events_after_latest_restart()
        # undo_till_previous("action", applied_events)
        # undo_till_previous("action", applied_events)
        # slot_rewind = applied_events
        slot_rewind = []

        # if not tracker.get_slot("slot_rewind"):
        #     logger.debug("not tracker.get_slot")
        #     applied_events = tracker.events_after_latest_restart()
        # else:
        #     logger.debug("tracker.get_slot")
        #     applied_events = tracker.get_slot("slot_rewind")
        applied_events = tracker.events_after_latest_restart()
        # действия 1 .. N
        # действие[i] = action .. action user user_featurization

        logger.debug("event_name")
        logger_event_name(applied_events)

        logger.debug("event_type")
        logger_event_type(applied_events)
        # удаляем action и user последнего действия (вызов кнопки назад)
        undo_till_previous("user", applied_events)
        logger.debug("event_type_new1")
        logger_event_type(applied_events)

        undo_till_previous("action", applied_events)
        logger.debug("event_type_new2")
        logger_event_type(applied_events)

        # удаляем action и user предпоследнего действия
        undo_till_previous("user", applied_events)
        logger.debug("event_type_new3")
        logger_event_type(applied_events)

        undo_till_previous("action", applied_events)
        logger.debug("event_type_new4")
        logger_event_type(applied_events)

        # оставляем только предпоследнее действие (удаляем все действия до него)
        event_type_ = []
        for event in applied_events :
            event_type_.append(event.get("event"))

        for _ in range(event_type_.count("user_featurization")) :
            for e in applied_events[:] :
                del applied_events[0]
                if e["event"] == "user_featurization" :
                    break
        logger.debug("event_type_new5")
        logger_event_type(applied_events)

        if not applied_events:
            return [FollowupAction("action_menu")]

# ДОБАВИТЬ УЧЕТ ТОГО, ЧТО ЕСЛИ ЕСТЬ ОТПРАВКА ВО ВНЕШНИЙ СЕРВЕР, ТО КНОПКА НАЗАД НЕ ДОЛЖНА РАБОТАТЬ
        return applied_events #, SlotSet("slot_rewind", slot_rewind)


        # def applied_events(self) -> List[Dict[Text, Any]] :
        #     """Returns all actions that should be applied - w/o reverted events."""
        #
        #     def undo_till_previous(event_type: Text, done_events: List[Dict[Text, Any]]) :
        #         """Removes events from `done_events` until the first
        #         occurrence `event_type` is found which is also removed."""
        #         # list gets modified - hence we need to copy events!
        #         for e in reversed(done_events[:]) :
        #             del done_events[-1]
        #             if e["event"] == event_type :
        #                 break
        #
        #     applied_events: List[Dict[Text, Any]] = []
        #     for event in self.events :
        #         event_type = event.get("event")
        #         if event_type == "restart" :
        #             applied_events = []
        #         elif event_type == "undo" :
        #             undo_till_previous("action", applied_events)
        #         elif event_type == "rewind" :
        #             # Seeing a user uttered event automatically implies there was
        #             # a listen event right before it, so we'll first rewind the
        #             # user utterance, then get the action right before it (also removes
        #             # the `action_listen` action right before it).
        #             undo_till_previous("user", applied_events)
        #             undo_till_previous("action", applied_events)
        #         else :
        #             applied_events.append(event)
        #     return applied_events

        #return [UserUtteranceReverted()]

class ActionUndo(Action):
    def name(self) -> Text:
        return "action_undo"

    def run(self, dispatcher, tracker, domain) -> List[EventType]:
        #dispatcher.utter_message(template="my_custom_fallback_template")
        dispatcher.utter_message(text='undo')
        return [ActionReverted()]

class ActionMessage(Action):
    def name(self) -> Text:
        return "action_message"

    def run(self, dispatcher, tracker, domain) -> List[EventType]:
        text = tracker.latest_message['text']
        logger.debug('text')
        logger.debug(text)
        applied_events = tracker.events_after_latest_restart()
        logger.debug('applied_events')
        logger.debug(applied_events)
        text_user = []
        for event in applied_events :
            event_type = event.get("event")
            if event_type == 'user':
                text_user.append(event.get("text"))
        logger.debug('text_user')
        logger.debug(text_user)
        dispatcher.utter_message(text=text_user[-2]) # предпоследнее, последнее = /message
        return [applied_events[-1]]


