# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2017-11-15 11:45
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gvsigol_core', '0006_auto_20171115_1132'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='toc_mode',
            field=models.TextField(default='toc_hidden', max_length=50),
        ),
    ]