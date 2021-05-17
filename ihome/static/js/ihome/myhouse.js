$(document).ready(function() {
    // $(".auth-warn").show();
    // 对于发布房源，只有认证后的用户才可以，所以要判断用户的实名认证状态
    $.get('/api/v1.0/users/auth', function (data) {
        // alert('发送ajax给/users/auth');
        if (data.errno == '4101') {
            location.href = '/login.html';
        } else if (data.errno == '0') {
            // 未认证的用户，在页面中展示'去认证'的按钮
            if (!(data.data.real_name && data.data.id_card)) {
                $('.auth-warn').show();
                return;
            }
            // 已认证的用户，请求其之前发布的房源信息
            $.get('/api/v1.0/users/houses', function (data) {
                // alert('发送ajax请求给/users/houses');
                // alert(data.errno);
                // alert(data.data.houses);
                if (data.errno == '0') {
                    // alert('程序进入==0');
                    $('#houses-list').html(template('houses-list-tmpl', {houses: data.data.houses}));
                } else {
                    $('#houses-list').html(template('houses-list-tmpl', {houses: []}));
                }
            })
        }


    })
})