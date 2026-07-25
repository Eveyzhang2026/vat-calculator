/**
 * 增值税税负动态测算 - 前端交互逻辑
 */

let industries = [];
let lastResult = null;
let burdenChart = null;

document.addEventListener('DOMContentLoaded', function() {
    loadIndustries();
    setupEventListeners();
});

async function loadIndustries() {
    try {
        const response = await fetch('/api/industries');
        const data = await response.json();
        if (data.success) {
            industries = data.industries;
            populateIndustrySelect(industries);
        } else {
            showError('加载行业数据失败');
        }
    } catch (error) {
        console.error('加载行业数据出错:', error);
        showError('网络请求失败，请刷新页面重试');
    }
}

function populateIndustrySelect(list) {
    const select = document.getElementById('industry');
    list.forEach(industry => {
        const option = document.createElement('option');
        option.value = industry.id;
        option.textContent = `${industry.name} (${(industry.output_rate * 100).toFixed(0)}%)`;
        option.dataset.description = industry.description || '';
        option.dataset.type = industry.taxpayer_type;
        option.dataset.rateOptions = JSON.stringify(industry.rate_options || []);
        option.dataset.deductionOptions = JSON.stringify(industry.additional_deduction_options || []);
        select.appendChild(option);
    });

    select.addEventListener('change', function() {
        const opt = this.options[this.selectedIndex];
        document.getElementById('industryDesc').textContent = opt.dataset.description || '';
        const type = opt.dataset.type;
        const rateOptions = JSON.parse(opt.dataset.rateOptions || '[]');
        const deductionOptions = JSON.parse(opt.dataset.deductionOptions || '[]');
        updateFormForTaxpayer(type, rateOptions, deductionOptions);
    });
}

function updateFormForTaxpayer(type, rateOptions, deductionOptions) {
    const inputTaxGroup = document.getElementById('inputTaxGroup');
    const otherGroup = document.getElementById('otherDeductionsGroup');
    const levyGroup = document.getElementById('levyRateGroup');
    const addGroup = document.getElementById('addDeductionGroup');
    const exemptionGroup = document.getElementById('exemptionGroup');
    const levySelect = document.getElementById('levyRate');

    if (type === 'small') {
        inputTaxGroup.style.opacity = '0.5';
        inputTaxGroup.querySelector('input').disabled = true;
        inputTaxGroup.querySelector('input').value = '';
        otherGroup.style.opacity = '0.5';
        otherGroup.querySelector('input').disabled = true;
        otherGroup.querySelector('input').value = '';
        addGroup.style.display = 'none';

        levySelect.innerHTML = '';
        rateOptions.forEach(r => {
            const o = document.createElement('option');
            o.value = r;
            o.textContent = (r * 100).toFixed(0) + '%';
            levySelect.appendChild(o);
        });
        levyGroup.style.display = 'flex';
        exemptionGroup.style.display = 'flex';
    } else {
        inputTaxGroup.style.opacity = '1';
        inputTaxGroup.querySelector('input').disabled = false;
        otherGroup.style.opacity = '1';
        otherGroup.querySelector('input').disabled = false;
        levyGroup.style.display = 'none';
        exemptionGroup.style.display = 'none';

        if (deductionOptions && deductionOptions.length > 0) {
            const sel = document.getElementById('additionalDeductionRate');
            sel.innerHTML = '<option value="0">无</option>';
            deductionOptions.forEach(r => {
                const o = document.createElement('option');
                o.value = r;
                o.textContent = (r * 100).toFixed(0) + '%';
                sel.appendChild(o);
            });
            addGroup.style.display = 'flex';
        } else {
            addGroup.style.display = 'none';
        }
    }
}

function setupEventListeners() {
    document.getElementById('vatForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        await calculateVAT();
    });
    document.getElementById('resetBtn').addEventListener('click', resetForm);
    document.getElementById('exportBtn').addEventListener('click', exportResult);
    document.getElementById('compareBtn').addEventListener('click', compareIndustries);
}

