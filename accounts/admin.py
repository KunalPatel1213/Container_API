from django.contrib import admin
from django import forms
from .models import Register, Login

class RegisterAdminForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, required=True)

    class Meta:
        model = Register
        fields = ['fullname', 'email', 'password']

    def save(self, commit=True):
        user = super().save(commit=False)
        # Only set password if it's changed or new
        if self.cleaned_data['password']:
            user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user

class RegisterAdmin(admin.ModelAdmin):
    form = RegisterAdminForm
    list_display = ('id', 'fullname', 'email', 'hashed_password')
    readonly_fields = ('hashed_password',)
    search_fields = ('fullname', 'email')

    def hashed_password(self, obj):
        return 'hashed_password'

admin.site.register(Register, RegisterAdmin)