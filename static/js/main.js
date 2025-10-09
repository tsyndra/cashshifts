let cashShiftData = null;
let bankData = null;
let bankColumns = [];

$(document).ready(function() {
    // Загружаем филиалы
    loadBranches();
    
    // Обработчики событий
    $('#branchSelect').on('change', onBranchChange);
    $('#cashShiftSelect').on('change', onCashShiftChange);
    $('#loadCashShiftBtn').on('click', loadCashShiftData);
    $('#bankReportFile').on('change', onBankReportFileSelected);
    $('#uploadBankReportBtn').on('click', uploadBankReport);
    $('#compareBtn').on('click', compareData);
});

function loadBranches() {
    $.ajax({
        url: '/api/branches',
        method: 'GET',
        success: function(branches) {
            const select = $('#branchSelect');
            select.empty().append('<option value="">Выберите филиал...</option>');
            branches.forEach(branch => {
                select.append(`<option value="${branch.id}">${branch.name}</option>`);
            });
        },
        error: function(xhr) {
            showError('Ошибка загрузки филиалов: ' + (xhr.responseJSON?.error || 'Неизвестная ошибка'));
        }
    });
}

function onBranchChange() {
    const branchId = $(this).val();
    const cashShiftSelect = $('#cashShiftSelect');
    
    if (!branchId) {
        cashShiftSelect.prop('disabled', true).empty()
            .append('<option value="">Сначала выберите филиал...</option>');
        $('#loadCashShiftBtn').prop('disabled', true);
        return;
    }
    
    // Загружаем кассовые смены для выбранного филиала
    showLoading();
    $.ajax({
        url: '/api/cash-shifts',
        method: 'GET',
        data: { branch_id: branchId },
        success: function(shifts) {
            hideLoading();
            cashShiftSelect.prop('disabled', false).empty()
                .append('<option value="">Выберите смену...</option>');
            
            shifts.forEach(shift => {
                const openDate = new Date(shift.openDate).toLocaleString('ru-RU');
                const closeDate = shift.closeDate ? new Date(shift.closeDate).toLocaleString('ru-RU') : 'Не закрыта';
                cashShiftSelect.append(
                    `<option value="${shift.id}" data-branch-id="${branchId}">
                        ${openDate} - ${closeDate} (${shift.cashierName || 'Неизвестный кассир'})
                    </option>`
                );
            });
        },
        error: function(xhr) {
            hideLoading();
            showError('Ошибка загрузки смен: ' + (xhr.responseJSON?.error || 'Неизвестная ошибка'));
        }
    });
}

function onCashShiftChange() {
    const shiftId = $(this).val();
    $('#loadCashShiftBtn').prop('disabled', !shiftId);
}

function loadCashShiftData() {
    const shiftId = $('#cashShiftSelect').val();
    const branchId = $('#branchSelect').val();
    
    if (!shiftId || !branchId) {
        showError('Выберите филиал и смену');
        return;
    }
    
    showLoading();
    $.ajax({
        url: `/api/cash-shift/${shiftId}/payments`,
        method: 'GET',
        data: { branch_id: branchId },
        success: function(data) {
            hideLoading();
            cashShiftData = data.payments;
            $('#cashShiftCount').text(cashShiftData.length);
            $('#cashShiftInfo').show();
            
            // Отображаем статистику по типам операций
            displayOperationStats(data.operationStats, data.totalOperations, data.totalSum);
            
            checkCompareButton();
            showSuccess(`Загружено ${cashShiftData.length} операций`);
        },
        error: function(xhr) {
            hideLoading();
            showError('Ошибка загрузки данных смены: ' + (xhr.responseJSON?.error || 'Неизвестная ошибка'));
        }
    });
}

function onBankReportFileSelected() {
    const file = this.files[0];
    $('#uploadBankReportBtn').prop('disabled', !file);
}

