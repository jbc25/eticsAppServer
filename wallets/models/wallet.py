# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import uuid

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class Wallet(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User)
    balance = models.FloatField(default=0, verbose_name='Saldo actual')
    last_transaction = models.DateTimeField(blank=True, null=True, verbose_name='Última transacción')

    class Meta:
        verbose_name = 'Monedero'
        verbose_name_plural = 'Monederos'
        ordering = ['user']

    def __unicode__(self):
        return self.user.username + ': ' + str(self.balance)

    def new_transaction(self, amount, wallet=None, concept=None, bonification=False, **kwargs):

        if wallet:
            wallet_from = self
            wallet_to = wallet
        else:
            wallet_from = None
            wallet_to = self

        if not concept:
            if bonification:
                concept = "Bonificación en boniatos por compra"
            elif wallet_from:
                concept = "Transferencia"

        from wallets.models.transaction import STATUS_PENDING, Transaction

        return Transaction.objects.create(wallet_from=wallet_from, wallet_to=wallet_to,
                                          status=STATUS_PENDING, **kwargs)


# Method to create the wallet for every new user
@receiver(post_save, sender=User)
def create_user_wallet(sender, instance, created, **kwargs):
    if created:
        print 'Creating user wallet!'
        Wallet.objects.create(user=instance)

