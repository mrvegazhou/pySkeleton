/**
 * Created by vega on 16/1/17.
 */
var xsrf = getCookie("_xsrf");
//显示上传照片
function showPhotoView(obj) {
    var photo = $('.ScrollableArea');
    var arrow = $(obj);
    if(photo.css('display')=='none') {
        photo.show();
        arrow.html('<i class="fa fa-angle-double-up"></i>');
    } else {
        photo.hide();
        arrow.html('<i class="fa fa-angle-double-down"></i>');
    }
}
//展示 隐藏层
function showDiv(obj) {
    var open_div = $(obj).siblings('.isOpen');
    var obj_pos = $(obj).position();
	open_div.find('ul').css({"position":"position", "left": parseInt(obj_pos.left)+'px'});
	open_div.toggle();
    $(document).one("click", function () {
		open_div.hide();
	});
	event.stopPropagation();
}

//展示每个newsfeed的删除提示
function showDelOp()
{
    $('.feed-list > li').hover(function(){
        $(this).find('.del').show();
    },function(){
        $(this).find('.del').hide();
    });
}

//发表newsfeed图片删除
function showDeleteDiv(obj, id)
{
    var temp_obj = $(obj);
	var divObj = $("<div onmouseout='divOnmouseout(\""+id+"\");'><a href='javascript:;' onclick='delImg(this,\""+id+"\");'><i class='fa fa-remove' style='padding:5px;color:red;float:right;clear: both;'></i></a></div>");
	divObj.addClass("divX");
    var pos = temp_obj.position();
	divObj.attr("id", id+"-DIV-DEL");
	divObj.css({"position":"absolute", "left": pos.left, "top":pos.top});
	temp_obj.parent().append(divObj);
}
function divOnmouseout(resourceCode){
	$("#"+resourceCode+"-DIV-DEL").detach();
}
//删除feed图片
function delImg(obj, id) {
    var args = {"_xsrf": getCookie("_xsrf"), 'id': id};
    $.postJSON("/ucenter/delFeedImg", args, function(response) {
        if( response.code=='success' ){
            var temp_obj = $(obj);
            temp_obj.parent().parent().remove();
        }
	});
}
//删除feed news
function delNewsFeedItem(id) {
    var args = {"_xsrf": getCookie("_xsrf"), 'id': id};
    $.postJSON("/ucenter/delNewsfeed", args, function(response) {
        if( response.code=='success' ){
            $("#feed-item-"+id).remove();
        }
	});
}
//列表排序
function sortList(order_by) {
    var args = {"_xsrf": getCookie("_xsrf"), 'order_by': order_by};
    var feed_list = $('.feed-list');
    $.postJSON("/ucenter/sortNewsFeed", args, function(response) {
        if( response.code=='success' ){
            var str_tmp = '';
            feed_list.html('');
            feed_list.html('<img id="loading" src="/static/img/loading.gif">');
            $.each(response.res, function (i, val) {
                var img_str = '';
                if( val.img_urls ) {
                    img_str += '<div class="feed-list-img">';
                    $.each(val.img_urls, function (idx, img) {
                        img_str += '<img src="/ucenter/feedimg/'+img+'" />';
                    });
                    img_str += '</div>';
                }
                var html = '<li id="feed-item-'+val.id+'">'+
                                '<p>' +
                                    '<span class="feed-content">'+val.content+'</span>' +img_str+
                                '</p>'+
                                '<div>'+
                                    '<span class="time-from">'+val.create_time+'来自 '+val.from_source+'</span>'+
                                    '<span class="is-open">'+val.is_open+'可见</span>'+
                                    '<span><a href="javascript:;" onclick="delNewsFeedItem('+val.id+');" class="del">删除</a></span>'+
                                '</div>'+
                            '</li>';
                str_tmp += html;
            });
            $('#loading').remove();
            feed_list.html(str_tmp);
            showDelOp();
            delete str_tmp;
        }
	});
}

//滚动到‘查看更多’判断
msg_list_loading = false;
$(function(){
    var last_item = $(".show-more-items");
    var show_more_offset_top = last_item.offset().top;
    var doc_offset_top = $(document).height();
    var distance = doc_offset_top - show_more_offset_top;
    var page = parseInt($("#more-page").html());
    if( last_item.length>0 ) {
        $(window).scroll(function(){
            if( !msg_list_loading ){
                if( (($(window).scrollTop() + $(window).height()) + distance) >= $(document).height() ){
                    msg_list_loading = true;
                    getAjaxList(page);
                }
            }
        });
    }
});
//点击更多
function getMoreList()
{
    getAjaxList(parseInt($("#more-page").html()));
}

