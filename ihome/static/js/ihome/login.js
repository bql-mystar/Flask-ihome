function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

$(document).ready(function() {
    $("#mobile").focus(function(){
        $("#mobile-err").hide();
    });
    $("#password").focus(function(){
        $("#password-err").hide();
    });
    $(".form-login").submit(function(e){
        e.preventDefault();
        mobile = $("#mobile").val();
        passwd = $("#password").val();
        if (!mobile) {
            $("#mobile-err span").html("请填写正确的手机号！");
            $("#mobile-err").show();
            return;
        } 
        if (!passwd) {
            $("#password-err span").html("请填写密码!");
            $("#password-err").show();
            return;
        }
        // 组织参数
        var params = {
            'mobile': mobile,
            'password': passwd
        };
        // 将参数转换为json字符串
        var params = JSON.stringify(params);
        $.ajax({
            url: '/api/v1.0/sessions',
            type: 'post',
            data: params,
            contentType: 'application/json',
            dataType: 'json',
            headers: {
                'X-CSRFToken': getCookie('csrf_token')
            },
            success: function (data) {
                if (data.errno == '0'){
                    // 登录成功，跳转到主页
                    location.href = '/';
                }else{
                    // 其它的错误信息，在页面中展示
                    $('#password-err span').html(data.errmsg);
                    $('#password-err').show();
                }
            }
        })
    });
})