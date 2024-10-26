"""
Views for the recipe APIs.
"""

from drf_spectacular.utils import (
    extend_schema_view,
    extend_schema,
    OpenApiParameter,
    OpenApiTypes

)

from rest_framework import (
    viewsets,
    mixins,
    status,
filters,
generics,
)

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count
from core.models import (
    Recipe,
    Tag,
    Ingredient,
Liked,
)

from recipe import serializers


class UserDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = serializers.UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


@extend_schema_view(
    list = extend_schema(
        parameters=[
            OpenApiParameter(
                'tags',
                OpenApiTypes.STR,
                description = 'Comma separated list of IDs to filter',
            ),
            OpenApiParameter(
                'ingredients',
                OpenApiTypes.STR,
                description = 'Comma separated list of IDs to filter',
            )
        ]
    )
)
class RecipeViewSet(viewsets.ModelViewSet):

    """View for manage recipe APIs."""
    serializer_class = serializers.RecipeDetailSerializer
    queryset = Recipe.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    search_fields = ['title']   #added 17/10/2024
    filter_backends = (filters.SearchFilter,) #added 17/10/2024


    def _params_to_ints(self, qs):
        """Convert a list of strings to integers."""
        """1, 2, 3"""
        return [int(str_id) for str_id in qs.split(',')]


    def get_queryset(self):
        """Retrieve recipes for authenticated user."""

        tags = self.request.query_params.get('tags')
        ingredients = self.request.query_params.get('ingredients')
        queryset = self.queryset

        if tags:
            tags_ids = self._params_to_ints(tags)
            for tag_id in tags_ids:
                queryset = queryset.filter(tags__id=tag_id)

        if ingredients:
            ingredients_id = self._params_to_ints(ingredients)
            for ingredient_id in ingredients_id:
                queryset = queryset.filter(ingredients__id=ingredient_id)

        return queryset.order_by('-id').distinct()

    def get_serializer_class(self):
        """Return the serializer class for request."""

        if self.action == 'list':
            return serializers.RecipeSerializer

        elif self.action == 'upload_image':
            return serializers.RecipeImageSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        """Create a new recipe."""
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        if serializer.instance.user != self.request.user:
            return Response({'detail': 'Not authorised to update this recipe.'}, status=status.HTTP_403_FORBIDDEN)
        serializer.save()

    def perform_destroy(self, instance):
        if instance.user != self.request.user:
            return Response({'detail': 'Not authorised to update this recipe.'}, status=status.HTTP_403_FORBIDDEN)
        instance.delete()
    @action(detail=False, methods=['get'], url_path='user-recipes')
    def user_recipes(self, request):

        user = request.user
        queryset = self.queryset.filter(user=user)

        search_query = request.query_params.get('search')
        tags = request.query_params.get('tags')
        ingredients = request.query_params.get('ingredients')

        if search_query:
            queryset = queryset.filter(title__icontains=search_query)

        if tags:
            queryset = queryset.filter(tags__id__in=tags.split(','))

        if ingredients:
            queryset = queryset.filter(ingredients__id__in=ingredients.split(','))


        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='liked-recipes')
    def liked_recipes(self, request):
        user = request.user
        liked_recipe_ids = Liked.objects.filter(user=user).values_list('liked_recipe__id', flat=True)
        queryset = self.queryset.filter(id__in=liked_recipe_ids)

        search_query = request.query_params.get('search')
        tags = request.query_params.get('tags')
        ingredients = request.query_params.get('ingredients')

        if search_query:
            queryset = queryset.filter(title__icontains=search_query)

        if tags:
            queryset = queryset.filter(tags__id__in=tags.split(','))

        if ingredients:
            queryset = queryset.filter(ingredients__id__in=ingredients.split(','))


        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='all-recipes')
    def all_recipes(self, request):
        all_recipes=self.queryset.order_by('id')
        serializer = self.get_serializer(all_recipes, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], serializer_class=serializers.LikeSerializer)
    def like_recipe(self, request, pk=None):
        recipe = self.get_object()
        user = request.user

        if Liked.objects.filter(user=user, liked_recipe=recipe).exists():
            Liked.objects.filter(user=user, liked_recipe=recipe).delete()
            return Response({'status': 'unliked'}, status=status.HTTP_200_OK)
        else:
            Liked.objects.create(user=user, liked_recipe=recipe)
            return Response({'status': 'liked'}, status=status.HTTP_201_CREATED)


    @action(methods=['POST'], detail=True, url_path='upload-image')
    def upload_image(self, request, pk=None):
        """Upload an image to recipe."""

        recipe = self.get_object()
        serializer = self.get_serializer(recipe, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    list = extend_schema(
        parameters=[
            OpenApiParameter(
                'assigned_only',
                OpenApiTypes.INT, enum =  [0,1],
                description = 'Filter by items assigned to recipes.'
            )
        ]
    )
)
class BaseRecipeAttrViewSet(mixins.DestroyModelMixin,
                            mixins.UpdateModelMixin,
                            mixins.ListModelMixin,
                            viewsets.GenericViewSet):
    """Base ViewSet for recipe attributes."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter queryset to authenticated user."""

        assigned_only = bool(
            int(self.request.query_params.get('assigned_only', 0))
        )
        queryset = self.queryset

        if assigned_only:
            queryet = queryset.filter(recipe__isnull = False)

        return queryset.filter(
            user=self.request.user
            ).order_by('-name').distinct()


class TagViewSet(BaseRecipeAttrViewSet):
    """Manage tags in the database."""

    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()





class IngredientViewSet(BaseRecipeAttrViewSet):
    """Manage ingredients in the database."""

    serializer_class = serializers.IngredientSerializer
    queryset = Ingredient.objects.all()


