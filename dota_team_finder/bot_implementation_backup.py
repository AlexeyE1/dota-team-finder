"""
БОТ ДЛЯ DOTA TEAM FINDER
Полная реализация чата с ботом для заполнения анкеты и поиска команды

СОДЕРЖАНИЕ:
1. Модель BotState (models.py)
2. BotChatView (views.py) 
3. URL для бота (urls.py)
4. Шаблоны (templates)
5. Изменения в chat.html
"""

# ============================================================================
# 1. МОДЕЛЬ BOTSTATE (добавить в direct_messages/models.py)
# ============================================================================

"""
class BotState(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='bot_state')
    
    # Этап диалога
    STAGE_CHOICES = [
        ('welcome', 'Приветствие'),
        ('role', 'Выбор роли'),
        ('mmr', 'MMR'),
        ('availability', 'Время доступности'),
        ('bio', 'О себе'),
        ('browsing', 'Просмотр анкет'),
        ('completed', 'Анкета заполнена'),
    ]
    current_stage = models.CharField(max_length=20, choices=STAGE_CHOICES, default='welcome')
    
    # Заполненные данные анкеты
    selected_role = models.IntegerField(
        choices=[
            (1, 'Carry'),
            (2, 'Mid'),
            (3, 'Offlane'),
            (4, 'Support'),
            (5, 'Hard Support'),
        ],
        null=True, blank=True
    )
    selected_mmr_range = models.CharField(max_length=20, null=True, blank=True)
    selected_availability = models.CharField(max_length=20, null=True, blank=True)
    bio_text = models.TextField(blank=True)
    
    # Фильтры для поиска анкет
    filter_mmr_min = models.IntegerField(null=True, blank=True)
    filter_mmr_max = models.IntegerField(null=True, blank=True)
    
    # Текущий просматриваемый пользователь
    current_profile_index = models.IntegerField(default=0)
    viewed_profiles = models.JSONField(default=list)  # Список ID просмотренных профилей
    
    # Временные метки
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Состояние бота'
        verbose_name_plural = 'Состояния ботов'
    
    def __str__(self):
        return f"BotState для {self.user.steam_nickname}"
    
    def reset_to_welcome(self):
        # Сброс к начальному состоянию
        self.current_stage = 'welcome'
        self.selected_role = None
        self.selected_mmr_range = None
        self.selected_availability = None
        self.bio_text = ''
        self.current_profile_index = 0
        self.viewed_profiles = []
        self.save()
    
    def is_questionnaire_completed(self):
        # Проверка, заполнена ли анкета
        return (
            self.selected_role is not None and
            self.selected_mmr_range and
            self.selected_availability and
            self.current_stage in ['browsing', 'completed']
        )
    
    def get_next_stage(self):
        # Получение следующего этапа анкеты
        stages = ['welcome', 'role', 'mmr', 'availability', 'bio', 'browsing']
        try:
            current_index = stages.index(self.current_stage)
            return stages[current_index + 1] if current_index + 1 < len(stages) else 'completed'
        except ValueError:
            return 'welcome'
"""

# ============================================================================
# 2. BOTCHATVIEW (добавить в direct_messages/views.py)
# ============================================================================

