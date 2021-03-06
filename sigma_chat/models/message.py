# -*- coding: utf-8 -*-
from django.db import models

from chat_member import ChatMember
from chat import Chat


class Message(models.Model):
    text = models.TextField()
    chatmember = models.ForeignKey(ChatMember, related_name='chatmember_message')
    chat = models.ForeignKey(Chat, related_name='chat_message')
    date = models.DateTimeField(auto_now=True)
    attachment = models.FileField(upload_to=chat_directory_path)

    def chat_directory_path(self, filename):
        # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
        return 'uploads/chats/{0}/{1}'.format(self.chat.id, filename)

    ################################################################
    # PERMISSIONS                                                  #
    ################################################################

    @staticmethod
    def has_read_permission(request):
        return True

    def has_object_read_permission(self, request):
        return request.user.is_member(self.chat)

    @staticmethod
    def has_write_permission(request):
        return True

    def has_object_write_permission(self, request):
        return request.user == self.chatmember.user
