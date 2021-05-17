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
    // 查询用户的实名认证信息
    $.get('/api/v1.0/users/auth', function (data) {
        // 用户未登录
        if(data.errno == '4101'){
            location.href = 'login.html';
        }
        // 查询到用户的信息
        else if (data.errno == '0'){
            // 如果返回的数据中real_name和id_card均不为Null，表示用户填写实名信息
            if (data.data.real_name && data.data.id_card){
                $('#real-name').val(data.data.real_name);
                $('#id-card').val(data.data.id_card);
                // 给input添加isable属性，禁止用户修改
                $('#real-name').prop('disabled', true);
                $('#id-card').prop('disabled', true);
                // 隐藏提交保存按钮
                $('#form-auth>input[type="submit"]').hide();
            }
        }else{
            alert(data.errmsg);
        }
    }, 'json')

    // 管理实名信息表单的提交行为
    $('#form-auth').submit(function (e) {
        e.preventDefault();
        // 如果用户没填写完整，展示错误信息
        var realName = $('#real-name').val();
        var idCard = $('#id-card').val();
        if (realName == '' || !idCard == ''){
            $('.error-msg').show();
        }
        // 组织参数，并以转换为json字符串格式
        var params = {
            'real_name': realName,
            'id_card': idCard
        };
        params = JSON.stringify(params);
        $.ajax({
            url: '/api/v1.0/users/auth',
            type: 'post',
            data: params,
            contentType: 'application/json',
            dataType: 'json',
            headers: {
                'X-CSRFToken': getCookie('csrf_token')
            },
            success: function (data) {
                if (data.errno == '4101'){
                    location.href = '/login';
                }else if (data.errno == '0'){
                    $('.error-msg').hide();
                    // 显示保存成功信息
                    showSuccessMsg();
                    // 给input添加isable属性，禁止用户修改
                    $('#real-name').prop('disabled', true);
                    $('#id-card').prop('disabled', true);
                    // 隐藏提交保存按钮
                    $('#form-auth>input[type="submit"]').hide();
                }else{
                    alert(data.errmsg);
                }
            }
        })
    })
})

