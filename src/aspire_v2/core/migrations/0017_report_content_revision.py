from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0016_alter_analysisresult_options"),
    ]

    operations = [
        migrations.AddField(
            model_name="report",
            name="content_revision",
            field=models.PositiveIntegerField(default=0),
        ),
    ]