"""
from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import ChatGroup, BotState, ChatMessage
from .forms import ChatMessageForm
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from accounts.models import CustomUser
from django.http import Http404

class BotChatView(LoginRequiredMixin, TemplateView):
    template_name = 'direct_messages/chat.html'
    
    def dispatch(self, request, *args, **kwargs):
        self.user = request.user
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Получаем чат с ботом
        bot_chat = self.get_or_create_bot_chat()
        
        # Получаем или создаём состояние бота
        bot_state, created = BotState.objects.get_or_create(user=self.user)
        
        chat_messages = bot_chat.chat_messages.all()[:30][::-1]
        show_welcome = not chat_messages
        
        # Сборка списка чатов пользователя (как в обычном ChatView)
        user_chats = []
        private_chats = self.user.chat_groups.filter(is_private=True)
        for group in private_chats:
            if group.is_bot:
                user_chats.insert(0, {
                    'group_name': group.group_name,
                    'avatar_url': 'https://via.placeholder.com/40x40/007bff/ffffff?text=🤖',
                    'nickname': 'DotaFinderBot',
                    'slug': 'bot',
                    'last_message': 'Анкета и поиск команды',
                    'last_message_time': '',
                    'unread_count': 0,
                    'is_online': True,
                })
            else:
                companion = None
                for member in group.members.all():
                    if member != self.user:
                        companion = member
                        break
                if companion:
                    last_msg = group.chat_messages.first()
                    user_chats.append({
                        'group_name': group.group_name,
                        'avatar_url': companion.steam_avatar or 'https://media.steampowered.com/steamcommunity/public/images/avatars/fe/fef49e7fa7e1997310d705b2a6158ff8dc1cdfeb_full.jpg',
                        'nickname': companion.steam_nickname,
                        'slug': companion.slug,
                        'last_message': last_msg.body if last_msg else '',
                        'last_message_time': last_msg.created_at.strftime('%H:%M') if last_msg else '',
                        'unread_count': 0,
                        'is_online': group.users_online.filter(pk=companion.pk).exists(),
                    })
        
        context.update({
            'chatroom_name': bot_chat.group_name,
            'other_user': None,  # Для бота нет other_user
            'chat_messages': chat_messages,
            'user': self.user,
            'user_chats': user_chats,
            'form': ChatMessageForm(),
            'is_bot_chat': True,
            'show_welcome': show_welcome,
        })
        return context
    
    def get_or_create_bot_chat(self):
        if self.user.chat_groups.filter(is_bot=True).exists():
            return self.user.chat_groups.filter(is_bot=True).first()
        else:
            bot_chat = ChatGroup.objects.create(is_private=True, is_bot=True)
            bot_chat.members.add(self.user)
            return bot_chat
    
    def post(self, request, *args, **kwargs):
        form = ChatMessageForm(request.POST)
        if form.is_valid():
            message_text = form.cleaned_data['body']
            
            # Получаем чат с ботом
            bot_chat = self.get_or_create_bot_chat()
            
            # Сохраняем сообщение пользователя
            user_message = ChatMessage.objects.create(
                body=message_text,
                author=request.user,
                group=bot_chat
            )
            
            # Обрабатываем сообщение ботом
            bot_response = self.process_bot_message(message_text)
            
            # Возвращаем HTML с новым сообщением пользователя и ответом бота
            context = {
                'message': user_message, 
                'user': request.user,
                'bot_response': bot_response
            }
            return render(request, 'direct_messages/partials/bot_chat_message_p.html', context)
        else:
            return HttpResponse(status=204)
    
    def process_bot_message(self, message_text):
        # Обработка сообщения пользователя ботом
        bot_state, created = BotState.objects.get_or_create(user=self.user)
        
        # Обработка кнопок
        if message_text.startswith('button:'):
            action = message_text.split(':', 1)[1]
            return self.handle_button_action(bot_state, action)
        else:
            # Обработка текстового сообщения
            return self.handle_text_message(bot_state, message_text)
    
    def handle_button_action(self, bot_state, action):
        # Обработка нажатия кнопки
        if action == 'start_questionnaire':
            bot_state.current_stage = 'role'
            bot_state.save()
            return {
                'message': 'Какая у тебя основная роль?',
                'buttons': [
                    ['button:role_carry', 'Carry'],
                    ['button:role_mid', 'Mid'],
                    ['button:role_offlane', 'Offlane'],
                    ['button:role_support', 'Support'],
                    ['button:role_hard_support', 'Hard Support']
                ]
            }
        
        elif action.startswith('role_'):
            role_map = {
                'role_carry': 1, 'role_mid': 2, 'role_offlane': 3,
                'role_support': 4, 'role_hard_support': 5
            }
            bot_state.selected_role = role_map.get(action)
            bot_state.current_stage = 'mmr'
            bot_state.save()
            return {
                'message': 'Какой у тебя MMR?',
                'buttons': [
                    ['button:mmr_0_1000', '<1000'],
                    ['button:mmr_1000_2000', '1000-2000'],
                    ['button:mmr_2000_3000', '2000-3000'],
                    ['button:mmr_3000_4000', '3000-4000'],
                    ['button:mmr_4000_plus', '4000+'],
                    ['button:mmr_unknown', 'Не знаю']
                ]
            }
        
        elif action.startswith('mmr_'):
            mmr_map = {
                'mmr_0_1000': '<1000',
                'mmr_1000_2000': '1000-2000',
                'mmr_2000_3000': '2000-3000',
                'mmr_3000_4000': '3000-4000',
                'mmr_4000_plus': '4000+',
                'mmr_unknown': 'Не знаю'
            }
            bot_state.selected_mmr_range = mmr_map.get(action)
            bot_state.current_stage = 'availability'
            bot_state.save()
            return {
                'message': 'В какое время ты обычно играешь?',
                'buttons': [
                    ['button:availability_morning', 'Утро (6:00-12:00)'],
                    ['button:availability_day', 'День (12:00-18:00)'],
                    ['button:availability_evening', 'Вечер (18:00-00:00)'],
                    ['button:availability_night', 'Ночь (00:00-6:00)'],
                    ['button:availability_any', 'Любое время']
                ]
            }
        
        elif action.startswith('availability_'):
            availability_map = {
                'availability_morning': 'Утро (6:00-12:00)',
                'availability_day': 'День (12:00-18:00)',
                'availability_evening': 'Вечер (18:00-00:00)',
                'availability_night': 'Ночь (00:00-6:00)',
                'availability_any': 'Любое время'
            }
            bot_state.selected_availability = availability_map.get(action)
            bot_state.current_stage = 'bio'
            bot_state.save()
            return {
                'message': 'Расскажи немного о себе (опционально)',
                'buttons': [
                    ['button:bio_skip', 'Пропустить'],
                    ['button:bio_write', 'Написать']
                ]
            }
        
        elif action == 'bio_skip':
            bot_state.current_stage = 'browsing'
            bot_state.save()
            return self.show_next_profile(bot_state)
        
        elif action == 'next_profile':
            return self.show_next_profile(bot_state)
        
        elif action.startswith('write_to_user_'):
            user_id = action.split('_')[-1]
            try:
                target_user = CustomUser.objects.get(pk=user_id)
                # Создаём чат с пользователем
                chat_url = f"/direct_messages/chat/{target_user.slug}/"
                return {
                    'message': f'Отлично! Я создал чат с {target_user.steam_nickname}. Переходи по ссылке:',
                    'buttons': [
                        [f'link:{chat_url}', f'Написать {target_user.steam_nickname}']
                    ]
                }
            except CustomUser.DoesNotExist:
                return {
                    'message': 'Пользователь не найден.',
                    'buttons': [['button:next_profile', 'Следующая анкета']]
                }
        
        return {
            'message': 'Неизвестная команда.',
            'buttons': [['button:start_questionnaire', 'Начать заново']]
        }
    
    def handle_text_message(self, bot_state, message_text):
        # Обработка текстового сообщения
        if bot_state.current_stage == 'bio':
            bot_state.bio_text = message_text
            bot_state.current_stage = 'browsing'
            bot_state.save()
            return self.show_next_profile(bot_state)
        
        return {
            'message': 'Пожалуйста, используй кнопки для ответа.',
            'buttons': [['button:start_questionnaire', 'Начать заново']]
        }
    
    def show_next_profile(self, bot_state):
        # Показать следующую анкету пользователя
        # Получаем пользователей по фильтру
        users = CustomUser.objects.exclude(pk=self.user.pk)
        
        if bot_state.selected_role:
            users = users.filter(role=bot_state.selected_role)
        
        # Исключаем уже просмотренных
        if bot_state.viewed_profiles:
            users = users.exclude(pk__in=bot_state.viewed_profiles)
        
        if users.exists():
            user = users[bot_state.current_profile_index % users.count()]
            bot_state.viewed_profiles.append(user.pk)
            bot_state.current_profile_index += 1
            bot_state.save()
            
            role_display = dict(CustomUser._meta.get_field('role').choices).get(user.role, 'Не указана')
            
            return {
                'message': f'''
👤 **{user.steam_nickname}**
🎯 **Роль:** {role_display}
📊 **MMR:** {user.mmr or 'Не указан'}
📝 **О себе:** {user.bio or 'Не указано'}
                '''.strip(),
                'buttons': [
                    ['button:next_profile', 'Следующая анкета'],
                    [f'button:write_to_user_{user.pk}', f'Написать {user.steam_nickname}']
                ]
            }
        else:
            return {
                'message': 'Больше анкет не найдено. Попробуй изменить фильтр!',
                'buttons': [
                    ['button:start_questionnaire', 'Заполнить анкету заново']
                ]
            }
    
    def send_bot_message(self, chat_group, message_text, buttons=None):
        # Отправить сообщение от имени бота
        # Пока просто возвращаем None, сообщения бота будут создаваться в другом месте
        return None
"""

