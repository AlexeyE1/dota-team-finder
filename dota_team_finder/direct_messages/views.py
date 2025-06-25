from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import ChatGroup, ChatMessage
from .forms import ChatMessageForm
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from accounts.models import CustomUser
from django.http import Http404


class ChatView(LoginRequiredMixin, TemplateView):
    template_name = 'direct_messages/chat.html'
    context_object_name = 'chat_messages'
    form_class = ChatMessageForm

    def dispatch(self, request, *args, **kwargs):
        self.chatroom_name = kwargs.get('chatroom_name', 'public-chat')
        self.user = request.user
        return super().dispatch(request, *args, **kwargs)

    def get_chat_group(self):
        if not hasattr(self, '_chat_group'):
            self._chat_group = get_object_or_404(ChatGroup, group_name=self.chatroom_name)
        return self._chat_group

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        chat_group = self.get_chat_group()
        other_user = None
        if chat_group.is_private:
            if self.user not in chat_group.members.all():
                raise Http404()
            for member in chat_group.members.all():
                if member != self.user:
                    other_user = member
                    break

        # Сборка списка чатов пользователя для левой менюшки
        user_chats = []
        private_chats = self.user.chat_groups.filter(is_private=True)
        for group in private_chats:
            # Собеседник
            companion = None
            for member in group.members.all():
                if member != self.user:
                    companion = member
                    break
            if not companion:
                continue
            # Последнее сообщение
            last_msg = group.chat_messages.first()
            user_chats.append({
                'group_name': group.group_name,
                'avatar_url': companion.steam_avatar or 'https://media.steampowered.com/steamcommunity/public/images/avatars/fe/fef49e7fa7e1997310d705b2a6158ff8dc1cdfeb_full.jpg',
                'nickname': companion.steam_nickname,
                'slug': companion.slug,
                'last_message': last_msg.body if last_msg else '',
                'last_message_time': last_msg.created_at.strftime('%H:%M') if last_msg else '',
                'is_online': group.users_online.filter(pk=companion.pk).exists(),
            })

        if 'form' not in context:
            context['form'] = ChatMessageForm()

        context['chatroom_name'] = self.chatroom_name
        context['other_user'] = other_user
        context['chat_messages'] = chat_group.chat_messages.all()[:30][::-1]
        context['user'] = self.request.user
        context['user_chats'] = user_chats
        return context

    def post(self, request, *args, **kwargs):
        form = ChatMessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.author = request.user
            message.group = self.get_chat_group()
            message.save()
            # Возвращаем только HTML-фрагмент с новым сообщением
            context = {'message': message, 'user': request.user}
            return render(request, 'direct_messages/partials/chat_message_p.html', context)
        else:
            # Если форма невалидна, возвращаем пустой ответ, чтобы htmx ничего не делал
            return HttpResponse(status=204)




@login_required
def get_or_create_chat(request, slug_profile):
    if request.user.slug == slug_profile:
        return redirect('direct_messages:chat')
    
    other_user = CustomUser.objects.get(slug=slug_profile)
    my_chatrooms = request.user.chat_groups.filter(is_private=True)

    if my_chatrooms.exists():
        for chatroom in my_chatrooms:
            if other_user in chatroom.members.all():
                chatroom = chatroom
                break
            else:
                chatroom = ChatGroup.objects.create(is_private=True)
                chatroom.members.add(other_user, request.user)
    else:
        chatroom = ChatGroup.objects.create(is_private=True)
        chatroom.members.add(other_user, request.user)
    
    return redirect('direct_messages:chatroom', chatroom.group_name)