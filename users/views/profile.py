# views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from users.models.profile import Profile
from users.serializers.profile import ProfileSerializer
from rest_framework.permissions import IsAuthenticated
import cloudinary.uploader

class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the profile
        return obj.user == request.user

class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    
    def create(self, request, *args, **kwargs):
        """Create a new profile for the authenticated user"""
        # Check if user already has a profile
        if hasattr(request.user, 'profile'):
            return Response(
                {'error': 'User already has a profile'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Add the authenticated user to the profile data
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_queryset(self):
        queryset = Profile.objects.all()
        username = self.request.query_params.get('username', None)
        if username is not None:
            queryset = queryset.filter(user__username=username)
        return queryset

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Endpoint to get the current user's profile"""
        try:
            profile = request.user.profile
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        except Profile.DoesNotExist:
            return Response(
                {'error': 'Profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            # Add more detailed error logging
            print(f"Unexpected error in me endpoint: {str(e)}")
            return Response(
                {'error': f'An unexpected error occurred: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


    @action(detail=True, methods=['post'])
    def upload_picture(self, request):
        try:
            # Retrieve the user's profile
            profile = request.user.profile
        except Profile.DoesNotExist:
            return Response(
                {'error': 'Profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if image is provided
        if 'profile_pic' not in request.FILES:
            return Response(
                {'error': 'No image provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        image_file = request.FILES['profile_pic']
        
        # Validate file
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif']
        if image_file.content_type not in allowed_types:
            return Response(
                {'error': 'Invalid file type'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Upload to Cloudinary
            upload_result = cloudinary.uploader.upload(
                image_file,
                folder=f'profile_pics/{request.user.username}/',
                public_id=f'{request.user.username}_profile',
                overwrite=True,
                # Optional transformations
                transformation=[
                    {'width': 400, 'height': 400, 'crop': 'fill'},
                    {'quality': 'auto'},
                ]
            )
            
            # Update profile with Cloudinary URL
            print(upload_result['secure_url'])
            profile.profile_pic = upload_result['secure_url']
            profile.save()
            
            return Response({
                'message': 'Profile picture uploaded successfully',
                'profile_pic_url': upload_result['secure_url']
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response(
                {'error': f'Upload failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        