function uploadBankReport() {
    const fileInput = $('#bankReportFile')[0];
    const file = fileInput.files[0];
    
    if (!file) {
        showError('Выберите файл');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    showLoading();
    $.ajax({
        url: '/api/upload-bank-report',
        method: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        success: function(response) {
            hideLoading();
            bankData = response.data;
            bankColumns = response.columns;
            
            $('#bankReportCount').text(response.rows_count);
            $('#bankReportInfo').show();
            
            // Заполняем селекты для маппинга колонок
            const amountSelect = $('#amountColumn');
            const typeSelect = $('#typeColumn');
            const dateSelect = $('#dateColumn');
            
            amountSelect.empty();
            typeSelect.empty();
            dateSelect.empty().append('<option value="">Не использовать</option>');
            
            bankColumns.forEach(col => {
                amountSelect.append(`<option value="${col}">${col}</option>`);
                typeSelect.append(`<option value="${col}">${col}</option>`);
                dateSelect.append(`<option value="${col}">${col}</option>`);
            });
            
            // Пытаемся автоматически определить колонки
            const amountCol = bankColumns.find(c => c.toLowerCase().includes('сумма') || c.toLowerCase().includes('amount'));
            const typeCol = bankColumns.find(c => c.toLowerCase().includes('тип') || c.toLowerCase().includes('type') || c.toLowerCase().includes('способ'));
            const dateCol = bankColumns.find(c => c.toLowerCase().includes('дата') || c.toLowerCase().includes('date'));
            
            if (amountCol) amountSelect.val(amountCol);
            if (typeCol) typeSelect.val(typeCol);
            if (dateCol) dateSelect.val(dateCol);
            
            $('#columnMapping').show();
            checkCompareButton();
            showSuccess(`Загружено ${response.rows_count} строк из банковского отчета`);
        },
        error: function(xhr) {
            hideLoading();
            showError('Ошибка загрузки отчета: ' + (xhr.responseJSON?.error || 'Неизвестная ошибка'));
        }
    });
}

function checkCompareButton() {
    const canCompare = cashShiftData !== null && bankData !== null;
    $('#compareBtn').prop('disabled', !canCompare);
}

function compareData() {
    if (!cashShiftData || !bankData) {
        showError('Загрузите данные кассовой смены и банковский отчет');
        return;
    }
    
    const mapping = {
        amount: $('#amountColumn').val(),
        type: $('#typeColumn').val(),
        date: $('#dateColumn').val()
    };
    
    if (!mapping.amount || !mapping.type) {
        showError('Укажите соответствие колонок для суммы и типа платежа');
        return;
    }
    
    showLoading();
    $.ajax({
        url: '/api/compare-data',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            cashShiftData: cashShiftData,
            bankData: bankData,
            mapping: mapping
        }),
        success: function(response) {
            hideLoading();
            displayComparisonResults(response);
        },
        error: function(xhr) {
            hideLoading();
            showError('Ошибка сравнения: ' + (xhr.responseJSON?.error || 'Неизвестная ошибка'));
        }
    });
}

function displayComparisonResults(response) {
    const summary = response.summary;
    const comparison = response.comparison;
    
    // Отображаем сводку
    $('#summary').html(`
        <div class="col-md-3">
            <div class="card text-center">
                <div class="card-body">
                    <h6 class="card-title">Совпадений</h6>
                    <p class="card-text fs-4 text-success">${summary.matchedCount}</p>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card text-center">
                <div class="card-body">
                    <h6 class="card-title">Только в кассе</h6>
                    <p class="card-text fs-4 text-warning">${summary.unmatchedCashCount}</p>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card text-center">
                <div class="card-body">
                    <h6 class="card-title">Только в банке</h6>
                    <p class="card-text fs-4 text-danger">${summary.unmatchedBankCount}</p>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card text-center">
                <div class="card-body">
                    <h6 class="card-title">Разница</h6>
                    <p class="card-text fs-4 ${summary.totalDifference === 0 ? 'text-success' : 'text-danger'}">
                        ${summary.totalDifference.toFixed(2)} ₽
                    </p>
                </div>
            </div>
        </div>
    `);
    
    // Отображаем таблицу
    const tbody = $('#comparisonTable tbody');
    tbody.empty();
    
        comparison.forEach(item => {
            const statusBadge = item.status === 'match' 
                ? '<span class="badge bg-success">Совпадение</span>' 
                : '<span class="badge bg-warning">Несовпадение</span>';
            
            const typeLabel = item.type === 'matched' ? '' :
                item.type === 'cash_only' ? '<span class="badge bg-info">Только в кассе</span>' :
                '<span class="badge bg-secondary">Только в банке</span>';
            
            tbody.append(`
                <tr class="${item.status === 'match' ? '' : 'table-warning'}">
                    <td>${item.paymentType} ${typeLabel}</td>
                    <td>${item.cashAmount.toFixed(2)} ₽</td>
                    <td>${item.bankAmount.toFixed(2)} ₽</td>
                    <td class="${item.difference === 0 ? 'text-success' : 'text-danger'}">
                        ${item.difference.toFixed(2)} ₽
                    </td>
                    <td>${statusBadge}</td>
                </tr>
            `);
        });
    
    $('#comparisonResults').show();
    $('html, body').animate({
        scrollTop: $('#comparisonResults').offset().top - 100
    }, 500);
}

function showLoading() {
    $('#loadingSpinner').show();
}

function hideLoading() {
    $('#loadingSpinner').hide();
}

function showError(message) {
    alert('Ошибка: ' + message);
}

function showSuccess(message) {
    console.log('Успех: ' + message);
}

function displayOperationStats(operationStats, totalOperations, totalSum) {
    let statsHtml = `
        <div class="alert alert-info mt-3">
            <h6><strong>Статистика по типам операций:</strong></h6>
            <div class="row">
    `;
    
    // Отображаем статистику для каждого типа операции
    Object.entries(operationStats).forEach(([paymentType, stats]) => {
        statsHtml += `
            <div class="col-md-6 mb-2">
                <strong>${paymentType}:</strong> ${stats.count} операций, 
                <span class="text-primary">${stats.sum.toFixed(2)} ₽</span>
            </div>
        `;
    });
    
    statsHtml += `
            </div>
            <hr>
            <div class="row">
                <div class="col-md-6">
                    <strong>Всего операций:</strong> ${totalOperations}
                </div>
                <div class="col-md-6">
                    <strong>Общая сумма:</strong> 
                    <span class="text-success">${totalSum.toFixed(2)} ₽</span>
                </div>
            </div>
        </div>
    `;
    
    // Добавляем статистику в информационный блок
    $('#cashShiftInfo').append(statsHtml);
}

