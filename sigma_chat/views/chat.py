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


class ChatFilterBackend(DRYPermissionFiltersBase):
    def filter_queryset(self, request, queryset, view):
        """
        Limits all list requests w.r.t the Normal Rules of Visibility.
        """
        user_chats_ids = request.user.user_chatmember.filter(is_member=True).values_list('chat_id', flat=True)
        return queryset.prefetch_related('chatmember') \
            .filter(chatmember__user=request.user) \
            .distinct()


class ChatViewSet(viewsets.ModelViewSet):
    queryset = Chat.objects.all()
    serializer_class = ChatSerializer
    permission_classes = [IsAuthenticated, ]
    filter_backends = (ChatFilterBackend, )

    def update(self, request, pk=None):
        try:
            chat = Chat.objects.get(pk=pk)
        except Chat.DoesNotExist:
            raise Http404("Chat %d not found" % pk)

        if not request.user.is_admin(chat):
            return Response(status=status.HTTP_403_FORBIDDEN)
        return super(ChatViewSet, self).update(request, pk)

    def create(self, request):
        data = request.data
        data['user'] = request.user.id
        serializer = self.serializer_class(data=data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @decorators.detail_route(methods=['put'])
    def add_member(self, request, pk=None):
        """
        Add an user in chat pk.
        ---
        omit_serializer: true
        parameters_strategy:
            form: replace
        parameters:
            - name: user_id
              type: integer
              required: true
        """
        try:
            chat = Chat.objects.get(pk=pk)
            user = User.objects.get(pk=request.data.get('user_id', None))
            if not request.user.is_admin(chat):
                return Response(status=status.HTTP_403_FORBIDDEN)

            # Already chat member ?
            try:
                ChatMember.objects.get(user=user.id, chat=chat.id)
                return Response("Already Chat member", status=status.HTTP_400_BAD_REQUEST)
            except ChatMember.DoesNotExist:
                pass

            ChatMember.create(chat=chat, user=user, role="M")
            s = ChatSerializer(chat)
            return Response(s.data, status=status.HTTP_200_OK)

        except Chat.DoesNotExist:
            raise Http404("Chat %d not found" % pk)
        except User.DoesNotExist:
            raise Http404("User %d not found" % request.data.get('user_id', None))
