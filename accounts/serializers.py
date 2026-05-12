from rest_framework import serializers
from .models import Register



class RegisterSerializer(serializers.ModelSerializer):
    fullname = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        # Replace password with 'hashed_password' in GET response
        rep['password'] = 'hashed_password'
        return rep
    def create(self, validated_data):
        password = validated_data.pop('password')
        validated_data.pop('confirm_password')
        user = Register(
            fullname=validated_data['fullname'],
            email=validated_data['email']
        )
        user.set_password(password)
        user.save()
        return user


    class Meta:
        model = Register
        fields = ['id', 'fullname', 'email', 'password', 'confirm_password']
        extra_kwargs = {
            'confirm_password': {'write_only': True},
            'fullname': {'required': True},
            'email': {'required': True},
        }


    def validate_email(self, value):
        if not value:
            raise serializers.ValidationError("Email is required.")
        if Register.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists.")
        return value


    def validate(self, data):
        if not data.get('fullname'):
            raise serializers.ValidationError({"fullname": "Full name is required."})
        if not data.get('password'):
            raise serializers.ValidationError({"password": "Password is required."})
        if not data.get('confirm_password'):
            raise serializers.ValidationError({"confirm_password": "Confirm password is required."})
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return data

    def create(self, validated_data):
        password = validated_data.pop('password')
        validated_data.pop('confirm_password')
        user = Register(
            fullname=validated_data['fullname'],
            email=validated_data['email']
        )
        user.set_password(password)
        user.save()
        return user
