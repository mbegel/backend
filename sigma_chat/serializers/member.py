from rest_framework import serializers

from sigma_chat.models.chatmember import ChatMember

class ChatMemberSerializer(serializers.ModelSerializer):
    """
    Serialize ChatMember model.
    """
    class Meta:
        model = ChatMember
