# -*- coding: utf-8 -*-
from django.db import models

from sigma_core.models.user import User

from conversation import Conversation


class Member(models.Model):
    CREATOR = 'C'
    ADMIN = 'A'
    MEMBER = 'M'
    KICKED = 'K'
    ROLE_CHOICES = (
        (CREATOR, 'Creator'),
        (ADMIN, 'Admin'),
        (MEMBER, 'Member'),
        (KICKED, 'Kicked'),
    )
    role = models.CharField(max_length=1, choices=ROLE_CHOICES, DEFAULT=MEMBER)
    user = models.ForeignKey(User, related_name='user_member')
    conversation = models.ForeignKey(Conversation, related_name='conversation_member')
    
    # Related fields : 
    #     _member_message (model Message.member)