function getAjaxList(page)
{
    var last_item = $(".show-more-items");
    last_item.html('<img src="/static/img/loading.gif">');
    var args = {"_xsrf": xsrf, 'page': page+1};
    $.postJSON("/ucenter/getMoreItems", args, function(response) {
        if( response.code=='success' ){
            if( (response.res).length>0 )
            {
                var str = "";
                $.each(response.res, function (i, val) {
                    str += '<li id="feed-item-' + val.id + '">' +
                            '<p>' + val.content + '</p>' +
                            '<div>' +
                            '<span class="time-from">' + val.create_time + '来自 ' + val.from_source + '</span>' +
                            '<span class="is-open">'+val.is_open+'可见</span>'+
                            '<span><a href="javascript:;" onclick="delFeedNewsItem(' + val.id + ');" class="del">删除</a></span>' +
                            '</div>' +
                            '</li>';
                });
                $(".feed-list").append(str);
                page += 1;
                $("#more-page").html(page);
            }
            last_item.remove();
        } else {
            last_item.remove();
        }
    });
}

$("#conBox").limitTextarea({
    maxNumber:140,     //最大字数
    position:'.maxNum'
});

//上传图片
$('.upload_img').uploadFile({
    url: '/ucenter/uploadImg',
    dataType: 'json',
    fileName: 'feed_img',
    allowedTypes: 'image/*',
    extFilter: 'jpg;png;gif',
    extraData: {"_xsrf": xsrf},
    onBeforeUpload: function(id){
        var max_count = $('#feed-container').children('.section').length;
        if( max_count>12 ){
            slowOutMsg('danger', '图片数量已经超出');
            return false;
        }
        $.uploadFileExt.addFile('#feed-container', '#feed-container', 'upload-feed-img');
    },
    onUploadProgress: function(id, percent){
        var percentStr = percent + '%';
        $.uploadFileExt.updateFileProgress(id, percentStr, '.upload-feed-img');
    },
    onUploadSuccess: function(id, data, file){
        var feed_container = $('#feed-container');
        //添加展示图片
        var new_img = '<div class="section">'+
                        '<img width="100px" data-id='+data.res.id+' height="100px" id="img-'+data.res.id+'" src="" onmouseover="showDeleteDiv(this, \''+data.res.id+'\');"/>'+
                      '</div>';
        feed_container.prepend(new_img);
        var img = $('#img-'+data.res.id);
        if(typeof FileReader !== "undefined"){
            var reader = new FileReader();
            reader.onload = function (e) {
              img.attr('src', e.target.result);
            }
            reader.readAsDataURL(file);
        } else {
            img.attr('src', data.res.url);
        }
        $.uploadFileExt.updateFileProgress(id, '100%', '.upload-feed-img');
        $('.upload-feed-img').fadeOut(2000);
        var img_count = parseInt(feed_container.attr('file-counter'));
        if( img_count>6 )
        {
            feed_container.css("overflow-x", "hidden");
            feed_container.css("overflow-y", "auto");
        }
        var imgs = $('input[name="newsfeed_img_urls"]').val();
        imgs = (imgs!='') ? imgs+','+data.res.filename : data.res.filename;
        $('input[name="newsfeed_img_urls"]').val(imgs);
    },
    onUploadError: function(id, message){
        slowOutMsg('danger', message);
    },
    onFileTypeError: function(file){
        var msg = '请上传正确的图片格式！';
        slowOutMsg('danger', msg);
    },
    onFileSizeError: function(file){
        slowOutMsg('danger', file.name + '超出规定大小');
    },
    onFallbackMode: function(message){
        slowOutMsg('danger', '浏览器不支持 ' + message);
    }
});

//是否公开Newsfeed
function isOpenNewsfeed(code) {
    var temp = 1;
    var public_content = '公开';
    switch(code) {
        case 1:
            temp = 1;
            public_content = '朋友';
            break;
        case 2:
            temp = 2;
            public_content = '仅自己';
            break;
        case 3:
            temp = 3;
            public_content = '朋友';
            break;
        case 4:
            temp = 4;
            public_content = '群组';
            break;
        default:
            temp = 1;
            public_content = '公开';
            break;
    }
    $('input[name="isopen"]').val(temp);
    $('#public_content').html(public_content);
}

//清空内容和图片
function clearContents()
{
    $("#conBox").val('');
    $('#feed-container').find('.section').each(function(){
        $(this).remove();
    });
    $('input[name="newsfeed_img_urls"]').val('');
    $("input[name='newsfeed_activity_ids']").val('');
    $("input[name='isopen']").val(1);
    $(".isPublic").html('<span id="public_content">公开</span>');
}

