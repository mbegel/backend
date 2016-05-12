import os.path

from django.db import models

from sigma_core.models.user import User
from sigma_core.models.group import Group


def img_path(instance, filename):
    from django.utils.crypto import get_random_string
    extension = os.path.splitext(filename)[1]
    return "img/" + get_random_string(length=150, allowed_chars='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_') + extension


class Image(models.Model):
    file = models.ImageField(max_length=255, upload_to=img_path)
    owner = models.ForeignKey(User)
    added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.__str__()

    def delete(self, *args, **kwargs):
        self.file.delete(save=False)
        return super(Image, self).delete(*args, **kwargs)
