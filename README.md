# **AI_assistant**
<hr>

Данный репозиторий содержит ai-ассистента, реализованного на rasa.  

## **Начало работы**
<hr>

```$ git clone git@github.com:SofiaKhutsieva/ai_assistant.git```  
```$ pip install -r requirements.txt```

<br>

## **Возможности**  
<hr>

- формирование сценариев (entity-recognition, intent-classification);  
- поддержка t2s (silero);  
- поддержка s2t (whisper);  
- отправка / прием документов;  
- развертывание в телеграм.  

возможные доработки:  
-корректор  
-добавление llm  


<br>

## **Как пользоваться**  
<hr>

в credentials.yml указать свои значения:
- access_token
- verify
- webhook_url  

https://main--rasahq.netlify.app/docs/rasa/next/connectors/telegram

webhook_url = ```https://<host>:<port>/webhooks/telegram/webhook```  
если с локального ```https://<host>:<port>``` = ngrok http 5005  
если с удаленного сервера, то указать соответсвующие параметры host и port + настройки nginx


```rasa train``` - переобучение (при изменениях в nlu и domain)  
```rasa shell``` - запуск бота через командную строку  

```rasa run actions --debug``` - запуск экшенов  
```rasa run --debug``` - запуск кора  
```rasa run --enable-api --debug``` - запуск кора с сервера  

<br>

## **Структура папок**
<hr>

<pre>
├── actions             <- сценарии
│   ├── action_base.py              <- базовые сценарии (рестарт, меню)
│   ├── action_document_tmpl.py     <- сценарий отправки шаблона документа
│   ├── action_greeting.py          <- сценарий приветсвия
│   └── action_vacation.py          <- сценарий отпуска
├── channels            <- коннектор 
│   └── custom_telegram_channel.py  <- кастомный коннектор для телеграма
├── data                <- данные
│   ├── nlu.yaml                    <- выборка для обучения (entity-recognition, intent-classification)
│   ├── rules.yaml                  <- правила
│   └── stories.yaml                <- истории
├── utils               <- утилиты   
│   ├── s2t                         <- s2t
│   ├── t2s                         <- t2s
│   ├── spell_checker               <- корректор
│   ├── utils_buttons.py            <- кнопки (валидация)
│   └── utils_documents.py          <- отправка / прием документов
├── config.yml          <- конфиг (модель)
├── credentials.yml     <- credentials (работа с каналами)
├── domain.yml          <- domain (все что используется в ассистенте: слоты, экшены, интенты, ...)
├── endpoints.yml       <- endpoints
└── README.md           <- описание проекта