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
            if not request.user.is_chat_admin(chat):
                return Response(status=status.HTTP_403_FORBIDDEN)

            # Already chat member ?
            try:
                ChatMember.objects.get(user=user.id, chat=chat.id)
                return Response("Already Chat member", status=status.HTTP_400_BAD_REQUEST)
            except ChatMember.DoesNotExist:
                pass

            ChatMember.create(chat=chat, user=user, is_creator=False, is_admin=False)
            s = ChatSerializer(chat)
            return Response(s.data, status=status.HTTP_200_OK)

        except Chat.DoesNotExist:
            raise Http404("Chat %d not found" % pk)
        except User.DoesNotExist:
            raise Http404("User %d not found" % request.data.get('user_id', None))

    @decorators.detail_route(methods=['put'])
    def change_role(self, request, pk=None):
        """
        Change the permissions of user in chat pk.
        ---
        omit_serializer: true
        parameters_strategy:
            form: replace
        parameters:
            - name: chatmember_id
              type: integer
              required: true
            - name: role
              type: string
              required: true
        """
        try:
            chat = Chat.objects.get(pk=pk)
            chatmember = ChatMember.objects.get(pk=request.data.get('chatmember_id', None))
            """
                - cannot change the role of the creator
                - if has quit the conversation, can rejoin, but administrator cannot force it
                - if not admin, only can REjoin conversation if not banned
            """
            has_ragequit = request.user == chatmember.user and not (chatmember.is_member or chatmember.is_banned)
            if chatmember.is_creator or (not has_ragequit) or ((not request.user.is_chat_admin(chat)) and not (chatmember.is_member or chatmember.is_banned)) :
                return Response(status=status.HTTP_403_FORBIDDEN)

            role = request.data.get('role', None)
            if(role == "admin" and not has_ragequit):
                chatmember.is_admin = True
                chatmember.is_member = True
                chatmember.is_banned = False
                chatmember.save()
                s = ChatMemberSerializer(chatmember)
                return Response(s.data, status=status.HTTP_200_OK)
            if(role == "member"):
                chatmember.is_admin = False
                chatmember.is_member = True
                chatmember.is_banned = False
                chatmember.save()
                s = ChatMemberSerializer(chatmember)
                return Response(s.data, status=status.HTTP_200_OK)
            if(role == "banned" and not has_ragequit):
                chatmember.is_admin = False
                chatmember.is_member = False
                chatmember.is_banned = True
                chatmember.save()
                s = ChatMemberSerializer(chatmember)
                return Response(s.data, status=status.HTTP_200_OK)
            return Response("Incorrect role.", status=status.HTTP_400_BAD_REQUEST)

        except Chat.DoesNotExist:
            raise Http404("Chat %d not found" % pk)
        except ChatMember.DoesNotExist:
            raise Http404("ChatMember %d not found" % request.data.get('chatmember_id', None))
