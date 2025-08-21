from django.db import models


class Publication(models.Model):
    file_url = models.URLField(max_length=255, unique=True)
    # Competence no formato 'YYYY-MM'
    competence = models.CharField(max_length=7, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.competence} - {self.file_url}"

    class Meta:
        ordering = ["-created_at"]
