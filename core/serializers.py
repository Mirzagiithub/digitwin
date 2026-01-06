from rest_framework import serializers
from django.contrib.auth import authenticate, password_validation
from django.core.validators import validate_email
from django.utils import timezone
from .models import Organization, CustomUser
import re


# ============================
# ORGANIZATION
# ============================
class OrganizationSerializer(serializers.ModelSerializer):
    user_count = serializers.IntegerField(read_only=True)
    asset_count = serializers.IntegerField(read_only=True)
    is_subscription_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = Organization
        fields = [
            'id', 'name', 'domain', 'slug', 'subscription_tier',
            'subscription_start', 'subscription_end', 'asset_limit',
            'user_limit', 'is_active', 'is_trial', 'contact_email',
            'contact_phone', 'address', 'timezone', 'currency',
            'language', 'user_count', 'asset_count',
            'is_subscription_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']

    def validate_domain(self, value):
        # Accept real domains like example.com, my-org.co.in
        pattern = r'^(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}$'
        if not re.match(pattern, value):
            raise serializers.ValidationError('Invalid domain name')
        return value.lower()

    def create(self, validated_data):
        validated_data['slug'] = validated_data['domain'].replace('.', '-')
        return super().create(validated_data)


# ============================
# USER
# ============================
class UserSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(
        source='organization.name', read_only=True
    )
    full_name = serializers.CharField(read_only=True)
    is_org_admin = serializers.BooleanField(read_only=True)

    password = serializers.CharField(
        write_only=True,
        required=False,
        style={'input_type': 'password'}
    )

    class Meta:
        model = CustomUser
        fields = [
            'id', 'email', 'password',
            'first_name', 'last_name', 'full_name',
            'organization', 'organization_name', 'role',
            'phone', 'department', 'job_title', 'profile_picture',
            'is_active', 'email_verified', 'phone_verified',
            'two_factor_enabled', 'is_org_admin',
            'notifications_enabled', 'email_notifications',
            'push_notifications', 'language',
            'last_login', 'date_joined', 'last_activity', 'login_count'
        ]
        read_only_fields = [
            'id', 'last_login', 'date_joined',
            'last_activity', 'login_count',
            'email_verified', 'phone_verified'
        ]

    def validate_email(self, value):
        validate_email(value)
        organization = self.context.get('organization')

        qs = CustomUser.objects.filter(email=value.lower())
        if organization:
            qs = qs.filter(organization=organization)

        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise serializers.ValidationError('Email already exists')

        return value.lower()

    def create(self, validated_data):
        organization = self.context.get('organization')
        password = validated_data.pop('password', None)

        if organization:
            validated_data['organization'] = organization

        user = CustomUser.objects.create_user(**validated_data)

        if password:
            password_validation.validate_password(password, user)
            user.set_password(password)
            user.save(update_fields=['password'])

        return user


# ============================
# LOGIN
# ============================
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True, style={'input_type': 'password'}
    )
    organization = serializers.CharField(required=False)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')
        org_slug = data.get('organization')

        user = authenticate(email=email, password=password)
        if not user:
            raise serializers.ValidationError('Invalid credentials')

        if not user.is_active:
            raise serializers.ValidationError('User account is disabled')

        if org_slug:
            if not user.organization or user.organization.slug != org_slug:
                raise serializers.ValidationError(
                    'User not found in this organization'
                )

        data['user'] = user
        return data


# ============================
# PASSWORD CHANGE
# ============================
class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField()
    confirm_password = serializers.CharField()

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError(
                {'confirm_password': 'Passwords do not match'}
            )

        password_validation.validate_password(data['new_password'])
        return data


# ============================
# PROFILE UPDATE
# ============================
class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 'phone',
            'department', 'job_title', 'profile_picture',
            'language', 'notifications_enabled',
            'email_notifications', 'push_notifications'
        ]