# ============================================================================
# 3. URL ДЛЯ БОТА (добавить в direct_messages/urls.py)
# ============================================================================

"""
from django.urls import path
from .views import ChatView, get_or_create_chat, BotChatView

app_name = 'direct_messages'

urlpatterns = [
    path('', ChatView.as_view(), name='chat'),
    path('chat/bot/', BotChatView.as_view(), name='bot-chat'),  # Сначала более специфичный
    path('chat/<slug:slug_profile>/', get_or_create_chat, name='start-chat'),  # Потом общий
    path('chat/room/<chatroom_name>/', ChatView.as_view(), name='chatroom'),
]
"""

# ============================================================================
# 4. ШАБЛОН BOT_CHAT_MESSAGE_P.HTML (создать direct_messages/templates/direct_messages/partials/bot_chat_message_p.html)
# ============================================================================

"""
<div id='chat_messages'>

<div class="fade-in-up">
    <!-- Сообщение пользователя -->
    {% include "direct_messages/chat_message.html" %}
    
    <!-- Ответ бота с кнопками -->
    {% if bot_response %}
    <div class="message-item incoming">
        <div class="message-avatar">
            <img src="https://via.placeholder.com/40x40/007bff/ffffff?text=🤖" class="rounded-circle" alt="Bot Avatar" width="40" height="40">
        </div>
        <div class="message-body">
            <div class="message-content">
                <p>{{ bot_response.message|linebreaks }}</p>
                
                <!-- Кнопки бота -->
                {% if bot_response.buttons %}
                <div class="bot-buttons mt-2">
                    {% for button in bot_response.buttons %}
                        {% if button.0.startswith('button:') %}
                            <button class="btn btn-outline-primary btn-sm me-2 mb-1" 
                                    onclick="sendBotButton('{{ button.0 }}')">
                                {{ button.1 }}
                            </button>
                        {% elif button.0.startswith('link:') %}
                            <a href="{{ button.0|slice:'5:' }}" class="btn btn-primary btn-sm me-2 mb-1">
                                {{ button.1 }}
                            </a>
                        {% endif %}
                    {% endfor %}
                </div>
                {% endif %}
            </div>
            <div class="message-author-info">
                <strong>DotaFinderBot</strong>
                <span>@bot</span>
            </div>
        </div>
    </div>
    {% endif %}
</div>

<style>
    @keyframes fadeInAndUp {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .fade-in-up {
        animation: fadeInAndUp 0.3s ease;
    }
    
    .bot-buttons {
        display: flex;
        flex-wrap: wrap;
        gap: 5px;
    }
    
    .bot-buttons .btn {
        font-size: 0.9rem;
        padding: 0.25rem 0.5rem;
    }
</style>

<script>
    function sendBotButton(buttonAction) {
        const form = document.querySelector('form');
        const input = form.querySelector('input[name="body"], textarea[name="body"]');
        input.value = buttonAction;
        form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
    }
    scrollToBottom();
</script>

</div>
"""

