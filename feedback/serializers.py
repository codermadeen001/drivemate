# serializers.py
"""from rest_framework import serializers
from .models import Feedback

class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        #fields = '__all__'
        fields = ['feedback_id', 'car_id', 'rental_id', 'comment', 'feedback_date']




"""



# serializers.py
from rest_framework import serializers
from .models import Feedback
from django.contrib.auth import get_user_model

User = get_user_model()

class FeedbackSerializer(serializers.ModelSerializer):
    first_name = serializers.SerializerMethodField()
    profile_picture = serializers.SerializerMethodField()

    class Meta:
        model = Feedback
        fields = [
            'feedback_id', 'car_id', 'rental_id', 'comment', 'feedback_date',
            'first_name', 'profile_picture'
        ]

    def get_first_name(self, obj):
        return obj.user.first_name if obj.user else None

    def get_profile_picture(self, obj):
        return obj.user.profile_picture if obj.user and obj.user.profile_picture else None
