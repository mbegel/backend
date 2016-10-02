from django.http import Http404
from django.db.models import Q

from rest_framework import viewsets, decorators, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from dry_rest_permissions.generics import DRYPermissionFiltersBase

from sigma_core.models.user import User
from sigma_chat.models.chat import Chat
from sigma_chat.models.chat_member import ChatMember
from sigma_chat.serializers.chat import ChatSerializer
from sigma_chat.models.message import Message
from sigma_chat.serializers.message import MessageSerializer


class MessageFilterBackend(DRYPermissionFiltersBase):
    def filter_queryset(self, request, queryset, view):
        """
        Limits all list requests w.r.t the Normal Rules of Visibility.
        """
        user_chats_ids = request.user.user_chatmember.filter(is_member=True).values_list('chat_id', flat=True)
        return queryset.prefetch_related('chat') \
            .filter(chatmember__user=request.user) \
            .distinct()


class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated, ]
    filter_backends = (MessageFilterBackend, )
