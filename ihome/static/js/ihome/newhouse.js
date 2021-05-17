function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

$(document).ready(function() {
    // $('.popup_con').fadeIn('fast');
    // $('.popup_con').fadeOut('fast');
    $.get('/api/v1.0/areas', function (data) {
        if (data.errno == '0') {
            // 获取接收到的地区信息
            var areas = data.data;
            // for (i=0;i<areas.length;i++){
            //     var area = areas[i];
            //     var area_info = '<option value="' + area.aid + '">' + area.aname + '</option>';
            //     $('#area-id').append(area_info);
            // }
            // 使用js模板
            var html = template('area-template', {areas: areas});
            $('#area-id').html(html);
        } else {
            alert(data.errmsg);
        }
    });
    $('#form-house-info').submit(function (e) {
        e.preventDefault();
        // 处理表单数据
        var data = {};
        $('#form-house-info').serializeArray().map(function (x) {
            data[x.name] = x.value;
        });
        // 收拾设置id信息
        var facility = [];
        $(':checked[name="facility"]').each(function (index, x) {
            facility[index] = $(x).val();
        });
        data.facility = facility;
        // 直接跳过数据判空操作
        // 向后端发送请求
        $.ajax({
            url: '/api/v1.0/houses/info',
            type: 'post',
            contentType: 'application/json',
            data: JSON.stringify(data),
            dataType: 'json',
            headers: {
                'X-CSRFToken': getCookie('csrf_token')
            },
            success: function (data) {
                if (data.errno == '4101') {
                    // 用户未登录
                    location.href = '/login.html';
                } else if (data.errno == '0') {
                    // 隐藏基本信息表单
                    $('#form-house-info').hide();
                    // 显示图片表单
                    $('#form-house-image').show();
                    // 设置图片表单中的house_id
                    var house_id = data.data.house_id;
                    $('#house-id').val(house_id);
                } else {
                    alert(data.errmsg)
                }
            }

        });
    });
    $('#form-house-image').submit(function (e) {
        e.preventDefault();
        $('#form-house-image').ajaxSubmit({
            url: '/api/v1.0/houses/image',
            type: 'post',
            dataType: 'json',
            headers: {
                'X-CSRFToken': getCookie('csrf_token')
            },
            success: function (data) {
                if (data.errno == '4101') {
                    location.href = '/login.html'
                } else if (data.errno == '0') {
                    img_html = '<img src="' + data.data.image_url + '">';
                    $('.house-image-cons').append(img_html);
                } else {
                    alert(data.errmsg);
                }

            }
        })
    })
})