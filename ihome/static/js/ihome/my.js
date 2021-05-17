function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

// 点击退出按钮时执行的函数
function logout() {
    $.ajax({
        url: '/api/v1.0/sessions',
        type: 'delete',
        headers: {
            'X-CSRFToken': getCookie('csrf_token')
        },
        dataType: 'json',
        success: function (data) {
            if (data.errno == '0'){
                location.href = '/'
            }
        }
    })
}

$(document).ready(function(){
    $.get('/api/v1.0/users', function (data) {
        // 用户未登录
        if(data.errno == '4101'){
            location.href = 'login.html';
        }
        // 查询到用户的信息
        else if (data.errno == '0'){
            $('#user-name').html(data.data.name);
            $('#user-mobile').html(data.data.mobile);
            if (data.data.avatar){
                $('#user-avatar').attr('src', data.data.avatar);
            }
        }
    }, 'json')
})