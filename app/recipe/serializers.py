"""
Serializers for recipe APIs.
"""
from rest_framework import serializers
from core.models import (
    Recipe,
    Tag,
    Ingredient,
)
import requests
from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ['id', 'email', 'name']
        read_only_fields = ['id']

class IngredientSerializer(serializers.ModelSerializer):
    """Serializer for ingredients."""

    class Meta:
        model = Ingredient
        fields = ['id', 'name']
        read_only_fields = ['id']

class TagSerializer(serializers.ModelSerializer):
    """Serializer for tags."""

    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields = ['id']

class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for recipes."""

    user = UserSerializer(read_only=True)
    tags = TagSerializer(many=True, required=False)
    ingredients = IngredientSerializer(many=True, required=False)

    class Meta:
        model = Recipe
        fields = ['id', 'title', 'time_minutes', 'price', 'link', 'tags', 'ingredients', 'image', 'user']
        read_only_fields = ['id']

    def _get_or_create_tags(self, tags, recipe):
        """Handle getting or creating tags as needed."""
        auth_user = self.context['request'].user
        for tag in tags:
            tag_obj, created = Tag.objects.get_or_create(
                user = auth_user,
                **tag
            )
            recipe.tags.add(tag_obj)


    def _get_or_create_ingredients(self, ingredients, recipe):
        """Handle getting or creating ingredients as needed."""
        auth_user = self.context['request'].user

        for ingredient in ingredients:
            ingredient_obj, created = Ingredient.objects.get_or_create(
                user = auth_user,
                **ingredient,
            )
            recipe.ingredients.add(ingredient_obj)

    def create(self, validated_data):
        """Create a recipe."""
        tags = validated_data.pop('tags', [])
        ingredients = validated_data.pop('ingredients', [])
        recipe = Recipe.objects.create(**validated_data)
        self._get_or_create_tags(tags, recipe)
        self._get_or_create_ingredients(ingredients, recipe)

        return recipe

    def update(self, instance, validated_data):
        """Update recipe."""

        tags = validated_data.pop('tags', None)
        ingredients = validated_data.pop('ingredients', None)

        if tags is not None:
            instance.tags.clear()
            self._get_or_create_tags(tags, instance)

        if ingredients is not None:
            instance.ingredients.clear()
            self._get_or_create_ingredients(ingredients, instance)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')

        if instance.image and request:
            image_url = request.build_absolute_uri(instance.image.url)
            if request.is_secure():
                representation['image'] = image_url.replace("http://", "https://")
            else:
                representation['image'] = image_url

        return representation

class RecipeDetailSerializer(RecipeSerializer):
    """Serializer for recipe detail view."""

    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ['description', 'image']


class RecipeImageSerializer(serializers.ModelSerializer):
    """Serializer for uploading images to recipes."""
    image_url = serializers.URLField(write_only=True, required=False)
    class Meta:
        model = Recipe
        fields = ['id', 'image', 'image_url']
        read_only_fields = ['id']
        # extra_kwargs = {'image': {'required' : 'True'}}

    def validate(self, attrs):
        if not attrs.get('image') and not attrs.get('image_url'):
            raise serializers.ValidationError('Either image or image_url must be provided!')
        return attrs

    def save(self, **kwargs):
        image_url = self.validated_data.get('image_url', None)

        if image_url:
            response = requests.get(image_url)
            response.raise_for_status()
            image_name = image_url.split("/")[-1]
            image_file = ContentFile(response.content, name=image_name)
            self.validated_data['image'] = image_file

        return super().save(**kwargs)