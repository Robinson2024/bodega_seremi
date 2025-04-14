from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from accounts.models import clean_rut

class RutBackend(ModelBackend):
    def authenticate(self, request, rut=None, password=None, **kwargs):
        UserModel = get_user_model()
        if rut is None:
            return None
        try:
            cleaned_rut = clean_rut(rut)
            user = UserModel.objects.get(rut=cleaned_rut)
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        except UserModel.DoesNotExist:
            return None

    def get_user(self, user_id):
        UserModel = get_user_model()
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None