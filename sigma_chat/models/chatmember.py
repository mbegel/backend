# -*- coding: utf-8 -*-
from django.db import models

from sigma_core.models.user import User

from conversation import Conversation


class ChatMember(models.Model):
    is_creator = models.BooleanField()
    is_admin = models.BooleanField()
    is_member = models.BooleanField(default=True)
    user = models.ForeignKey(User, related_name='user_chatmember')
    conversation = models.ForeignKey(Conversation, related_name='conversation_chatmember')
    
    # Related fields : 
    #     _member_message (model Message.member)

    ################################################################
    # PERMISSIONS                                                  #
    ################################################################

    @staticmethod
    def has_read_permission(request):
        return True

    def has_object_read_permission(self, request):
        # Return True if user is the one of this ChatMember or if user is admin on the related conversation
        return request.user.is_member(self.conversation)

    @staticmethod
    def has_write_permission(request):
        return True

    def has_object_write_permission(self, request):
        # Return True if user is the one of this ChatMember or if user is admin on the related conversation
        return !request.user.is_creator(self.conversation) && (request.user == self.user || request.user.is_admin(self.conversation))
