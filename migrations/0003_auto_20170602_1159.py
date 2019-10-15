# -*- coding: utf-8 -*-

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('datatracker', '0002_auto_20170602_1005'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='group',
            field=models.CharField(default=None, max_length=64, null=True, blank=True),
            preserve_default=True,
        ),
    ]
