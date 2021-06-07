# Generated by Django 2.1.9 on 2021-06-07 14:33

import uuid

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AllBanks',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('modified', models.DateTimeField(auto_now=True, null=True)),
                ('name', models.CharField(max_length=100)),
                ('acronym', models.CharField(max_length=50)),
                ('bank_code', models.CharField(max_length=50)),
            ],
            options={
                'verbose_name_plural': 'All Banks',
            },
        ),
        migrations.CreateModel(
            name='Bank',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('account_name', models.CharField(max_length=100)),
                ('account_number', models.CharField(max_length=50)),
                ('account_type', models.CharField(max_length=50)),
                ('bank', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='banks.AllBanks')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
