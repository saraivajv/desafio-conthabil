from rest_framework import viewsets

from .models import Publication
from .serializers import PublicationSerializer


class PublicationViewSet(viewsets.ModelViewSet):
    queryset = Publication.objects.all()
    serializer_class = PublicationSerializer
    # Habilita a filtragem pelo campo 'competence'
    # Ex: /api/publications/?competence=2025-07
    filterset_fields = ["competence"]
