# -*- coding: utf-8 -*-
from django.db import models


class Conversation(Group):
    name = models.CharField(length=50)
    
    # Related fields : 
    #     _conversation_chatmember (model ChatMember.conversation)
    #     _conversation_message (model Message.conversation)

    ################################################################
    # PERMISSIONS                                                  #
    ################################################################

    @staticmethod
    def has_read_permission(request):
        return True

    def has_object_read_permission(self, request):
        # Return True if user is the one of this ChatMember or if user is admin on the related conversation
        return request.user.is_member(self)

    @staticmethod
    def has_write_permission(request):
        return True

    def has_object_write_permission(self, request):
        # Return True if user is the one of this ChatMember or if user is admin on the related conversation
        return request.user.is_admin(self)
        
