from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


def migrate_register_rows_to_auth_users(apps, schema_editor):
    register_model = apps.get_model("accounts", "Register")
    user_app_label, user_model_name = settings.AUTH_USER_MODEL.split(".")
    user_model = apps.get_model(user_app_label, user_model_name)

    for profile in register_model.objects.all():
        email = profile.email.lower()
        user = user_model.objects.filter(username__iexact=email).first()

        if user is None:
            user = user_model(
                username=email,
                email=email,
                first_name=profile.fullname,
                is_active=True,
                password=profile.password or make_password(None),
            )
            user.save()
        else:
            user.email = email
            user.first_name = profile.fullname
            if profile.password and not user.password:
                user.password = profile.password
            user.save(update_fields=["email", "first_name", "password"])

        profile.user_id = user.pk
        profile.email = email
        profile.save(update_fields=["user", "email"])


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("accounts", "0004_register_company"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="register",
            options={"ordering": ["fullname"]},
        ),
        migrations.AddField(
            model_name="register",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="register",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name="register",
            name="user",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="profile",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.RunPython(migrate_register_rows_to_auth_users, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="register",
            name="user",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="profile",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.RemoveField(
            model_name="register",
            name="password",
        ),
        migrations.DeleteModel(
            name="Login",
        ),
    ]
