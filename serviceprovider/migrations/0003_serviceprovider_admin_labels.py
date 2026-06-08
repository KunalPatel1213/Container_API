from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("serviceprovider", "0002_serviceprovider_account_type_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="serviceprovider",
            options={
                "ordering": ["name"],
                "verbose_name": "Service Provider Account",
                "verbose_name_plural": "Service Provider Accounts",
            },
        ),
    ]