function getFormData() {
    const industryEl = document.getElementById('industry');
    const opt = industryEl.options[industryEl.selectedIndex];
    const type = opt.dataset.type;
    const deductionOptions = JSON.parse(opt.dataset.deductionOptions || '[]');

    const sales = parseFloat(document.getElementById('salesAmount').value);
    const inputTax = parseFloat(document.getElementById('inputTax').value);
    const other = parseFloat(document.getElementById('otherDeductions').value);

    const data = {
        industry_id: industryEl.value,
        sales_amount: isNaN(sales) ? null : sales,
        input_tax: isNaN(inputTax) ? 0 : inputTax,
        other_deductions: isNaN(other) ? 0 : other,
        is_tax_inclusive: document.getElementById('isTaxInclusive').checked,
        additional_tax_rate: parseFloat(document.getElementById('additionalTaxRate').value)
    };

    if (type === 'small') {
        data.levy_rate = parseFloat(document.getElementById('levyRate').value);
        data.exemption_threshold = parseFloat(document.getElementById('exemptionThreshold').value);
        data.additional_deduction_rate = 0;
    } else {
        data.levy_rate = null;
        data.exemption_threshold = 100000;
        data.additional_deduction_rate = (deductionOptions.length > 0)
            ? parseFloat(document.getElementById('additionalDeductionRate').value)
            : 0;
    }
    return data;
}

async function calculateVAT() {
    const formData = getFormData();

    if (!formData.industry_id) {
        showError('请选择行业');
        return;
    }
    if (formData.sales_amount === null || formData.sales_amount <= 0) {
        showError('请输入有效的销售额（大于0）');
        return;
    }

    showLoading();
    hideError();

    try {
        const response = await fetch('/api/calculate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });
        const data = await response.json();
        if (data.success) {
            lastResult = data.result;
            displayResults(data.result, data.suggestions);
            if (data.result.taxpayer_type === '一般纳税人') {
                await loadScenarioAndDraw(formData, data.result);
            } else {
                document.getElementById('chartSection').style.display = 'none';
            }
        } else {
            showError(data.error || '计算失败');
        }
    } catch (error) {
        console.error('计算出错:', error);
        showError('网络请求失败，请稍后重试');
    } finally {
        hideLoading();
    }
}

async function loadScenarioAndDraw(formData, result) {
    try {
        const outputTax = result.output_tax || 0;
        const maxInput = Math.max(outputTax, 1000);
        const step = maxInput / 20;
        const payload = {
            industry_id: formData.industry_id,
            sales_amount: formData.sales_amount,
            is_tax_inclusive: formData.is_tax_inclusive,
            input_tax_range: [0, maxInput],
            step: step,
            additional_tax_rate: formData.additional_tax_rate,
            additional_deduction_rate: formData.additional_deduction_rate
        };
        const response = await fetch('/api/scenario-analysis', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await response.json();
        if (data.success) {
            drawChart(data.results);
        }
    } catch (e) {
        console.error('情景分析出错:', e);
    }
}

function drawChart(results) {
    const section = document.getElementById('chartSection');
    section.style.display = 'block';

    if (typeof Chart === 'undefined') {
        section.innerHTML = '<p class="help-text">图表库加载失败（需联网加载 Chart.js）</p>';
        return;
    }

    const ctx = document.getElementById('burdenChart');
    const labels = results.map(r => r.input_tax);
    const burden = results.map(r => r.tax_burden_rate);
    const payable = results.map(r => r.vat_payable);

    if (burdenChart) burdenChart.destroy();
    burdenChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                { label: '税负率(%)', data: burden, borderColor: '#667eea',
                  backgroundColor: 'rgba(102,126,234,0.1)', yAxisID: 'y', fill: true, tension: 0.2 },
                { label: '应纳税额(元)', data: payable, borderColor: '#f59e0b',
                  backgroundColor: 'rgba(245,158,11,0.1)', yAxisID: 'y1', fill: false, tension: 0.2 }
            ]
        },
        options: {
            responsive: true,
            interaction: { mode: 'index', intersect: false },
            scales: {
                y: { type: 'linear', position: 'left', title: { display: true, text: '税负率(%)' } },
                y1: { type: 'linear', position: 'right', title: { display: true, text: '应纳税额(元)' },
                      grid: { drawOnChartArea: false } }
            }
        }
    });
}

