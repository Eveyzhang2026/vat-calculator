"""
增值税税负动态测算 - 核心计算模块
根据《税法》规定实现增值税计算逻辑
"""

import json
import os
from datetime import datetime


class VATCalculator:
    """增值税计算器"""
    
    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(__file__), 'data')
        self.industry_rates = self._load_industry_rates()
    
    def _load_industry_rates(self):
        """加载行业税率配置"""
        rates_file = os.path.join(self.data_dir, 'industry_rates.json')
        try:
            with open(rates_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise Exception("行业税率配置文件不存在")
    
    def get_industries(self):
        """获取所有行业列表"""
        return self.industry_rates.get('industries', [])
    
    def get_industry_by_id(self, industry_id):
        """根据ID获取行业信息"""
        for industry in self.get_industries():
            if industry['id'] == industry_id:
                return industry
        return None
    
    def calculate_vat(self, industry_id, sales_amount, input_tax=0, 
                     other_deductions=0, is_tax_inclusive=False,
                     levy_rate=None, additional_tax_rate=0.12,
                     additional_deduction_rate=0.0, exemption_threshold=100000):
        """
        计算增值税（含加计抵减、免税起征点、附加税费与综合税负率）
        
        参数:
            industry_id: 行业ID
            sales_amount: 销售额（元）
            input_tax: 进项税额（元）
            other_deductions: 其他可抵扣税额（元）
            is_tax_inclusive: 销售额是否含税（默认不含税）
            levy_rate: 小规模纳税人征收率（可选，覆盖默认 output_rate）
            additional_tax_rate: 附加税费合计率（城建+教育费+地方教育费，默认12%）
            additional_deduction_rate: 加计抵减率（如10%/15%，仅一般纳税人适用）
            exemption_threshold: 小规模免税起征点（不含税销售额，默认10万；0表示不享受）
        
        返回:
            dict: 包含详细计算结果
        """
        industry = self.get_industry_by_id(industry_id)
        if not industry:
            raise ValueError(f"未找到行业: {industry_id}")
        
        taxpayer_type = industry['taxpayer_type']
        
        # 确定适用税率/征收率：小规模可选征收率
        if taxpayer_type == 'small' and levy_rate is not None:
            tax_rate = float(levy_rate)
        else:
            tax_rate = industry['output_rate']
        
        # 含税换算为不含税
        if is_tax_inclusive:
            actual_sales = sales_amount / (1 + tax_rate)
        else:
            actual_sales = sales_amount
        
        notes = []
        
        # 小规模纳税人免税起征点
        exemption_applied = False
        if taxpayer_type == 'small' and exemption_threshold and exemption_threshold > 0:
            if actual_sales <= exemption_threshold:
                exemption_applied = True
        
        # 一般纳税人计算
        if taxpayer_type == 'general':
            output_tax = actual_sales * tax_rate
            input_tax_val = input_tax
            other_val = other_deductions
            vat_before = output_tax - input_tax - other_deductions
            # 加计抵减：以进项税额为基数，且不超过抵减前应纳税额
            add_deduction = input_tax * float(additional_deduction_rate)
            applied_add = min(add_deduction, max(vat_before, 0))
            carry_add = add_deduction - applied_add
            vat_payable = vat_before - applied_add
            total_deductions = input_tax + other_deductions + applied_add
        # 小规模纳税人计算（简易计税，不得抵扣）
        else:
            output_tax = 0
            input_tax_val = 0
            other_val = 0
            total_deductions = 0
            applied_add = 0
            carry_add = 0
            if exemption_applied:
                vat_payable = 0
                notes.append(f'销售额未超过起征点{exemption_threshold}元，免征增值税')
            else:
                vat_payable = actual_sales * tax_rate
        
        # 附加税费：以应纳税额为基数，留抵或免征时不征
        surcharge = vat_payable * additional_tax_rate if vat_payable > 0 else 0
        total_tax = vat_payable + surcharge
        
        # 税负率
        if actual_sales > 0:
            tax_burden_rate = (vat_payable / actual_sales) * 100
            composite_tax_burden_rate = (total_tax / actual_sales) * 100
        else:
            tax_burden_rate = 0
            composite_tax_burden_rate = 0
        
        result = {
            'industry_name': industry['name'],
            'taxpayer_type': '一般纳税人' if taxpayer_type == 'general' else '小规模纳税人',
            'tax_rate': tax_rate,
            'sales_amount': round(actual_sales, 2),
            'output_tax': round(output_tax, 2),
            'input_tax': round(input_tax_val, 2),
            'other_deductions': round(other_val, 2),
            'additional_deduction_rate': float(additional_deduction_rate),
            'additional_deduction_amount': round(applied_add, 2),
            'additional_deduction_carry': round(carry_add, 2),
            'total_deductions': round(total_deductions, 2),
            'vat_payable': round(vat_payable, 2),
            'additional_tax_rate': additional_tax_rate,
            'surcharge': round(surcharge, 2),
            'total_tax': round(total_tax, 2),
            'tax_burden_rate': round(tax_burden_rate, 2),
            'composite_tax_burden_rate': round(composite_tax_burden_rate, 2),
            'calculation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        if taxpayer_type == 'small':
            notes.append('小规模纳税人采用简易计税方法，不得抵扣进项税额')
        if applied_add > 0:
            notes.append(f'享受加计抵减{applied_add:.2f}元' + (f'，结转下期{carry_add:.2f}元' if carry_add > 0 else ''))
        
        if notes:
            result['note'] = '；'.join(notes)
        
        return result
    
    def calculate_scenario_analysis(self, industry_id, sales_amount, 
                                   input_tax_range, step=1000,
                                   is_tax_inclusive=False, levy_rate=None,
                                   additional_tax_rate=0.12,
                                   additional_deduction_rate=0.0,
                                   exemption_threshold=100000):
        """
        情景分析：不同进项税额下的税负变化
        
        参数:
            industry_id: 行业ID
            sales_amount: 销售额（元）
            input_tax_range: [最小值, 最大值]
            step: 步长（元）
            is_tax_inclusive / levy_rate / additional_tax_rate / additional_deduction_rate
            / exemption_threshold: 透传给 calculate_vat
        
        返回:
            list: 各情景的计算结果
        """
        results = []
        min_input, max_input = input_tax_range
        
        current_input = min_input
        while current_input <= max_input:
            result = self.calculate_vat(
                industry_id, sales_amount, current_input,
                is_tax_inclusive=is_tax_inclusive,
                levy_rate=levy_rate,
                additional_tax_rate=additional_tax_rate,
                additional_deduction_rate=additional_deduction_rate,
                exemption_threshold=exemption_threshold
            )
            results.append(result)
            current_input += step
        
        return results
    
    def compare_industries(self, sales_amount, input_tax=0, other_deductions=0,
                           is_tax_inclusive=False, additional_tax_rate=0.12,
                           exemption_threshold=100000, industry_ids=None):
        """
        多行业税负对比：相同销售额/进项下，计算各行业的应纳税额与税负率
        
        返回:
            list: 各行业计算结果
        """
        industries = self.get_industries()
        if industry_ids:
            industries = [i for i in industries if i['id'] in industry_ids]
        
        results = []
        for industry in industries:
            # 小规模默认用 output_rate（3%）参与横向对比
            levy = industry['output_rate'] if industry['taxpayer_type'] == 'small' else None
            # 加计抵减：对比时取各行业最高档，便于横向比较优惠力度
            add_rate = 0.0
            opts = industry.get('additional_deduction_options')
            if opts:
                add_rate = max(opts)
            r = self.calculate_vat(
                industry['id'], sales_amount, input_tax, other_deductions,
                is_tax_inclusive=is_tax_inclusive,
                levy_rate=levy,
                additional_tax_rate=additional_tax_rate,
                additional_deduction_rate=add_rate,
                exemption_threshold=exemption_threshold
            )
            results.append(r)
        return results
    
    def get_tax_planning_suggestions(self, result):
        """
        根据计算结果提供税务筹划建议
        
        参数:
            result: calculate_vat返回的结果
        
        返回:
            list: 建议列表
        """
        suggestions = []
        
        # 税负率分析
        tax_burden = result['tax_burden_rate']
        tax_rate = result['tax_rate'] * 100
        
        if result['taxpayer_type'] == '一般纳税人':
            # 税负率过高
            if tax_burden > tax_rate * 0.7:
                suggestions.append({
                    'type': 'warning',
                    'title': '税负率偏高',
                    'content': f'当前税负率{tax_burden}%较高，建议检查进项发票是否充分取得'
                })
            
            # 税负率过低
            elif tax_burden < tax_rate * 0.3 and tax_burden > 0:
                suggestions.append({
                    'type': 'info',
                    'title': '税负率偏低',
                    'content': f'当前税负率{tax_burden}%较低，注意保持合理的进销项比例，防范税务风险'
                })
            
            # 留抵税额
            if result['vat_payable'] < 0:
                suggestions.append({
                    'type': 'success',
                    'title': '形成留抵税额',
                    'content': f'本期形成留抵税额{abs(result["vat_payable"])}元，可用于下期继续抵扣'
                })
            
            # 进项抵扣建议
            if result['input_tax'] == 0:
                suggestions.append({
                    'type': 'warning',
                    'title': '无进项抵扣',
                    'content': '未取得进项发票将导致全额缴纳增值税，建议及时索取增值税专用发票'
                })
            
            # 加计抵减提示
            if result.get('additional_deduction_amount', 0) > 0:
                carry = result.get('additional_deduction_carry', 0)
                content = f'本期享受加计抵减{result["additional_deduction_amount"]}元'
                if carry > 0:
                    content += f'，未抵减完的{carry}元可结转下期继续抵减'
                suggestions.append({
                    'type': 'success',
                    'title': '享受加计抵减',
                    'content': content
                })
        
        return suggestions



