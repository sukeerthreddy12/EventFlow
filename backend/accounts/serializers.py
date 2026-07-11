from django.contrib.auth import authenticate
from rest_framework import serializers

from .models import User
from .tokens import delete_verification_token, get_user_id_from_verification_token, delete_password_reset_token, get_user_id_from_password_reset_token
from .emails import send_password_reset_email



class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    role = serializers.ChoiceField(choices=[User.Role.ATTENDEE, User.Role.ORGANISER])

    class Meta:
        model = User
        fields = ["username", "email", "password", "role"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class VerifyEmailSerializer(serializers.Serializer):
    token = serializers.CharField()

    def validate_token(self, value):
        user_id = get_user_id_from_verification_token(value)
        if user_id is None:
            raise serializers.ValidationError("Invalid or expired verification token.")
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid or expired verification token.")
        if user.is_verified:
            raise serializers.ValidationError("Email is already verified.")
        self.context["user"] = user
        self.context["token"] = value
        return value

    def save(self, **kwargs):
        user = self.context["user"]
        token = self.context["token"]
        user.is_verified = True
        user.save(update_fields=["is_verified"])
        delete_verification_token(token)
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs["email"].lower()

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid email or password.")

        authenticated_user = authenticate(
            username=user.username,
            password=attrs["password"],
        )
        if authenticated_user is None:
            raise serializers.ValidationError("Invalid email or password.")

        if not authenticated_user.is_verified:
            raise serializers.ValidationError("Please verify your email before logging in.")

        attrs["user"] = authenticated_user
        return attrs

class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        return value.lower()

    def save(self, **kwargs):
        try:
            user = User.objects.get(email=self.validated_data["email"])
        except User.DoesNotExist:
            return None  # don't reveal whether email exists

        send_password_reset_email(user)
        return user
from django.contrib.auth.password_validation import validate_password

class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": "Passwords do not match."}
            )
        validate_password(attrs["new_password"])
        return attrs

    def validate_token(self, value):
        user_id = get_user_id_from_password_reset_token(value)
        if user_id is None:
            raise serializers.ValidationError("Invalid or expired reset token.")

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid or expired reset token.")

        self.context["user"] = user
        self.context["token"] = value
        return value

    def save(self, **kwargs):
        user = self.context["user"]
        token = self.context["token"]
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        delete_password_reset_token(token)
        return user

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "role", "is_verified"]
        read_only_fields = fields
