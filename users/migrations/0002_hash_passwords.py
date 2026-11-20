from django.contrib.auth.hashers import identify_hasher, make_password
from django.db import migrations, models


def hash_plain_passwords(apps, schema_editor):
    Register = apps.get_model('users', 'Register')
    for user in Register.objects.all():
        try:
            identify_hasher(user.password)  # already hashed
        except ValueError:
            user.password = make_password(user.password)
            user.save(update_fields=['password'])


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='register',
            name='password',
            field=models.CharField(max_length=128),
        ),
        migrations.RunPython(hash_plain_passwords, migrations.RunPython.noop),
    ]
