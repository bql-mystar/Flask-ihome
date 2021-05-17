function showSuccessMsg() {
    $('.popup_con').fadeIn('fast', function() {
        setTimeout(function(){
            $('.popup_con').fadeOut('fast',function(){}); 
        },1000) 
    });
}

function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

$(document).ready(function () {
    $('#form-avatar').submit(function (e) {
        // 阻止表单的默认行为
        e.preventDefault();
        // 利用jquery.form.min.js提供的ajaxSubmit对表单进行异步提交
        $(this).ajaxSubmit({
            url: '/api/v1.0/users/avatar',
            type: 'post',
            dataType: 'json',
            headers: {
                'X-CSRFToken': getCookie('csrf_token')
            },
            success: function (data) {
                if(data.errno == '0'){
                    // 上传成功
                    avatarUrl = data.data.avatar_url;
                    $('#user-avatar').attr('src', avatarUrl);
                }else{
                    alert(data.errmsg);
                }
            }
        })
    })
    $('#form-name').submit(function (e) {
        // 阻止提交的默认行为
        e.preventDefault();
        // 获取参数
        var name = $('#form-name #user-name').val()
        if (!name){
            alert('请输入用户名！');
            return;
        }
        var param = {
            'name': name
        };
        param = JSON.stringify(param)
        $.ajax({
            url: '/api/v1.0/users/name',
            type: 'put',
            data: param,
            contentType: 'application/json',
            dataType: "json",
            headers: {
                'X-CSRFToken': getCookie('csrf_token')
            },
            success: function (data) {
                if (data.errno == '0'){
                    $('.error-msg').hide();
                    showSuccessMsg();
                }else if (data.errno == '4001'){
                    $('.error-msg').show();
                }else if (data.errno == '4101'){
                    // errno为4101，也就是未登录
                    location.href = '/login.html';
                }
            }
        })

    })
})

