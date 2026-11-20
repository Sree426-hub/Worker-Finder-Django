from django.db import models


class Register(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    # 128 chars: enough for Django's hashed passwords
    password = models.CharField(max_length=128)

    def __str__(self):
        return self.name
