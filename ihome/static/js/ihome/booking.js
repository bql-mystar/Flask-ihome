function hrefBack() {
    history.go(-1);
}

function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

function decodeQuery(){
    var search = decodeURI(document.location.search);
    return search.replace(/(^\?)/, '').split('&').reduce(function(result, item){
        values = item.split('=');
        result[values[0]] = values[1];
        return result;
    }, {});
}

function showErrorMsg() {
    $('.popup_con').fadeIn('fast', function() {
        setTimeout(function(){
            $('.popup_con').fadeOut('fast',function(){}); 
        },1000) 
    });
}

$(document).ready(function(){
    var queryData = decodeQuery();
    var houseId = queryData['hid'];

    $(".input-daterange").datepicker({
        format: "yyyy-mm-dd",
        startDate: "today",
        language: "zh-CN",
        autoclose: true
    });
    $(".input-daterange").on("changeDate", function(){
        var startDate = $("#start-date").val();
        var endDate = $("#end-date").val();

        if (startDate && endDate && startDate > endDate) {
            showErrorMsg();
        } else {
            var sd = new Date(startDate);
            var ed = new Date(endDate);
            days = (ed - sd)/(1000*3600*24) + 1;
            var price = $(".house-text>p>span").html();
            var amount = days * parseFloat(price);
            $(".order-amount>span").html(amount.toFixed(2) + "(共"+ days +"晚)");
        }
    });
    // 提交订单
    $('.submit-btn').on('click', function (e) {
        if ($('.order-amount>span').html()){
            $(this).prop('disabled', true);
            var startDate = $('#start-date').val();
            var endDate = $('#end-date').val();
            var params = {
                'house_id': houseId,
                'start_date': startDate,
                'end_date': endDate
            };
            $.ajax({
                url: '/api/v1.0/orders',
                type: 'post',
                data: JSON.stringify(params),
                contentType: 'application/json',
                dataType: 'json',
                headers: {
                    'X-CSRFToken': getCookie('csrf_token')
                },
                success: function (data) {
                    if ("4101" == data.errno) {
                        location.href = "/login.html";
                    } else if ("4004" == data.errno) {
                        showErrorMsg("房间已被抢定，请重新选择日期！");
                    } else if ("0" == data.errno) {
                        location.href = "/orders.html";
                    }
                }
            })

        }
    })
})