//发表状态
function publicNewsFeedSubmit()
{
    $('#public-newsfeed-form').formValidate(
        [
            {id: 'conBox', rules: 'required', display: '状态内容'},
        ],
        function(errors){
            if(errors.length==0) {
                $.ajax({
                    type: "POST",
                    url: '/ucenter/public',
                    data: $('#public-newsfeed-form').serialize(),
                    dataType:"json",
                    success: function(data) {
                        if( data.code=='success' ) {
                            showNewsFeedItem(data.res);
                            clearContents();
                        } else {
                            slowOutMsg('danger', data.msg);
                        }
                        $('a.imgZoom').imgZoom();
                    },
                    error: function(XMLHttpRequest, textStatus, errorThrown) {
                        slowOutMsg('danger', errorThrown);
                    }
                });
            } else {
                var str = '';
                $.each(errors, function(i,val){
                    str += val.error+',';
                });
                str = str.substring(0, str.length-1);
                slowOutMsg('danger', str);
            }
         },
        {showMsg: true}
    );
}
//发布成功生成状态列表
function showNewsFeedItem( item ) {
    var item_str =  '<li id="feed-item-'+item['id']+'">' +
                        '<p>'+item['content']+'</p>' +
                        '<div>' +
                            '<span class="time-from">'+item['create_time']+' 来自 '+item['from_source']+'</span>' +
                            '<a href="javascrip:;" onclick="delFeedNewsItem(this, '+item['id']+');" class="del">删除</a>' +
                        '</div>' +
                    '</li>';
    $('.feed-list').prepend(item_str);
}

//获取客户端当前的请求的坐标
var l_x = 116.38075;
var l_y = 39.918986;
//获取用户的坐标
$(function(){
    $.postJSON("/ucenter/mapLocation", {"_xsrf": getCookie("_xsrf")}, function(response) {
        if( response.code=='success' ){
            l_x = response.res.content.point.x;
            l_y = response.res.content.point.y;
        }
    });
});
//检索百度地图
function selectMapAddr() {
    var addr = document.getElementById("select_map_addr").value;
    document.getElementById("map_res_str").innerHTML = addr;
}
//textarea插入内容，并计算剩余字数
var insertContnet = function(str, type) {
    if($.trim(str)=='') {
        return false;
    }
    switch(type) {
        case 'map':
            plus = 2;
            str = '[@'+str+'@]';
            break;
        case 'emotion':
            str = '';
            plus = 1;
            break;
        case 'event':
            str = '[#'+str+'#]';
            plus = 2;
            break;
        default :
            plus = 0;
            break;
    }
    $('.maxNum').html(parseInt($('.maxNum').html())-plus);
    if(str!='') {
        var content = $('#conBox').val();
        $('#conBox').val(content+str);
    }
    return true;
}
$('.map-marker').click(function(){
    //生成弹出框
    var opts = {'title':'地图标注', 'width': '700px', 'height': 'auto', 'is_showbg':false, 'zindex':999, 'btn_ok_text':'确认', 'btn_cancel_text': '', 'id': 'ucenter-map-marker'};
    var map_str = '<div id="ucenter-map-marker-content"></div>'+
                   '<div class="map-input-cls">' +
                        '<div id="r-result">' +
                            '位置关键词:<input type="text" id="suggestId" size="30" value="北京" style="width:200px;" />' +
                            '<span style="margin:0px 5px;font-size:13px;color:#0A8021">指定地址信息:</span><span id="map_res_str"></span>' +
                        '</div>'+
	                    '<div id="searchResultPanel" style="border:1px solid #C0C0C0;width:150px;height:auto; display:none;"></div>' +
                    '</div>';
    opts.content = map_str;
    var d = new Dialog(opts);
    d.init();
    $('#ucenter-map-marker .content').css({'padding':'0px'});
    var map = new BMap.Map("ucenter-map-marker-content");
    map.centerAndZoom(city, 12);
    map.addControl(new BMap.NavigationControl());
    var ac = new BMap.Autocomplete(    //建立一个自动完成的对象
		{"input" : "suggestId"
		,"location" : map
	});
    var mkr = new BMap.Marker(new BMap.Point(l_x, l_y), {enableDragging: true, raiseOnDrag: true});
    map.addOverlay(mkr);
    mkr.addEventListener('dragend', function(e){
        var myGeo = new BMap.Geocoder();
        var opts = {title : '<span style="font-size:13px;color:#0A8021">坐标附近地址信息:</span>'};
        // 根据坐标得到地址描述
        location_list_str = '<select style="width:200px;height:20px;" id="select_map_addr" onchange="selectMapAddr();"><option value="0">-请选择-</option>{options}</select>';
        options_str = '';
        myGeo.getLocation(e.point, function(result){
            if(result){
                if(result.surroundingPois.length>0) {
                   $.each(result.surroundingPois, function(key, item){
                        options_str += '<option value="'+item.address+'">'+item.address+'</option>';
                   });
                }
            }
            location_list_str = location_list_str.replace('{options}', options_str);
            var infoWindow =new BMap.InfoWindow(location_list_str, opts);
            document.getElementById("map_res_str").innerHTML = result.address;
            mkr.openInfoWindow(infoWindow);
            map.addOverlay(mkr);
        });
    });
    mkr.addEventListener('dragging', function(e){
        mkr.closeInfoWindow();
    });
    ac.addEventListener("onhighlight", function(e) {  //鼠标放在下拉列表上的事件
	    var str = "";
		var _value = e.fromitem.value;
		var value = "";
		if (e.fromitem.index > -1) {
			value = _value.province +  _value.city +  _value.district +  _value.street +  _value.business;
		}
		str = "FromItem<br />index = " + e.fromitem.index + "<br />value = " + value;
		value = "";
		if (e.toitem.index > -1) {
			_value = e.toitem.value;
			value = _value.province +  _value.city +  _value.district +  _value.street +  _value.business;
		}
		str += "<br />ToItem<br />index = " + e.toitem.index + "<br />value = " + value;
		document.getElementById("searchResultPanel").innerHTML = str;
	});
    var myValue;
	ac.addEventListener("onconfirm", function(e) {    //鼠标点击下拉列表后的事件
	    var _value = e.item.value;
		myValue = _value.province +  _value.city +  _value.district +  _value.street +  _value.business;
		document.getElementById("searchResultPanel").innerHTML ="onconfirm<br />index = " + e.item.index + "<br />myValue = " + myValue;

        map.clearOverlays();    //清除地图上所有覆盖物
        function myFun(){
            var pp = local.getResults().getPoi(0).point;    //获取第一个智能搜索的结果
            map.centerAndZoom(pp, 18);
            map.addOverlay(new BMap.Marker(pp));    //添加标注
        }
        var local = new BMap.LocalSearch(map, { //智能搜索
          onSearchComplete: myFun
        });
        local.search(myValue);
	});

    d.bind_func('ok', function(){
        insertContnet(document.getElementById("map_res_str").innerHTML, 'map');
        d.closed();
    });
});

