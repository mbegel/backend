# -*- coding: utf-8 -*-
from rest_framework import serializers

from sigma_chat.models.chat_member import ChatMember

class ChatMemberSerializer(serializers.ModelSerializer):
    """
    Serialize ChatMember model.
    """
    class Meta:
        model = ChatMember

    user = serializers.PrimaryKeyRelatedField(read_only=True)
    chat = serializers.PrimaryKeyRelatedField(read_only=True)
    #chatmember_message = serializers.PrimaryKeyRelatedField(read_only=True, many=True)
