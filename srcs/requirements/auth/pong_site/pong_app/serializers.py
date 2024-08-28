from django.conf import settings
from rest_framework import generics
from django.contrib.auth.models import User
from .models import User
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework.validators import UniqueValidator
from .validators import validate_password_match

# RegisterSerializer: crée un utilisateur à partir des données d'inscription fournies.
# Il s'assure que le mot de passe est traité de manière sécurisée (hashé)
# et qu'il n'est pas visible dans les réponses.
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    first_name = serializers.CharField(required=True, allow_blank=False)
    last_name = serializers.CharField(required=True, allow_blank=False)
    profile_photo = serializers.ImageField(required=False, allow_empty_file=True)
    date_joined = serializers.DateTimeField(required=False, read_only=True, format=settings.DATETIME_FORMAT)
    last_login = serializers.DateTimeField(required=False, read_only=True, format=settings.DATETIME_FORMAT)

    class Meta:
        model = User
        fields = ('username', 'password', 'password2', 'email', 'first_name', 'last_name', 'profile_photo', 'is_active', 'date_joined', 'last_login')

    def validate(self, attrs):
        validate_password_match(attrs['password'], attrs['password2'])
        return attrs

    def create(self, validated_data):
        # Delete password2 before user creation
        validated_data.pop('password2')

        # Create user in the database
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            password=validated_data['password'],
            profile_photo=validated_data.get('profile_photo')
        )

        # Vérifiez si l'utilisateur a fourni une photo de profil, sinon utilisez une image par défaut
        if not user.profile_photo:
            user.profile_photo = 'images/default-user-profile-photo.jpg'  # Chemin relatif à MEDIA_ROOT
        user.set_password(validated_data['password'])
        user.save()
        return user

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']

class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, validators=[validate_password])
    new_password2 = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        validate_password_match(attrs['new_password'], attrs['new_password2'])
        return attrs

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise ValidationError({"old_password": "The old password is incorrect."})
        return value