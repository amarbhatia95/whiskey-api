from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets, mixins, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import Tag, Place, Whiskey

from whiskey import serializers


class BaseWhiskeyAttrViewset(viewsets.GenericViewSet,
                             mixins.ListModelMixin,
                             mixins.CreateModelMixin):
    """Base viewset for user owned whiskey attributes"""
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        """Return objects for the current authenticated user only"""
        assigned_only = bool(
            int(self.request.query_params.get('assigned_only', 0))
        )
        queryset = self.queryset
        if assigned_only:
            queryset = queryset.filter(whiskey__isnull=False)

        return queryset.filter(
            user=self.request.user
        ).order_by('-name').distinct()

    def perform_create(self, serializer):
        """Create a new object"""
        return serializer.save(user=self.request.user)


class TagViewSet(BaseWhiskeyAttrViewset):
    """Manage tags in the database"""
    queryset = Tag.objects.all()
    serializer_class = serializers.TagSerializer


class PlaceViewSet(BaseWhiskeyAttrViewset):
    """Manage places in the database"""
    queryset = Place.objects.all()
    serializer_class = serializers.PlaceSerializer


class WhiskeyViewSet(viewsets.ModelViewSet):
    """Manage Whiskeys in database"""
    serializer_class = serializers.WhiskeySerializer
    queryset = Whiskey.objects.all()
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def _params_to_ints(self, qs):
        '''convert a list of string ids to a list of integers'''
        return [int(str_id) for str_id in qs.split(',')]

    def get_queryset(self):
        """Retrieve the Whiskeys for the authenticated user"""
        tags = self.request.query_params.get('tags')
        places = self.request.query_params.get('places')
        queryset = self.queryset
        if tags:
            tag_ids = self._params_to_ints(tags)
            queryset = queryset.filter(tags__id__in=tag_ids)
        if places:
            places_id = self._params_to_ints(places)
            queryset = queryset.filter(places__id__in=places_id)

        return queryset.filter(user=self.request.user)

    def get_serializer_class(self):
        """Return appropiate serializer class"""
        if self.action == 'retrieve':
            return serializers.WhiskeyDetailSerializer
        elif self.action == 'upload_image':
            return serializers.WhiskeyImageSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        """Create a new whiskey"""
        serializer.save(user=self.request.user)

    @action(methods=['POST'], detail=True, url_path='upload-image')
    def upload_image(self, request, pk=None):
        """Upload an image to a whiskey"""
        whiskey = self.get_object()
        serializer = self.get_serializer(
            whiskey,
            data=request.data
        )

        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
