#!/usr/bin/env python
# -*- coding: utf-8 -*-
import urllib2
from paypal.standard.models import PayPalStandardBase
from paypal.standard.ipn.signals import *


class PayPalIPN(PayPalStandardBase):
    """Logs PayPal IPN interactions."""
    class Meta:
        db_table = "paypal_ipn"
        verbose_name = "PayPal IPN"

    def __unicode__(self):
        fmt = u"<IPN: %s %s>"
        if self.is_transaction():
            return fmt % ("Transaction", self.txn_id)
        else:
            return fmt % ("Recurring", self.recurring_payment_id)

    def _postback(self):
        """Perform PayPal Postback validation."""
        self.response = urllib2.urlopen(self.get_endpoint(), "cmd=_notify-validate&%s" % self.query).read()
    
    def _verify_postback(self):
        if self.response != "VERIFIED":
            self.set_flag("Invalid postback. (%s)" % self.response)

    def send_signals(self):
        # Transaction signals:
        if self.is_transaction():
            if self.flag:
                payment_was_flagged.send(sender=self)
            else:
                payment_was_successful.send(sender=self)
        # Subscription signals:
        else:
            if self.is_subscription_cancellation():
                subscription_cancel.send(sender=self)
            elif self.is_subscription_signup():
                subscription_signup.send(sender=self)
            elif self.is_subscription_end_of_term():
                subscription_eot.send(sender=self)
            elif self.is_subscription_modified():
                subscription_modify.send(sender=self)