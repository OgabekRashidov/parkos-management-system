from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('parking', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SuperuserSecurityQuestion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question', models.CharField(max_length=300, verbose_name='Maxfiy savol')),
                ('answer_hash', models.CharField(max_length=256, verbose_name='Javob (hash)')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('last_reset_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Maxfiy savol',
                'verbose_name_plural': 'Maxfiy savollar',
            },
        ),
    ]
