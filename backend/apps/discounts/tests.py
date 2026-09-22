from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from .models import VolumeDiscountRule


class VolumeDiscountRuleTests(TestCase):
    def test_percentage_over_100_is_invalid(self):
        rule = VolumeDiscountRule(name="Malo", min_quantity=2, percentage=Decimal("150"))
        with self.assertRaises(ValidationError):
            rule.full_clean()

    def test_min_quantity_below_one_is_invalid(self):
        rule = VolumeDiscountRule(name="Malo", min_quantity=0, percentage=Decimal("10"))
        with self.assertRaises(ValidationError):
            rule.full_clean()

    def test_best_for_quantity_picks_highest_applicable_percentage(self):
        VolumeDiscountRule.objects.create(name="3+", min_quantity=3, percentage=Decimal("5"))
        r5 = VolumeDiscountRule.objects.create(
            name="5+", min_quantity=5, percentage=Decimal("12")
        )
        # Regla inactiva no debe elegirse aunque tenga mejor %.
        VolumeDiscountRule.objects.create(
            name="10+", min_quantity=10, percentage=Decimal("20"), is_active=False
        )

        self.assertIsNone(VolumeDiscountRule.best_for_quantity(2))
        self.assertEqual(VolumeDiscountRule.best_for_quantity(3).percentage, Decimal("5"))
        self.assertEqual(VolumeDiscountRule.best_for_quantity(6), r5)
        # A 10 unidades, la de 20% está inactiva → gana la de 5+ (12%).
        self.assertEqual(VolumeDiscountRule.best_for_quantity(10), r5)
