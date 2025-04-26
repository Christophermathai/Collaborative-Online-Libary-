from main.models import tbl_user
class EmailAuthBackend:
    def authenticate(self,request,username="none", password="none"):
        try:
            user=tbl_user.objects.get(email=username)
            if user.check_password(password):
                return user
        except tbl_user.DoesNotExist:
            return None
    def get_user(self ,UID):
        try:
            return tbl_user.objects.get(pk=UID)
        except tbl_user.DoesNotExist:
            return None