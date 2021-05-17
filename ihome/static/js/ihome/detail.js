function hrefBack() {
    history.go(-1);
}

function decodeQuery(){
    var search = decodeURI(document.location.search);
    return search.replace(/(^\?)/, '').split('&').reduce(function(result, item){
        values = item.split('=');
        result[values[0]] = values[1];
        return result;
    }, {});
}

$(document).ready(function(){
    var queryData = decodeQuery();
    var houseId = queryData['id'];
    // alert(houseId);
    request_url = '/api/v1.0/houses/' + houseId;
    // alert(request_url);
    $.get(request_url, function (data) {
        // alert('发送ajax请求给/houses/6');
        if (data.errno == '0'){
            // alert('进入errno==0');
            $(".swiper-container").html(template("house-image-tmpl", {img_urls:data.data.house.img_urls, price:data.data.house.price}));
            $(".detail-con").html(template("house-detail-tmpl", {house:data.data.house}));
            // data.data.user_id为访问页面用户,data.data.house.user_id为房东
            if (data.data.user_id != data.data.house.user_id){
                $(".book-house").attr("href", "/booking.html?hid="+data.data.house.hid);
                $(".book-house").show();
            }
            var mySwiper = new Swiper ('.swiper-container', {
                loop: true,
                autoplay: 2000,
                autoplayDisableOnInteraction: false,
                pagination: '.swiper-pagination',
                paginationType: 'fraction'
            });
        }
        else {
            // alert(data.errmsg);
            alert('啥子也没有');
        }
    }, 'json');


    // $(".book-house").show();
});