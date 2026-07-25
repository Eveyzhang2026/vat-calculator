"""
增值税税负动态测算系统 - Flask Web应用
提供RESTful API接口和Web界面
"""

from flask import Flask, render_template, request, jsonify
from calculator import VATCalculator
import traceback

app = Flask(__name__)
calculator = VATCalculator()


@app.route('/')
def index():
    """主页"""
    return render_template('index.html')


@app.route('/api/industries', methods=['GET'])
def get_industries():
    """获取行业列表API"""
    try:
        industries = calculator.get_industries()
        return jsonify({
            'success': True,
            'industries': industries
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/calculate', methods=['POST'])
def calculate_vat():
    """计算增值税API"""
    try:
        data = request.get_json()
        
        # 参数验证
        if not data:
            return jsonify({
                'success': False,
                'error': '请求数据为空'
            }), 400
        
        industry_id = data.get('industry_id')
        sales_amount = data.get('sales_amount')
        
        if not industry_id:
            return jsonify({
                'success': False,
                'error': '请选择行业'
            }), 400
        
        if not sales_amount or sales_amount <= 0:
            return jsonify({
                'success': False,
                'error': '请输入有效的销售额'
            }), 400
        
        # 提取参数
        input_tax = data.get('input_tax', 0)
        other_deductions = data.get('other_deductions', 0)
        is_tax_inclusive = data.get('is_tax_inclusive', False)
        levy_rate = data.get('levy_rate')
        additional_tax_rate = data.get('additional_tax_rate', 0.12)
        additional_deduction_rate = data.get('additional_deduction_rate', 0)
        exemption_threshold = data.get('exemption_threshold', 100000)
        
        # 执行计算
        result = calculator.calculate_vat(
            industry_id=industry_id,
            sales_amount=float(sales_amount),
            input_tax=float(input_tax),
            other_deductions=float(other_deductions),
            is_tax_inclusive=bool(is_tax_inclusive),
            levy_rate=levy_rate,
            additional_tax_rate=float(additional_tax_rate),
            additional_deduction_rate=float(additional_deduction_rate),
            exemption_threshold=float(exemption_threshold)
        )
        
        # 获取税务筹划建议
        suggestions = calculator.get_tax_planning_suggestions(result)
        
        return jsonify({
            'success': True,
            'result': result,
            'suggestions': suggestions
        })
    
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    
    except Exception as e:
        print(f"计算错误: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': f'计算失败: {str(e)}'
        }), 500


@app.route('/api/scenario-analysis', methods=['POST'])
def scenario_analysis():
    """情景分析API"""
    try:
        data = request.get_json()
        
        industry_id = data.get('industry_id')
        sales_amount = data.get('sales_amount')
        input_tax_range = data.get('input_tax_range', [0, 200000])
        step = data.get('step', 10000)
        is_tax_inclusive = data.get('is_tax_inclusive', False)
        levy_rate = data.get('levy_rate')
        additional_tax_rate = data.get('additional_tax_rate', 0.12)
        additional_deduction_rate = data.get('additional_deduction_rate', 0)
        exemption_threshold = data.get('exemption_threshold', 100000)
        
        if not industry_id or not sales_amount:
            return jsonify({
                'success': False,
                'error': '缺少必要参数'
            }), 400
        
        results = calculator.calculate_scenario_analysis(
            industry_id=industry_id,
            sales_amount=float(sales_amount),
            input_tax_range=input_tax_range,
            step=int(step),
            is_tax_inclusive=bool(is_tax_inclusive),
            levy_rate=levy_rate,
            additional_tax_rate=float(additional_tax_rate),
            additional_deduction_rate=float(additional_deduction_rate),
            exemption_threshold=float(exemption_threshold)
        )
        
        return jsonify({
            'success': True,
            'results': results
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/compare', methods=['POST'])
def compare_industries():
    """多行业税负对比API"""
    try:
        data = request.get_json()
        sales_amount = data.get('sales_amount')
        if not sales_amount:
            return jsonify({
                'success': False,
                'error': '请输入销售额'
            }), 400
        
        results = calculator.compare_industries(
            sales_amount=float(sales_amount),
            input_tax=float(data.get('input_tax', 0)),
            other_deductions=float(data.get('other_deductions', 0)),
            is_tax_inclusive=bool(data.get('is_tax_inclusive', False)),
            additional_tax_rate=float(data.get('additional_tax_rate', 0.12)),
            exemption_threshold=float(data.get('exemption_threshold', 100000))
        )
        
        return jsonify({
            'success': True,
            'results': results
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    print("=" * 60)
    print("增值税税负动态测算系统启动中...")
    print("=" * 60)
    print("访问地址: http://127.0.0.1:5000")
    print("按 Ctrl+C 停止服务")
    print("=" * 60)
    
    app.run(debug=True, host='127.0.0.1', port=5000)
