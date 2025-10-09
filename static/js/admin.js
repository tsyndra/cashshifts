$(document).ready(function() {
    // Обработчики событий
    $('#saveUserBtn').on('click', saveUser);
    $('.toggle-user').on('click', toggleUser);
    $('.change-password').on('click', showChangePasswordModal);
    $('#savePasswordBtn').on('click', changePassword);
    $('.delete-user').on('click', deleteUser);
});

function saveUser() {
    const username = $('#username').val();
    const email = $('#email').val();
    const password = $('#password').val();
    const is_admin = $('#is_admin').is(':checked');
    
    // Собираем выбранные филиалы
    const branches = [];
    $('.branch-checkbox:checked').each(function() {
        branches.push({
            id: $(this).val(),
            name: $(this).data('branch-name')
        });
    });
    
    if (!username || !password) {
        alert('Заполните обязательные поля');
        return;
    }
    
    $.ajax({
        url: '/admin/users/add',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            username: username,
            email: email,
            password: password,
            is_admin: is_admin,
            branches: branches
        }),
        success: function(response) {
            alert(response.message);
            location.reload();
        },
        error: function(xhr) {
            alert('Ошибка: ' + (xhr.responseJSON?.error || 'Неизвестная ошибка'));
        }
    });
}

function toggleUser() {
    const userId = $(this).data('user-id');
    
    if (!confirm('Вы уверены, что хотите изменить статус этого пользователя?')) {
        return;
    }
    
    $.ajax({
        url: `/admin/users/${userId}/toggle`,
        method: 'POST',
        success: function(response) {
            location.reload();
        },
        error: function(xhr) {
            alert('Ошибка: ' + (xhr.responseJSON?.error || 'Неизвестная ошибка'));
        }
    });
}

function showChangePasswordModal() {
    const userId = $(this).data('user-id');
    $('#changePasswordUserId').val(userId);
    $('#newPassword').val('');
    $('#changePasswordModal').modal('show');
}

function changePassword() {
    const userId = $('#changePasswordUserId').val();
    const newPassword = $('#newPassword').val();
    
    if (!newPassword) {
        alert('Введите новый пароль');
        return;
    }
    
    $.ajax({
        url: `/admin/users/${userId}/change-password`,
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            password: newPassword
        }),
        success: function(response) {
            alert(response.message);
            $('#changePasswordModal').modal('hide');
        },
        error: function(xhr) {
            alert('Ошибка: ' + (xhr.responseJSON?.error || 'Неизвестная ошибка'));
        }
    });
}

function deleteUser() {
    const userId = $(this).data('user-id');
    
    if (!confirm('Вы уверены, что хотите удалить этого пользователя? Это действие нельзя отменить.')) {
        return;
    }
    
    $.ajax({
        url: `/admin/users/${userId}/delete`,
        method: 'DELETE',
        success: function(response) {
            alert(response.message);
            location.reload();
        },
        error: function(xhr) {
            alert('Ошибка: ' + (xhr.responseJSON?.error || 'Неизвестная ошибка'));
        }
    });
}