function displayResults(result, suggestions) {
    document.getElementById('resultSection').style.display = 'block';
    document.getElementById('exportBtn').style.display = 'inline-block';

    document.getElementById('resultIndustry').textContent = result.industry_name;
    document.getElementById('resultTaxpayerType').textContent = result.taxpayer_type;
    document.getElementById('resultTaxRate').textContent = (result.tax_rate * 100).toFixed(2) + '%';
    document.getElementById('resultSales').textContent = formatCurrency(result.sales_amount);
    document.getElementById('resultOutputTax').textContent = formatCurrency(result.output_tax);
    document.getElementById('resultInputTax').textContent = formatCurrency(result.input_tax);
    document.getElementById('resultOtherDeductions').textContent = formatCurrency(result.other_deductions);
    document.getElementById('resultAddDeduction').textContent = formatCurrency(result.additional_deduction_amount);
    document.getElementById('resultVatPayable').textContent = formatCurrency(result.vat_payable);
    document.getElementById('resultSurcharge').textContent = formatCurrency(result.surcharge);
    document.getElementById('resultTaxBurden').textContent = result.tax_burden_rate.toFixed(2) + '%';
    document.getElementById('resultCompositeBurden').textContent = result.composite_tax_burden_rate.toFixed(2) + '%';

    const isSmall = result.taxpayer_type === '小规模纳税人';
    document.getElementById('rowOutputTax').style.display = isSmall ? 'none' : 'flex';
    document.getElementById('rowInputTax').style.display = isSmall ? 'none' : 'flex';
    document.getElementById('rowOtherDeductions').style.display = isSmall ? 'none' : 'flex';
    const showAdd = result.additional_deduction_amount > 0 || result.additional_deduction_rate > 0;
    document.getElementById('rowAddDeduction').style.display = showAdd ? 'flex' : 'none';

    if (result.note) {
        const noteDiv = document.createElement('div');
        noteDiv.className = 'result-note';
        noteDiv.innerHTML = `<strong>提示：</strong>${result.note}`;
        const existing = document.querySelector('.result-note');
        if (existing) existing.remove();
        document.querySelector('.result-body').appendChild(noteDiv);
    }

    if (suggestions && suggestions.length > 0) {
        displaySuggestions(suggestions);
    } else {
        document.getElementById('suggestionsSection').style.display = 'none';
    }

    document.getElementById('resultSection').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function displaySuggestions(suggestions) {
    const section = document.getElementById('suggestionsSection');
    const list = document.getElementById('suggestionsList');
    list.innerHTML = '';
    suggestions.forEach(s => {
        const item = document.createElement('div');
        item.className = 'suggestion-item';
        item.innerHTML = `
            <span class="type ${s.type}">${getTypeLabel(s.type)}</span>
            <div class="title">${s.title}</div>
            <div class="content">${s.content}</div>
        `;
        list.appendChild(item);
    });
    section.style.display = 'block';
}

function getTypeLabel(type) {
    const labels = { 'warning': '⚠️ 提醒', 'info': 'ℹ️ 提示', 'success': '✅ 优势' };
    return labels[type] || '💡 建议';
}

async function compareIndustries() {
    const formData = getFormData();
    if (formData.sales_amount === null || formData.sales_amount <= 0) {
        showError('请先输入有效的销售额再进行多行业对比');
        return;
    }
    const exemption = formData.levy_rate !== null
        ? parseFloat(document.getElementById('exemptionThreshold').value)
        : 100000;
    const payload = {
        sales_amount: formData.sales_amount,
        input_tax: formData.input_tax,
        other_deductions: formData.other_deductions,
        is_tax_inclusive: formData.is_tax_inclusive,
        additional_tax_rate: formData.additional_tax_rate,
        exemption_threshold: exemption
    };
    try {
        const response = await fetch('/api/compare', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await response.json();
        if (data.success) {
            renderCompareTable(data.results);
        } else {
            showError(data.error || '对比失败');
        }
    } catch (e) {
        console.error('对比出错:', e);
        showError('网络请求失败，请稍后重试');
    }
}

function renderCompareTable(results) {
    const section = document.getElementById('compareSection');
    const tbody = document.querySelector('#compareTable tbody');
    tbody.innerHTML = '';
    results.forEach(r => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${r.industry_name}</td>
            <td>${r.taxpayer_type}</td>
            <td>${(r.tax_rate * 100).toFixed(0)}%</td>
            <td>${formatCurrency(r.vat_payable)}</td>
            <td>${formatCurrency(r.surcharge)}</td>
            <td>${r.tax_burden_rate.toFixed(2)}%</td>
            <td>${r.composite_tax_burden_rate.toFixed(2)}%</td>
        `;
        tbody.appendChild(tr);
    });
    section.style.display = 'block';
    section.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function resetForm() {
    document.getElementById('vatForm').reset();
    document.getElementById('resultSection').style.display = 'none';
    document.getElementById('chartSection').style.display = 'none';
    document.getElementById('suggestionsSection').style.display = 'none';
    document.getElementById('compareSection').style.display = 'none';
    document.getElementById('industryDesc').textContent = '';
    document.getElementById('exportBtn').style.display = 'none';
    hideError();
    if (burdenChart) { burdenChart.destroy(); burdenChart = null; }
    ['inputTaxGroup', 'otherDeductionsGroup'].forEach(id => {
        const g = document.getElementById(id);
        g.style.opacity = '1';
        g.querySelector('input').disabled = false;
    });
    document.getElementById('levyRateGroup').style.display = 'none';
    document.getElementById('addDeductionGroup').style.display = 'none';
    document.getElementById('exemptionGroup').style.display = 'none';
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function formatCurrency(amount) {
    return '¥' + Number(amount).toLocaleString('zh-CN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

function showLoading() {
    const btn = document.querySelector('#vatForm button[type="submit"]');
    btn.disabled = true;
    btn.textContent = '计算中...';
}
function hideLoading() {
    const btn = document.querySelector('#vatForm button[type="submit"]');
    btn.disabled = false;
    btn.textContent = '🧮 立即计算';
}

function showError(message) {
    const el = document.getElementById('errorMsg');
    el.textContent = '❌ ' + message;
    el.style.display = 'block';
}
function hideError() {
    const el = document.getElementById('errorMsg');
    el.style.display = 'none';
}

function exportResult() {
    if (!lastResult) return;
    const r = lastResult;
    const rows = [
        ['项目', '数值'],
        ['行业', r.industry_name],
        ['纳税人类型', r.taxpayer_type],
        ['适用税率/征收率', (r.tax_rate * 100).toFixed(2) + '%'],
        ['不含税销售额', r.sales_amount],
        ['销项税额', r.output_tax],
        ['进项税额', r.input_tax],
        ['其他抵扣', r.other_deductions],
        ['加计抵减', r.additional_deduction_amount],
        ['应纳税额', r.vat_payable],
        ['附加税费', r.surcharge],
        ['税负率(增值税)', r.tax_burden_rate + '%'],
        ['综合税负率', r.composite_tax_burden_rate + '%']
    ];
    const csv = '﻿' + rows.map(row => row.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `增值税测算_${r.industry_name}.csv`;
    a.click();
    URL.revokeObjectURL(url);
}
