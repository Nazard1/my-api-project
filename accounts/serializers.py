from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework.validators import UniqueValidator


class RegisterSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        max_length=30,
        validators=[
            UnicodeUsernameValidator(),
            UniqueValidator(
                queryset=User.objects.all(),
                message="Користувач із таким імʼям уже існує.",
            ),
        ],
    )
    first_name = serializers.CharField(max_length=30, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=30, required=False, allow_blank=True)
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        max_length=128,
        style={"input_type": "password"},
    )
    password2 = serializers.CharField(
        write_only=True, max_length=128, style={"input_type": "password"}
    )

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "password",
            "password2",
        ]

    def validate(self, attrs):
        errors = {}

        if attrs["password"] != attrs["password2"]:
            errors["password2"] = ["Паролі не збігаються."]

        # Тимчасовий (незбережений) користувач потрібен, щоб валідатор
        # міг перевірити схожість пароля на імʼя, email тощо.
        user = User(
            username=attrs["username"],
            first_name=attrs.get("first_name", ""),
            last_name=attrs.get("last_name", ""),
            email=attrs["email"],
        )
        try:
            validate_password(attrs["password"], user)
        except DjangoValidationError as exc:
            errors["password"] = list(exc.messages)

        if errors:
            raise serializers.ValidationError(errors)
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2")
        return User.objects.create_user(**validated_data)
