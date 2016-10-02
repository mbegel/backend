# -*- coding: utf-8 -*-
from rest_framework import serializers

from sigma_chat.models.chatmember import ChatMember

class ChatMemberSerializer(serializers.ModelSerializer):
    """
    Serialize ChatMember model.
    """
    class Meta:
        model = ChatMember

    user = PrimaryKeyRelatedField(read_only=True)
    conversation = PrimaryKeyRelatedField(read_only=True)
    message_set = PrimaryKeyRelatedField(read_only=True, many=True)