# ============================================================================
# 5. ИЗМЕНЕНИЯ В CHAT.HTML (добавить в direct_messages/templates/direct_messages/chat.html)
# ============================================================================

"""
1. Добавить кнопку чата с ботом в левую менюшку:
   <!-- Кнопка чата с ботом -->
   <div class="p-3 border-bottom">
       <a href="{% url 'direct_messages:bot-chat' %}" class="btn btn-primary w-100">
           <i class="fas fa-robot me-2"></i>Чат с ботом
       </a>
   </div>

2. Добавить приветствие бота, если чат пустой:
   {% if is_bot_chat and show_welcome %}
   <div class="message-item incoming">
       <div class="message-avatar">
           <img src="https://via.placeholder.com/40x40/007bff/ffffff?text=🤖" class="rounded-circle" alt="Bot Avatar" width="40" height="40">
       </div>
       <div class="message-body">
           <div class="message-content">
               <p>Привет! Я помогу тебе найти команду. Давай заполним анкету!</p>
               <button class="btn btn-outline-primary btn-sm mt-2" onclick="sendBotButton('button:start_questionnaire')">Начать заполнение анкеты</button>
           </div>
           <div class="message-author-info">
               <strong>DotaFinderBot</strong>
               <span>@bot</span>
           </div>
       </div>
   </div>
   {% endif %}

3. Изменить форму для работы с HTMX:
   <form method="post" class="w-100"
    {% if is_bot_chat %}
    hx-post="{% url 'direct_messages:bot-chat' %}"
    hx-target="#chat_messages"
    hx-swap="innerHTML"
    {% elif chatroom_name %}
    hx-ext='ws'
    ws-connect='/ws/chatroom/{{ chatroom_name }}'
    ws-send
    _="on htmx:wsAfterSend reset() me"
    {% endif %}>
       {% csrf_token %}
       <div class="input-group">
           {{ form.body }}
           <button type="submit" class="btn btn-primary">Отправить</button>
       </div>
   </form>
"""