//添加表情控件和newsfeed的删除提示
$(function (){
	$("a.smile-marker").facebox({
		Event : "click",	//触发事件
		textid : "conBox", //文本框 ID
		imgsrc: '/static/img/face/',
        imgs: faceimgs
	});
    showDelOp();
    //图片放大功能
    $('a.imgZoom').imgZoom();
});

//发布计划参加的活动
$('.event-marker').click(function(){
    var opts = {'title':'计划参加的活动',
                'width': '700px',
                'height': 'auto',
                'is_showbg':false,
                'zindex':999,
                'btn_ok_text':'确认',
                'btn_cancel_text': '',
                'footer_top': '0px',
                'id': 'ucenter-event-marker'};
    $.postJSON("/ucenter/userActs", {"_xsrf": getCookie("_xsrf")}, function(response) {
        if( response.code=='success' ){
            opts['content'] = response.res;
            var d = new Dialog(opts);
            d.init();
            d.bind_func('ok', function(){
                var activity_ids = '';
                $('#ucenter-chk-act-list').find("input[name^='act_']:checked").each(function(idx, node){
                    var str = $(this).parent('td').next().find('a').html();
                    insertContnet(str, 'event');
                    activity_ids += $(node).val()+',';
                });
                //存储事件活动的id到隐藏域
                var newsfeed_activity_ids = $("input[name='newsfeed_activity_ids']").val();
                newsfeed_activity_ids!='' ? newsfeed_activity_ids+',' : '';
                $("input[name='newsfeed_activity_ids']").val(newsfeed_activity_ids+activity_ids.substring(0, activity_ids.length-1));
                d.closed();
            });
            delete d;
            delete activity_ids;
        } else {
            slowOutMsg('warning', response.msg);
        }
	});
});

//在发表说说的文字内触发地图
function showMapByAddr( addr )
{
    //生成弹出框
    var opts = {'title':'地图标注', 'footer_top': '0px', 'width': '700px', 'height': 'auto', 'is_showbg':false, 'zindex':0, 'btn_ok_text':'确认', 'btn_cancel_text': '', 'id': 'ucenter-map-marker'};
    var map_str = '<div id="ucenter-map-marker-content"></div>';
    opts.content = map_str;
    var d = new Dialog(opts);
    d.init();
    d.bind_func('ok', function(){d.closed();});

    $('#ucenter-map-marker .content').css({'padding':'0px'});
    var map = new BMap.Map("ucenter-map-marker-content");
	//map.centerAndZoom(point, 12);
	// 创建地址解析器实例
	var myGeo = new BMap.Geocoder();
	// 将地址解析结果显示在地图上,并调整地图视野
	myGeo.getPoint('"'+addr+'"', function(point){
		if (point) {
			map.centerAndZoom(point, 16);
			map.addOverlay(new BMap.Marker(point));
		}else{
            slowOutMsg('danger', '您选择地址没有解析到结果!');
		}
	}, "");
}