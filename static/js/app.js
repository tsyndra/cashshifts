/**
 * Cash Shifts - Главный скрипт приложения
 * Очищенная производственная версия без дебаг-сообщений
 */

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
            console.error('Ошибка загрузки филиалов:', xhr.status);
            showError('Ошибка загрузки филиалов: ' + (xhr.responseJSON?.error || 'Неизвестная ошибка'));
        }
    });
}

function onBranchChange() {
    const branchId = $(this).val();
    const cashShiftSelect = $('#cashShiftSelect');
    
    // Скрываем предыдущие данные
    $('#cashShiftInfo').hide();
    $('#operationsTableContainer').hide();
    $('#comparisonResults').hide();
    
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
    
    // Скрываем предыдущие данные при смене смены
    if (!shiftId) {
        $('#cashShiftInfo').hide();
        $('#operationsTableContainer').hide();
        $('#comparisonResults').hide();
    }
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
            $('#cashShiftInfo').fadeIn('fast');
            
            // Очищаем предыдущую статистику (кроме первого блока с количеством операций)
            $('#cashShiftInfo .alert-info:not(:first)').remove();
            
            // Отображаем статистику по типам операций
            if (data.operationStats) {
                displayOperationStats(data.operationStats, data.totalOperations, data.totalSum);
            }
            
            // Создаем таблицу операций
            if (cashShiftData && cashShiftData.length > 0) {
                createOperationsTable(cashShiftData);
            }
            
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
            $('#bankReportInfo').fadeIn('fast');
            
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
            
            $('#columnMapping').fadeIn('fast');
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
    
    // Отображаем сводку с анимацией
    $('#summary').html(`
        <div class="col-md-3 mb-3">
            <div class="card text-center shadow-sm border-0 animate__animated animate__fadeInUp">
                <div class="card-body">
                    <i class="fas fa-check-circle fa-2x text-success mb-2"></i>
                    <h6 class="card-title text-muted">Совпадений</h6>
                    <p class="card-text fs-3 text-success fw-bold">${summary.matchedCount}</p>
                </div>
            </div>
        </div>
        <div class="col-md-3 mb-3">
            <div class="card text-center shadow-sm border-0 animate__animated animate__fadeInUp" style="animation-delay: 0.1s">
                <div class="card-body">
                    <i class="fas fa-exclamation-triangle fa-2x text-warning mb-2"></i>
                    <h6 class="card-title text-muted">Только в кассе</h6>
                    <p class="card-text fs-3 text-warning fw-bold">${summary.unmatchedCashCount}</p>
                </div>
            </div>
        </div>
        <div class="col-md-3 mb-3">
            <div class="card text-center shadow-sm border-0 animate__animated animate__fadeInUp" style="animation-delay: 0.2s">
                <div class="card-body">
                    <i class="fas fa-times-circle fa-2x text-danger mb-2"></i>
                    <h6 class="card-title text-muted">Только в банке</h6>
                    <p class="card-text fs-3 text-danger fw-bold">${summary.unmatchedBankCount}</p>
                </div>
            </div>
        </div>
        <div class="col-md-3 mb-3">
            <div class="card text-center shadow-sm border-0 animate__animated animate__fadeInUp" style="animation-delay: 0.3s">
                <div class="card-body">
                    <i class="fas fa-balance-scale fa-2x ${summary.totalDifference === 0 ? 'text-success' : 'text-danger'} mb-2"></i>
                    <h6 class="card-title text-muted">Разница</h6>
                    <p class="card-text fs-3 ${summary.totalDifference === 0 ? 'text-success' : 'text-danger'} fw-bold">
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
            ? '<span class="badge bg-success"><i class="fas fa-check"></i> Совпадение</span>' 
            : '<span class="badge bg-warning"><i class="fas fa-exclamation"></i> Несовпадение</span>';
        
        const typeLabel = item.type === 'matched' ? '' :
            item.type === 'cash_only' ? '<span class="badge bg-info ms-1">Только в кассе</span>' :
            '<span class="badge bg-secondary ms-1">Только в банке</span>';
        
        tbody.append(`
            <tr class="${item.status === 'match' ? 'table-light' : 'table-warning'}">
                <td><strong>${item.paymentType}</strong> ${typeLabel}</td>
                <td class="text-end">${item.cashAmount.toFixed(2)} ₽</td>
                <td class="text-end">${item.bankAmount.toFixed(2)} ₽</td>
                <td class="text-end ${item.difference === 0 ? 'text-success' : 'text-danger'} fw-bold">
                    ${item.difference >= 0 ? '+' : ''}${item.difference.toFixed(2)} ₽
                </td>
                <td class="text-center">${statusBadge}</td>
            </tr>
        `);
    });
    
    $('#comparisonResults').fadeIn('slow');
    $('html, body').animate({
        scrollTop: $('#comparisonResults').offset().top - 100
    }, 500);
}

function showLoading() {
    $('#loadingSpinner').fadeIn('fast');
}

function hideLoading() {
    $('#loadingSpinner').fadeOut('fast');
}

function showError(message) {
    // Используем Toast вместо alert
    const toast = `
        <div class="toast align-items-center text-white bg-danger border-0 position-fixed bottom-0 end-0 m-3" role="alert" style="z-index: 9999">
            <div class="d-flex">
                <div class="toast-body">
                    <i class="fas fa-exclamation-circle me-2"></i>${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;
    
    $('body').append(toast);
    const toastEl = $('.toast').last()[0];
    const bsToast = new bootstrap.Toast(toastEl, { delay: 5000 });
    bsToast.show();
    
    // Удаляем элемент после скрытия
    toastEl.addEventListener('hidden.bs.toast', function() {
        toastEl.remove();
    });
}

function showSuccess(message) {
    // Используем Toast вместо console.log
    const toast = `
        <div class="toast align-items-center text-white bg-success border-0 position-fixed bottom-0 end-0 m-3" role="alert" style="z-index: 9999">
            <div class="d-flex">
                <div class="toast-body">
                    <i class="fas fa-check-circle me-2"></i>${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;
    
    $('body').append(toast);
    const toastEl = $('.toast').last()[0];
    const bsToast = new bootstrap.Toast(toastEl, { delay: 3000 });
    bsToast.show();
    
    // Удаляем элемент после скрытия
    toastEl.addEventListener('hidden.bs.toast', function() {
        toastEl.remove();
    });
}

function displayOperationStats(operationStats, totalOperations, totalSum) {
    let statsHtml = `
        <div class="alert alert-info mt-3 border-0 shadow-sm">
            <h6 class="mb-3"><i class="fas fa-chart-pie me-2"></i><strong>Статистика по типам операций</strong></h6>
            <div class="row">
    `;
    
    // Отображаем статистику для каждого типа операции
    Object.entries(operationStats).forEach(([paymentType, stats]) => {
        statsHtml += `
            <div class="col-md-6 mb-2">
                <div class="d-flex justify-content-between align-items-center">
                    <span><i class="fas fa-money-bill-wave text-primary me-1"></i>${paymentType}:</span>
                    <span><span class="badge bg-primary">${stats.count}</span> <strong class="text-success">${stats.sum.toFixed(2)} ₽</strong></span>
                </div>
            </div>
        `;
    });
    
    statsHtml += `
            </div>
            <hr class="my-3">
            <div class="row">
                <div class="col-md-6">
                    <strong><i class="fas fa-list me-2"></i>Всего операций:</strong> <span class="badge bg-dark">${totalOperations}</span>
                </div>
                <div class="col-md-6 text-md-end">
                    <strong><i class="fas fa-ruble-sign me-2"></i>Общая сумма:</strong> 
                    <span class="text-success fw-bold fs-5">${totalSum.toFixed(2)} ₽</span>
                </div>
            </div>
            <hr class="my-3">
            <div class="text-center">
                <button class="btn btn-info" onclick="openOperationsModal()">
                    <i class="fas fa-list-alt me-2"></i>Детальный отчет по операциям
                </button>
            </div>
        </div>
    `;
    
    // Добавляем статистику в информационный блок
    $('#cashShiftInfo').append(statsHtml);
}

function createOperationsTable(operations) {
    if (!operations || operations.length === 0) {
        return;
    }
    
    // Очищаем tbody
    $('#operationsTableBody').empty();
    
    // Сортируем операции по дате (новые сверху)
    const sortedOperations = operations.sort((a, b) => {
        const dateA = new Date(a.date || a.creationDate || '');
        const dateB = new Date(b.date || b.creationDate || '');
        return dateB - dateA;
    });
    
    let rowsHtml = '';
    sortedOperations.forEach((operation, index) => {
        // Форматируем дату
        let formattedDate = '';
        try {
            const dateValue = operation.date || operation.creationDate || '';
            if (dateValue) {
                const date = new Date(dateValue);
                formattedDate = date.toLocaleString('ru-RU', {
                    year: 'numeric',
                    month: '2-digit',
                    day: '2-digit',
                    hour: '2-digit',
                    minute: '2-digit'
                });
            }
        } catch (e) {
            formattedDate = operation.date || operation.creationDate || '';
        }
        
        // Определяем тип операции
        const operationType = operation.operationType || 'unknown';
        let operationTypeText = '';
        let operationTypeClass = '';
        
        switch (operationType) {
            case 'cashless':
                operationTypeText = '<i class="fas fa-credit-card me-1"></i>Безналичный';
                operationTypeClass = 'badge bg-primary';
                break;
            case 'payin':
                operationTypeText = '<i class="fas fa-arrow-down me-1"></i>Внесение';
                operationTypeClass = 'badge bg-success';
                break;
            case 'payout':
                operationTypeText = '<i class="fas fa-arrow-up me-1"></i>Выдача';
                operationTypeClass = 'badge bg-warning text-dark';
                break;
            default:
                operationTypeText = 'Неизвестно';
                operationTypeClass = 'badge bg-secondary';
        }
        
        // Форматируем сумму
        const amount = parseFloat(operation.actualSum || 0);
        const formattedAmount = amount.toFixed(2) + ' ₽';
        
        // Определяем статус
        const status = operation.status || 'unknown';
        let statusText = '';
        let statusClass = '';
        
        switch (status) {
            case 'SUCCESS':
            case 'COMPLETED':
                statusText = '<i class="fas fa-check-circle me-1"></i>Успешно';
                statusClass = 'badge bg-success';
                break;
            case 'FAILED':
            case 'ERROR':
                statusText = '<i class="fas fa-times-circle me-1"></i>Ошибка';
                statusClass = 'badge bg-danger';
                break;
            case 'PENDING':
                statusText = '<i class="fas fa-clock me-1"></i>В обработке';
                statusClass = 'badge bg-warning text-dark';
                break;
            default:
                statusText = 'Неизвестно';
                statusClass = 'badge bg-secondary';
        }
        
        rowsHtml += `
            <tr class="animate-row">
                <td><small class="text-muted">${formattedDate}</small></td>
                <td><span class="${operationTypeClass}">${operationTypeText}</span></td>
                <td>${operation.paymentTypeName || 'Не указан'}</td>
                <td class="text-end"><strong class="text-primary">${formattedAmount}</strong></td>
                <td><span class="${statusClass}">${statusText}</span></td>
                <td><small class="text-muted">${operation.comment || '-'}</small></td>
            </tr>
        `;
    });
    
    // Добавляем строки в таблицу
    $('#operationsTableBody').html(rowsHtml);
    $('#operationsTableContainer').fadeIn('slow');
}

// Функция для открытия модального окна с детальным отчетом
function openOperationsModal() {
    if (!cashShiftData) {
        showError('Нет данных об операциях для отображения');
        return;
    }
    
    const operations = Array.isArray(cashShiftData) ? cashShiftData : cashShiftData.operations;
    
    // Вычисляем общую сумму из операций
    const totalSum = operations.reduce((sum, op) => sum + parseFloat(op.actualSum || 0), 0);
    
    // Заполняем общую информацию
    $('#totalOperations').text(operations.length);
    $('#totalAmount').text(totalSum.toFixed(2) + ' ₽');
    
    // Заполняем период смены
    if (typeof cashShiftData === 'object' && cashShiftData.shiftInfo) {
        const openDate = new Date(cashShiftData.shiftInfo.openDate);
        const closeDate = new Date(cashShiftData.shiftInfo.closeDate);
        const period = `${openDate.toLocaleString('ru-RU')} - ${closeDate.toLocaleString('ru-RU')}`;
        $('#shiftPeriod').text(period);
    } else {
        $('#shiftPeriod').text('Период не указан');
    }
    
    // Заполняем статистику по типам
    const typeStats = {};
    operations.forEach(op => {
        const type = op.paymentTypeName || 'Неизвестно';
        if (!typeStats[type]) {
            typeStats[type] = { count: 0, sum: 0 };
        }
        typeStats[type].count++;
        typeStats[type].sum += parseFloat(op.actualSum || 0);
    });
    
    let typeStatsHtml = '';
    Object.entries(typeStats).forEach(([type, stats]) => {
        typeStatsHtml += `
            <div class="d-flex justify-content-between mb-2">
                <strong>${type}:</strong>
                <span><span class="badge bg-secondary">${stats.count}</span> <strong class="text-success">${stats.sum.toFixed(2)} ₽</strong></span>
            </div>
        `;
    });
    $('#typeStatistics').html(typeStatsHtml);
    
    // Заполняем таблицу операций (аналогично createOperationsTable но для модального окна)
    let tableRowsHtml = '';
    operations.forEach((operation, index) => {
        let formattedDate = '';
        try {
            const dateValue = operation.date || operation.creationDate || '';
            if (dateValue) {
                const date = new Date(dateValue);
                formattedDate = date.toLocaleString('ru-RU');
            }
        } catch (e) {
            formattedDate = operation.date || operation.creationDate || '';
        }
        
        const operationType = operation.operationType || 'unknown';
        let operationTypeText = '';
        let operationTypeClass = '';
        
        switch (operationType) {
            case 'cashless':
                operationTypeText = 'Безналичный';
                operationTypeClass = 'badge bg-primary';
                break;
            case 'payin':
                operationTypeText = 'Внесение';
                operationTypeClass = 'badge bg-success';
                break;
            case 'payout':
                operationTypeText = 'Выдача';
                operationTypeClass = 'badge bg-warning text-dark';
                break;
            default:
                operationTypeText = 'Неизвестно';
                operationTypeClass = 'badge bg-secondary';
        }
        
        const amount = parseFloat(operation.actualSum || 0);
        const formattedAmount = amount.toFixed(2) + ' ₽';
        
        const status = operation.status || 'unknown';
        let statusText = '';
        let statusClass = '';
        
        switch (status) {
            case 'SUCCESS':
            case 'COMPLETED':
                statusText = 'Успешно';
                statusClass = 'badge bg-success';
                break;
            case 'FAILED':
            case 'ERROR':
                statusText = 'Ошибка';
                statusClass = 'badge bg-danger';
                break;
            case 'PENDING':
                statusText = 'В обработке';
                statusClass = 'badge bg-warning text-dark';
                break;
            default:
                statusText = 'Неизвестно';
                statusClass = 'badge bg-secondary';
        }
        
        tableRowsHtml += `
            <tr>
                <td>${index + 1}</td>
                <td><small>${formattedDate}</small></td>
                <td><span class="${operationTypeClass}">${operationTypeText}</span></td>
                <td>${operation.paymentTypeName || 'Не указан'}</td>
                <td class="text-end"><strong>${formattedAmount}</strong></td>
                <td><span class="${statusClass}">${statusText}</span></td>
                <td><small class="text-muted">${operation.comment || '-'}</small></td>
            </tr>
        `;
    });
    
    $('#operationsDetailTableBody').html(tableRowsHtml);
    
    // Показываем модальное окно
    $('#operationsModal').modal('show');
}

// Обработчик для экспорта в Excel
$(document).on('click', '#exportOperationsBtn', function() {
    if (!cashShiftData) {
        showError('Нет данных для экспорта');
        return;
    }
    
    const operations = Array.isArray(cashShiftData) ? cashShiftData : cashShiftData.operations;
    
    if (!operations || operations.length === 0) {
        showError('Нет операций для экспорта');
        return;
    }
    
    // Создаем CSV данные
    let csvContent = '№,Дата и время,Тип операции,Способ оплаты,Сумма,Статус,Комментарий\n';
    
    operations.forEach((operation, index) => {
        let formattedDate = '';
        try {
            const dateValue = operation.date || operation.creationDate || '';
            if (dateValue) {
                const date = new Date(dateValue);
                formattedDate = date.toLocaleString('ru-RU');
            }
        } catch (e) {
            formattedDate = operation.date || operation.creationDate || '';
        }
        
        const operationType = operation.operationType || 'unknown';
        let operationTypeText = '';
        switch (operationType) {
            case 'cashless': operationTypeText = 'Безналичный'; break;
            case 'payin': operationTypeText = 'Внесение'; break;
            case 'payout': operationTypeText = 'Выдача'; break;
            default: operationTypeText = 'Неизвестно';
        }
        
        const amount = parseFloat(operation.actualSum || 0);
        const status = operation.status || 'unknown';
        let statusText = '';
        switch (status) {
            case 'SUCCESS':
            case 'COMPLETED': statusText = 'Успешно'; break;
            case 'FAILED':
            case 'ERROR': statusText = 'Ошибка'; break;
            case 'PENDING': statusText = 'В обработке'; break;
            default: statusText = 'Неизвестно';
        }
        
        csvContent += `${index + 1},"${formattedDate}","${operationTypeText}","${operation.paymentTypeName || 'Не указан'}","${amount.toFixed(2)} ₽","${statusText}","${operation.comment || ''}"\n`;
    });
    
    // Создаем и скачиваем файл
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `operations_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    showSuccess('Экспорт завершен');
});
