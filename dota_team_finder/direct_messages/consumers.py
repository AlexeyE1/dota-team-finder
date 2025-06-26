from channels.generic.websocket import WebsocketConsumer
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from asgiref.sync import async_to_sync
import json
from .models import *
import ranktier


class ChatroomConsumer(WebsocketConsumer):
    def connect(self):
        self.user = self.scope['user']
        self.chatroom_name = self.scope['url_route']['kwargs']['chatroom_name']
        self.chatroom = get_object_or_404(ChatGroup, group_name=self.chatroom_name)

        async_to_sync(self.channel_layer.group_add)(
            self.chatroom_name,
            self.channel_name
        )

        # add adn update online users
        if self.user not in self.chatroom.users_online.all():
            self.chatroom.users_online.add(self.user)
            self.update_online_count()

        self.accept()
    
    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.chatroom_name,
            self.channel_name
        )

        # remove and update online users
        if self.user in self.chatroom.users_online.all():
            self.chatroom.users_online.remove(self.user)
            self.update_online_count()
    
    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        body = text_data_json['body']

        message = ChatMessage.objects.create(
            body=body,
            author=self.user,
            group=self.chatroom
        )

        event = {
            'type': 'message_handler',
            'message_id': message.id,
        }

        async_to_sync(self.channel_layer.group_send)(
            self.chatroom_name, event
        )

    def message_handler(self, event):
        message_id = event['message_id']
        message = ChatMessage.objects.get(id=message_id)
        context = {
            'message': message,
            'user': self.user,
        }

        html = render_to_string('direct_messages/partials/chat_message_p.html', context=context)
        self.send(text_data=html)
    
    def update_online_count(self):
        online_count = self.chatroom.users_online.count() - 1

        event = {
            'type': 'online_count_handler',
            'online_count': online_count
        }
        async_to_sync(self.channel_layer.group_send)(self.chatroom_name, event)
    
    def online_count_handler(self, event):
        online_count = event['online_count']
        html = render_to_string('direct_messages/partials/online_count.html', {'online_count': online_count})
        self.send(text_data=html)


class BotChatConsumer(WebsocketConsumer):
    QUESTIONS = [
        {'key': 'age', 'text': 'Сколько тебе лет?', 'type': 'text'},
        {'key': 'gender', 'text': 'Какой у тебя пол?', 'type': 'buttons', 'buttons': [
            {'text': 'Мужской', 'value': 'male'},
            {'text': 'Женский', 'value': 'female'}
        ]},
        {'key': 'country', 'text': 'В какой ты стране?', 'type': 'text'},
        {'key': 'role', 'text': 'Какая у тебя роль?', 'type': 'buttons', 'buttons': [
            {'text': 'Керри', 'value': '1'},
            {'text': 'Саппорт', 'value': '5'},
            {'text': 'Оффлейн', 'value': '3'}
        ]},
        {'key': 'available_from', 'text': 'Когда ты можешь играть?', 'type': 'buttons', 'buttons': [
            {'text': 'Вечер', 'value': '17:00'},
            {'text': 'Ночь', 'value': '23:00'},
            {'text': 'Утро', 'value': '05:00'},
            {'text': 'День', 'value': '11:00'}
        ]},
        {'key': 'bio', 'text': 'Расскажи о себе', 'type': 'text'},
        {'key': 'mmr', 'text': 'Какой твой MMR?', 'type': 'text'},
    ]

    def connect(self):
        self.user = self.scope['user']
        self.accept()
        # Начать с приветствия и кнопки
        self.send(text_data=json.dumps({
            'message': 'Привет! Давай заполним анкету. Нажми кнопку, чтобы начать.',
            'buttons': [
                {'text': 'Давай начнем', 'value': 'start'}
            ],
            'question_key': 'start'
        }))

    def receive(self, text_data=None, bytes_data=None):
        print(text_data)
        if not text_data:
            return
        data = json.loads(text_data)
        question_key = data.get('question_key')
        answer = data.get('answer')

        if question_key != 'profile_action':
            # Проверка на число
            if question_key == 'age':
                try:
                    answer = int(answer)
                except Exception:
                    self.send(text_data=json.dumps({'message': 'Пожалуйста, введи число.', 'question_key': question_key}))
            
            # Сохраняем ключ вопроса
            if question_key != 'start':
                setattr(self.user, question_key, answer)
                self.user.save()

            # Если возраст не указан, отправляем первый вопрос
            if self.user.age is None:
                self.send_question(0)
                return
            
            if self.user.gender is None:
                self.send_question(1)
                return
            
            if self.user.country is None:
                self.send_question(2)
                return
            
            if self.user.role is None:
                self.send_question(3)
                return
            
            if self.user.available_from is None:
                self.send_question(4)
                return
            
            if self.user.bio is None:
                self.send_question(5)
                return
            
            
            self.send(text_data=json.dumps({
                'message': 'Вот твоя анкета.',
                'profile': {
                    'age': self.user.age or '-',
                    'gender': self.user.gender or '-',
                    'country': self.user.country or '-',
                    'role': self.user.role or '-',
                    'available_from': str(self.user.available_from) if self.user.available_from else '-',
                    'bio': self.user.bio or '-',
                    'mmr': str(ranktier.Rank(self.user.rank[0] + self.user.rank[-1])) or '-'
                },
                'buttons': [
                    {'text': 'Изменить анкету', 'value': 'edit_profile'},
                    {'text': 'Поиск', 'value': 'start_search'}
                ],
                'question_key': 'profile_action'
            }))
        else:
            if answer == 'edit_profile':
                self.reset_questionnaire()
                return


    def send_question(self, idx):
        q = self.QUESTIONS[idx]
        payload = {
            'message': q['text'],
            'question_key': q['key']
        }
        if q.get('type') == 'buttons':
            payload['buttons'] = q['buttons']
        self.send(text_data=json.dumps(payload))
    
    def reset_questionnaire(self):
        self.user.age = None
        self.user.gender = None
        self.user.country = None
        self.user.role = None
        self.user.available_from = None
        self.user.bio = None
        self.user.mmr = None
        self.user.save()
        self.send_question(0)
 