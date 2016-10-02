from django.http import Http404
from django.db.models import Prefetch, Q

from rest_framework import viewsets, decorators, status, mixins
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import BaseFilterBackend
from dry_rest_permissions.generics import DRYPermissions

from sigma_core.models.user import User
from sigma_chat.models.chat_member import ChatMember
from sigma_chat.serializers.chat_member import ChatMemberSerializer
from sigma_chat.models.chat import Chat


class ChatMemberFilterBackend(BaseFilterBackend):
    filter_q = {
        'user': lambda u: Q(user=u),
        'chat': lambda g: Q(chat=c)
    }

    def filter_queryset(self, request, queryset, view):
        """
        Limits all list requests w.r.t the Normal Rules of Visibility.
        """
        user_chat_ids = request.user.user_chatmember.filter(is_member=True).values_list('chat_id', flat=True)
        # I can see a ChatMember if and only I am member of the chat
        queryset = queryset.prefetch_related(
            Prefetch('user', queryset=ChatMember.objects.filter(is_member=True))
        ).filter(Q(user_id=request.user.id) | Q(chat_id__in=user_chat_ids)
        )

        for (param, q) in self.filter_q.items():
            x = request.query_params.get(param, None)
            if x is not None:
                queryset = queryset.filter(q(x))

        return queryset.distinct()


class ChatMemberViewSet(viewsets.ModelViewSet):
    queryset = ChatMember.objects.select_related('chat', 'user')
    serializer_class = ChatMemberSerializer
    permission_classes = [IsAuthenticated, DRYPermissions]
    filter_backends = (ChatMemberFilterBackend, )

    def list(self, request):
        """
        ---
        parameters_strategy:
            query: replace
        parameters:
            - name: user
              type: integer
              paramType: query
            - name: chat
              type: integer
              paramType: query
        """
        return super().list(request)

    def create(self, request):
        serializer = ChatMemberSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if not request.user.is_admin(serializer.validated_data.get('chat')):
            return Response('You cannot add someone to a chat', status=status.HTTP_403_FORBIDDEN)

        try:
            chat = Chat.objects.get(pk=request.data.get('chat_id', None))
        except Chat.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        mem = serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
