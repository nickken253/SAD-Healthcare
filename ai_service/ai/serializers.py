from rest_framework import serializers

class ChatMessageSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=1000)
    # Có thể thêm user_id nếu chatbot Flask của bạn cần
    # user_id = serializers.CharField(required=False, allow_blank=True)

class ChatResponseSerializer(serializers.Serializer):
    reply = serializers.CharField()
    # user_id = serializers.CharField(required=False, allow_blank=True)
    