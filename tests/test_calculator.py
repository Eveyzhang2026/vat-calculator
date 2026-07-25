"""
增值税计算器单元测试
运行：python -m unittest tests/test_calculator.py -v
或：pytest tests/test_calculator.py -v
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from calculator import VATCalculator


class TestVATCalculator(unittest.TestCase):
    def setUp(self):
        self.calc = VATCalculator()

    def test_general_basic(self):
        r = self.calc.calculate_vat('manufacturing', 1000000, input_tax=100000)
        self.assertEqual(r['vat_payable'], 30000)
        self.assertAlmostEqual(r['tax_burden_rate'], 3.0)

    def test_additional_tax(self):
        r = self.calc.calculate_vat('manufacturing', 1000000, input_tax=100000,
                                    additional_tax_rate=0.12)
        self.assertEqual(r['surcharge'], 3600)
        self.assertAlmostEqual(r['composite_tax_burden_rate'], 3.36)

    def test_small_scale_levy(self):
        r = self.calc.calculate_vat('small_scale', 500000, levy_rate=0.01)
        self.assertEqual(r['vat_payable'], 5000)
        self.assertAlmostEqual(r['tax_burden_rate'], 1.0)

    def test_small_exemption(self):
        r = self.calc.calculate_vat('small_scale', 80000, levy_rate=0.03,
                                    exemption_threshold=100000)
        self.assertEqual(r['vat_payable'], 0)
        self.assertIn('免征', r['note'])

    def test_small_no_exemption(self):
        r = self.calc.calculate_vat('small_scale', 200000, levy_rate=0.03,
                                    exemption_threshold=100000)
        self.assertEqual(r['vat_payable'], 6000)

    def test_additional_deduction_carry(self):
        # 现代服务业6%，进项10万，加计10% => 加计1万；销项6万-进项10万=-4万(留抵)
        r = self.calc.calculate_vat('modern_service', 1000000, input_tax=100000,
                                    additional_deduction_rate=0.10)
        self.assertEqual(r['additional_deduction_amount'], 0)
        self.assertEqual(r['vat_payable'], -40000)
        self.assertEqual(r['additional_deduction_carry'], 10000)

    def test_additional_deduction_applied(self):
        # 销项12万 - 进项10万 = 2万；加计1万 => 应纳税额1万
        r = self.calc.calculate_vat('modern_service', 2000000, input_tax=100000,
                                    additional_deduction_rate=0.10)
        self.assertEqual(r['additional_deduction_amount'], 10000)
        self.assertEqual(r['vat_payable'], 10000)

    def test_scenario_count(self):
        rs = self.calc.calculate_scenario_analysis('manufacturing', 1000000,
                                                   [0, 130000], step=13000)
        self.assertEqual(len(rs), 11)

    def test_compare(self):
        rs = self.calc.compare_industries(1000000, input_tax=100000)
        self.assertTrue(len(rs) >= 10)
        names = [r['industry_name'] for r in rs]
        self.assertIn('制造业', names)
        self.assertIn('小规模纳税人', names)

    def test_tax_inclusive(self):
        r = self.calc.calculate_vat('manufacturing', 1130000, input_tax=100000,
                                    is_tax_inclusive=True)
        self.assertAlmostEqual(r['sales_amount'], 1000000.0)

    def test_invalid_industry(self):
        with self.assertRaises(ValueError):
            self.calc.calculate_vat('not_exist', 1000000)


if __name__ == '__main__':
    unittest.main()
