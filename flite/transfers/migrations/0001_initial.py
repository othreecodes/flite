# Generated by Django 2.1.9 on 2021-06-07 20:01

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('banks', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('modified', models.DateTimeField(auto_now=True, null=True)),
                ('reference', models.CharField(max_length=200)),
                ('status', models.CharField(help_text='was this transaction successful, pending or failed', max_length=200)),
                ('amount', models.FloatField(default=0.0)),
                ('new_balance', models.FloatField(default=0.0)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='BankTransfer',
            fields=[
                ('transaction_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='transfers.Transaction')),
                ('bank', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='banks.Bank')),
            ],
            options={
                'verbose_name_plural': 'Bank Transfers',
            },
            bases=('transfers.transaction',),
        ),
        migrations.CreateModel(
            name='P2PTransfer',
            fields=[
                ('transaction_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='transfers.Transaction')),
                ('recipient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recipient', to=settings.AUTH_USER_MODEL)),
                ('sender', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sender', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'P2P Transfers',
            },
            bases=('transfers.transaction',),
        ),
        migrations.AddField(
            model_name='transaction',
            name='owner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transaction', to=settings.AUTH_USER_MODEL),
        ),
    ]
