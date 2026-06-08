from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0005_register_uses_auth_user"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="register",
            options={
                "ordering": ["fullname"],
                "verbose_name": "User Account",
                "verbose_name_plural": "User Accounts",
            },
        ),
    ]
