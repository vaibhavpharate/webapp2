# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class VClientDataReport(models.Model):
    site_name = models.TextField(blank=True, null=True)
    site_status = models.CharField(max_length=200, blank=True, null=True)
    client_name = models.CharField(max_length=200, blank=True, null=True)
    state = models.TextField(blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    capacity = models.FloatField(blank=True, null=True)
    source = models.TextField(blank=True, null=True)
    data_type = models.TextField(blank=True, null=True)
    min_date = models.DateTimeField(blank=True, null=True)
    max_date = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'v_client_data_report'