# ============================================================================
# 6. ДОБАВИТЬ В МОДЕЛЬ CHATGROUP (direct_messages/models.py)
# ============================================================================

"""
class ChatGroup(models.Model):
    group_name = models.CharField(max_length=128, unique=True, default=shortuuid.uuid())
    users_online = models.ManyToManyField(CustomUser, related_name='online_in_groups', blank=True)
    members = models.ManyToManyField(CustomUser, related_name='chat_groups', blank=True)
    is_private = models.BooleanField(default=False)
    is_bot = models.BooleanField(default=False)  # Флаг для чата с ботом

    def __str__(self):
        return self.group_name
"""

# ============================================================================
# 7. МИГРАЦИИ
# ============================================================================

"""
Создать миграции:
python manage.py makemigrations direct_messages
python manage.py migrate
"""

# ============================================================================
# 8. ЛОГИКА РАБОТЫ БОТА
# ============================================================================

"""
ЭТАПЫ ДИАЛОГА:
1. welcome - Приветствие
2. role - Выбор роли (Carry, Mid, Offlane, Support, Hard Support)
3. mmr - MMR (<1000, 1000-2000, 2000-3000, 3000-4000, 4000+, Не знаю)
4. availability - Время доступности (Утро, День, Вечер, Ночь, Любое время)
5. bio - О себе (опционально)
6. browsing - Просмотр анкет других пользователей

КНОПКИ:
- button:start_questionnaire - Начать заполнение анкеты
- button:role_carry - Выбрать роль Carry
- button:mmr_2000_3000 - Выбрать MMR 2000-3000
- button:availability_evening - Выбрать время "Вечер"
- button:bio_skip - Пропустить описание
- button:next_profile - Следующая анкета
- button:write_to_user_123 - Написать пользователю с ID 123

ФИЛЬТРАЦИЯ:
- По роли (если пользователь выбрал роль)
- Исключение уже просмотренных пользователей
- Циклический перебор (если пользователей больше нет, начинаем сначала)

ТЕХНОЛОГИИ:
- Django Views (BotChatView)
- HTMX для асинхронных запросов
- Модель BotState для хранения состояния диалога
- Шаблоны Django для отображения
- JavaScript для обработки кнопок
""" 