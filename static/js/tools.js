//获取cookie
function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}
//弹出遮罩层
var Mask = function (options){
    var opts = $.extend(true, {}, Mask.defaults, options);
    this.opts = opts;
    this._closed = function(show_div_id){
        if( show_div_id==opts.show_div_id )
        {
            this._mask.remove();
        }
    };
    this._show = function(){
        //clientHeight是对象的可视部分高度；scrollHeight是对象的内容的高度；
        var ob_height = (document.documentElement.scrollHeight>document.documentElement.clientHeight) ? document.documentElement.scrollHeight : document.documentElement.clientHeight;
        var ob_width = (document.documentElement.scrollWidth>document.documentElement.clientWidth) ? document.documentElement.scrollWidth : document.documentElement.scrollWidth;
        var popup_div = $('<div></div>');
        popup_div.attr('id', 'bg_div');
        popup_div.css({     'background-color':opts.background,
                            'position':'absolute',
                            'left':0,
                            'top':0,
                            'display':'none',
                            'width':ob_width+'px',
                            'height':ob_height+'px',
                            'opacity':'0.5',
                            'filter': 'alpha(opacity=50);-moz-opacity: 0.5',
                            'z-index': opts.zindex
                           });
        popup_div.css({ 'display': "block" });
        //$("#" + opts.show_div_id ).css("top", "100px");
        $("#" + opts.show_div_id ).css("display", "block");
        $( "body" ).append(popup_div);
        if( opts.is_close )
        {
            $(popup_div).click(function() {$("#"+opts.show_div_id).remove(); $(popup_div).remove();});
        }
        this._mask = $(popup_div);
        return $(popup_div);
    };
};
Mask.defaults = {
    background: '#e3e3e3',
    show_div_id: '',
    is_close: true,
    zindex: 9999
};
///////////////////////////////建立弹出框////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
var Dialog = function(opts) {
    var that = this;
    this.dialog;
    this.btn_ok;
    this.btn_cancel;
    this._list = {};
    var isTouch = document.createTouch !== undefined;
    var _isIE6 = function() {
        return navigator.userAgent.match(/MSIE 6.0/)!= null;
    };
    var tpl = {
        iframe : '<iframe id="dialog-frame{rnd}" name="dialog-frame{rnd}" style="border:medium none;display:block;height:100%;width:100%;" frameborder="0" vspace="0" hspace="0" webkitAllowFullScreen mozallowfullscreen allowFullScreen' + (_isIE6() ? ' allowtransparency="true"' : '') + '></iframe>'
    };
    this.defaults = {
        id: '',
        width: '500px',//'100px',
        height: 'auto',//'200px',
        title: 'title',
        content: 'content',
        cancel: null,
        ok: null,
        btn_ok_text: '确定',
        btn_cancel_text: '取消',
        http: '',
        bar: true,
        close: true,
        drag: false,
        beforeshow: false,
        aftershow: false,
        delay_time: 0,
        builtin: true, //是否使用内置的弹出框
        zindex: 99,
        position: {x: 0, y: 0},
        is_resize: true,  // 默认情况下 随着窗口缩放而缩放
        is_scroll: true,
        is_move: true,
        opacity: 0.5,  //默认透明度
        background: '#e3e3e3',
        is_showbg: true, //是否显示遮罩层
        right_click: false,
        imgs: false,
        imgs_index: 1,
        footer_top: '30px',
    };
    this.opts = $.extend(true, {}, this.defaults, opts);
    this.id = this.opts.id=='' ? 'dialogDiv' : this.opts.id;
    var mask = new Mask({'show_div_id': this.id});
    //计算剧中
    this.center = function(obj) {
        var screen_width = $(window).width(), screen_height = $(window).height();  //当前浏览器窗口的 宽高
        var scroll_top = $(document).scrollTop(); //获取当前窗口距离页面顶部高度
        var scroll_left = $(document).scrollLeft();
        var obj_left = (screen_width - obj.width())/2 + scroll_left;
        var obj_top = (screen_height - obj.height())/2 + scroll_top;
        var zindex = this.opts.zindex;
        if(this.opts.is_showbg==true){
            zindex = parseInt(mask.opts.zindex)+1;
        }
        obj.css({'left': obj_left + 'px', 'top': obj_top + 'px','display': 'block', 'z-index':zindex});
        // 判断x,y位置默认是不是等于0 如是的话 居中 否则 根据传进来的位置重新定位
		if(0 === this.opts.position.x && 0 === this.opts.position.y)
        {
			obj.offset({'top':obj_top, 'left':obj_left});
		}
        else
        {
			obj.offset({'top':this.opts.position.y, 'left':this.opts.position.x});
		}
    };

    this.cal_wh  = function(obj) {
        that.center(obj);
        //浏览器窗口大小改变时
        $(window).unbind('resize');
        $(window).bind('resize',function(){
             t && clearTimeout(t);
             var t = setTimeout(function(){
                 if(that.opts.is_resize){
                     that.center(obj);
                 }
             },200);
         });
        //浏览器有滚动条时的操作
        /*$(window).unbind('scroll');
		$(window).bind('scroll',function(){
			t && clearTimeout(t);
			 var t = setTimeout(function(){
				 if(this.opts.is_scroll){
					 center(obj);
				 }
			 },200);
		});*/
    };
    this.closed = function() {
        if( that.opts.is_showbg )
        {
            mask._closed(that.id);
            delete mask;
        }
        try{that.dialog.remove();}catch(e){};
        $("#dialog-css-"+this.id).remove();
        delete that.dialog;
        delete that._list[that.id];
    };
    //判断content是否为对象
    this.content = function(obj, html) {
        $(obj).find('.content').empty('').html('<img src="/static/img/loading.gif" />');
        if( IsURL(html, '') )
        {
            var params = (arguments[2]==null) ? {} : arguments[2];
            tpl.iframe = $(tpl.iframe.replace(/\{rnd\}/g, new Date().getTime())).attr('src', html);
            $(obj).find('.content').empty('').html(tpl.iframe);
            $(obj).on('onreset', function() {
				try {
					$(this).find('iframe').hide().attr('src', '//about:blank').end().empty();
				} catch (e) {
                    $(obj).find('.content').empty('').html('<img src="/static/img/loading.gif" />');
                }
			});
        }
        else if( IsImg(html) )
        {

        }
        else
        {
            $(obj).find('.content').empty('')[typeof html === 'object' ? 'append' : 'html'](html);
        }
    };

    //加载css
    this.loadCss = function(width, height) {
        if(typeof(width)!='undefined' && width!='')
        {
            this.opts.width = width;
        }
        if(typeof(height)!='undefined' && height!='')
        {
            this.opts.height = height;
        }
        var margin_top = 'margin-top: '+this.opts.footer_top+';';
        if( parseInt(this.opts.height)<=50 )
        {
            margin_top = '';
        }
        $("head:eq(0)").append( "<style id='dialog-css-"+this.id+"'> \
             .dialogDiv {margin:auto; text-align:center; width: " + this.opts.width + "; padding: 0; word-break:break-all; word-wrap:break-word; min-width:200px;} \
             .dialogDiv .dialogBox {margin:0 auto; text-align:center; border:1px solid #d2d2d2;} \
             .dialogDiv .dialogBox .header {background:#4794c5; margin:2px 2px 0px 2px; height:26px; line-height:26px; text-align:left;} \
             .dialogDiv .dialogBox .header .header_left {float:left;} \
             .dialogDiv .dialogBox .header .header_right {float:right;} \
             .dialogDiv .dialogBox .header .header_right .close {margin: 0px 6px 0 0;} \
             .dialogDiv .dialogBox .header .header_right a {text-decoration: none; color:#336699; height:26px; line-height:26px; padding-right:5px;} \
             .dialogDiv .dialogBox .header h3 {font-size:14px; color:#ffffff; padding-left:5px; margin:0px; height: 26px; line-height: 26px;} \
             .dialogDiv .dialogBox .mid {height:"+ (parseInt(this.opts.height)+20) +";} \
             .dialogDiv .dialogBox .mid .content {font-size:12px; color:#6e6d6d; background:#ffffff; margin:0px auto 0 auto; vertical-align:middle; cursor:default; padding:15px 0 15px 0; height: " + this.opts.height + ";} \
             .dialogDiv .dialogBox .mid .footers {background:#ffffff; padding:9px; border-top: 1px solid #d2d2d2;" +margin_top+ "} \
             .dialogDiv .dialogBox .mid .footers a {background-color:rgb(71, 148, 197); color:#FFF; text-align:center; padding:3px 8px; margin:5px 8px; text-decoration:none; font-size:14px;} \
             </style>");
    };
    this.loadCss();

    //生成窗口
    this.created = function(refresh) {
        if(that._list[that.id] && refresh==false){
            return that._list[that.id];
        }
        var imgs = that.opts.imgs;
        if( imgs!=false )
        {
            var len = imgs.length;
            var img_div = '<div class="dialogImg" style="background-color: #FFFFFF;margin: 0 auto;position: absolute;height:'+this.opts.height+'; width:'+that.opts.width+'" id="'+that.id+'">'+
                                '<div id="img_container" style="padding:5px; line-height:0; text-align:center;">'+
                                  '<img id="img_dialog" src="/static/res/imgs/' +imgs[that.opts.imgs_index-1]+ '" />'+
                                '</div>'+
                                '<div id="img_nav" style="text-align: center;height: 20px; line-height: 20px;width:100%;">' +
                                    '<div style="overflow:hidden; display:inline-block;"> '+
                                        '<div style="padding:0 20px;float:left;"><a class="prev" href="javascript:;" style="text-decoration: none;" ><-</a></div>'+
                                        '<div style="padding:0 20px;float:left;"><span class="num">' +that.opts.imgs_index+ '</span>/'+len+'</div>'+
                                        '<div style="padding:0 20px;float:left;"><a class="next" href="javascript:;" style="text-decoration: none;">-></a></div>'+
                                    '</div>' +
                                    '<div class="closed" style="float:right; margin-right: 5px; cursor:pointer;">×</div>' +
                                '</div>'+
                           '</div>'+
                           '<div style="clear:both;"></div>';
            $("body").append(img_div);

            that.dialog = $(".dialogImg");

            that.dialog.find("#img_dialog").load(function() {
                var img_dialog = that.dialog.find("#img_dialog");
                that.dialog.css({'width':img_dialog.width()+10, 'height':img_dialog.height()+30});
                that.cal_wh(that.dialog);
            });
            that.dialog.find('.next').on('click', function(){
                var $num = that.dialog.find('.num');
                if( that.opts.imgs_index<imgs.length )
                {
                    that.opts.imgs_index = parseInt(that.opts.imgs_index)+1;

                }
                else if( that.opts.imgs_index>len )
                {
                    that.opts.imgs_index = len;
                }
                $num.empty('').html(that.opts.imgs_index);
                that.dialog.find('#img_dialog').attr('src', '/static/res/imgs/'+imgs[that.opts.imgs_index-1]);
            });
            that.dialog.find('.prev').on('click', function(){
                var $num = that.dialog.find('.num');
                if( that.opts.imgs_index<1 )
                {
                    that.opts.imgs_index = 1;
                }
                else
                {
                    that.opts.imgs_index = len-1;
                }
                $num.empty('').html(that.opts.imgs_index);
                that.dialog.find('#img_dialog').attr('src', '/static/res/imgs/'+imgs[that.opts.imgs_index-1]);
            });
        }
        else
        {
            var btn_ok_text = that.opts.btn_ok_text!='' ? '<a href="javascript:;" class="btn_ok">'+that.opts.btn_ok_text+'</a>' : '';
            var btn_cancel_text = that.opts.btn_cancel_text!='' ? '<a href="javascript:;" class="btn_cancel">'+that.opts.btn_cancel_text+'</a>' : '';
            var def_div = '<div class="dialogDiv" id="'+that.id+'"> \
                                <div class="dialogBox"> \
                                    <div class="header"> \
                                        <div class="header_left"> \
                                            <h3>'+that.opts.title+'</h3> \
                                        </div> \
                                        <div class="header_right"> \
                                            <a href="javascript:;" class="closed"><span class="close">×</span></a> \
                                        </div> \
                                    </div> \
                                    <div style="background:#ffffff;" class="mid"> \
                                        <div class="content"> \
                                        </div> \
                                        <div class="footers"> \
                                            '+btn_ok_text + btn_cancel_text+' \
                                        </div> \
                                     </div> \
                                </div> \
                            </div> \
                            ';
            $("body").append(def_div);

            that.dialog = $(".dialogDiv");

            that.dialog.find(".dialogBox > .mid > .footer > a").mousedown(
                function(){
                    $(this).css({ 'border':'0px inset #eee', 'color':'#CCCCCC', 'text-decoration':'none'});
                }
            ).mouseup(
                function(){
                    $(this).css({ 'border':'0px outset #eee', 'color':'#000000', 'text-decoration':'none'});
                }
            );
            if(that.opts.btn_ok_text=='' && that.opts.btn_cancel_text==''){
                that.dialog.find(".footer").remove();
            }
            //显示内容
            that.content(that.dialog, that.opts.http!='' ? that.opts.http : that.opts.content);
        }
        that.cal_wh(that.dialog);
        that.dialog.show();
        that.btn_ok = that.dialog.find('.btn_ok');
        that.btn_cancel = that.dialog.find('.btn_cancel');

        if(that.opts.is_showbg )
        {
            var tmp = mask._show();
            that.dialog.css({'z-index': parseInt(tmp.css('z-index'))+1});
        }
        //给关闭按钮绑定关闭动作
        if( that.dialog.find('.closed').length>0 && that.opts.close && that.dialog!=null )
        {
            that.dialog.find('.closed').on("click", function(){
                that.closed();
            });
        }
        //添加到list集合中
        that._list[that.id] = that.dialog;

        if( that.opts.delay_time == '' || typeof that.opts.delay_time == 'undefined')
        {
            return that.dialog;
        }
        else
        {
            t && clearTimeout(t);
            var t = setTimeout(function(){
                                    that.closed();
                                },that.opts.delay_time);
        }
    };
    this.changeContent = function(content, opts){
        if( opts )
        {
            that.opts = $.extend(true, {}, that.opts, opts);
            this.loadCss();
            obj = that.created(true);
        } else {
            if( typeof that._list[that.id]=='object' ) {
                obj = that._list[that.id];
            } else {
                obj = that.created();
            }
        }
        that.content(obj, content);
    };
    //初始化
    this.init = function(){
        if( typeof that._list[that.id]=='object' ){
            obj = that._list[that.id];
        } else {
            //使用弹出框
            obj = that.created();
        }
        if( arguments.length>0 && typeof(arguments[0])=='string' )
        {
            that.content(obj, arguments[0]);
        }
        //ESC关闭功能
        $(document).on('keydown', function (event) {
                                            var target = event.target;
                                            var nodeName = target.nodeName;
                                            var rinput = /^input|textarea$/i;
                                            var keyCode = event.keyCode;
                                            // 避免输入状态中 ESC 误操作关闭
                                            if (rinput.test(nodeName) && target.type !== 'button') {
                                                return;
                                            }
                                            if (keyCode === 27) {
                                                this.closed();
                                            }
        });
        that.dialog.find('.btn_cancel').on('click', function(){
            that.closed();
        });
        //拖拽效果
        if( that.opts.is_move )
        {
            that.dialog.drag(
            {
                viewArea:true
            });
        }
        return that;
    };
    //绑定弹出框的确认和取消按钮
    this.bind_func = function(name, callback){
        if(!$.isFunction(callback)){
            console.log('callback is not function');
            return false;
        }
        var obj = this;
        var ele;
        if(name=='ok'){
            ele = this.btn_ok;
        } else {
            ele = this.btn_cancel;
        }
        ele.on('click', function(){
            return callback(obj);
        });
    };

};

/**
 *  防止拖拽到可视区域以外
 *  handle:'h2.title',
    viewArea:true,
    ondragstart:function()
    {
        $h2.html('拖动开始');
    },
    ondraging:function()
    {
        $h2.html('拖动过程中……');
    },
    ondragstop:function()
    {
        $h2.html('拖动停止');
    }
 */
$.fn.drag = function(setting)
{
    return this.each(function()
    {
        var defaults=
        {
            handle:".header",
            zIndex:9999,
            direction:"xy",//运动方向
            viewArea:true,//是否只在可视区域拖动
            ondragstart:null,//拖动开始
            ondraging:null,//拖动过程
            ondragstop:null//拖动结束
        };
        var ie = function ()
        {
            var v = 4,
                div = document.createElement('div'),
                i = div.getElementsByTagName('i');
            do {
                div.innerHTML = '<!--[if gt IE ' + (++v) + ']><i></i><![endif]-->';
            } while (i[0]);
            return v > 5 ? v : false;
        }();
        var opt=		$.extend(defaults, setting),
            $box=		$(this),
            $parent=	$box,//父级
            $handle=	(opt.handle === "") ? $box : $box.find(opt.handle),
            sL,sT,//鼠标在box中的位置，为fixed服务
            x0,y0,//鼠标的初始坐标
            l0,t0,//box的初始位置
            pos = $box.css('position'),//默认位置
            on_drag = 0;//是否正在拖动
        var z_idx = $box.css('z-index')=='auto' ? opt.zIndex : $box.css('z-index');//默认层级
        var dowhile=true;
        while(dowhile)
        {
            $parent=$parent.parent();
            if($parent[0].tagName.toString().toLowerCase()=='body')
            {
                dowhile=false;
            }
            if($parent.css('position')!='static')
            {
                dowhile=false;
            }
        }

        // 鼠标按下
        $handle.css('cursor','move').on("mousedown", function(e)
        {
            var e=e||window.event;
            if(on_drag==1)return false;
            on_drag=1;
            x0=e.clientX,
            y0=e.clientY,
            sL=	x0-$box.position().left,
            sT=	y0-$box.position().top,
            l0=$box.offset().left,
            t0=$box.offset().top;
            if($.isFunction(opt.ondragstart))opt.ondragstart();
            return false;
        });

        // 鼠标按下并且在文档内移动
        $(document).on('mousemove',function(e)
        {
            var e=e||window.event;
            if(on_drag)
            {
                $box.css('cursor','move');
                var
                x1		=e.clientX,
                y1		=e.clientY;
                var
                l1		=x1-x0+l0,
                t1		=y1-y0+t0,
                boxW	=$box[0].offsetWidth,
                boxH	=$box[0].offsetHeight,
                boxML	=NaN20(parseInt($box.css('margin-left'),10)),
                boxMT	=NaN20(parseInt($box.css('margin-top'),10)),
                parentL	=$parent.position().left,//左位移
                parentT	=$parent.position().top,//上位移
                parentML=NaN20(parseInt($parent.css('margin-left'),10)),//父定位元素左外边距
                parentMT=NaN20(parseInt($parent.css('margin-top'),10)),//父定位元素左外边距上外边距
                parentBL=NaN20(parseInt($parent.css('border-left-width'),10)),//父定位元素左外边距左边框
                parentBT=NaN20(parseInt($parent.css('border-top-width'),10)),//父定位元素左外边距上边框
                winW	=$(window).width(),
                winH	=$(window).height(),
                scrL	=$(window).scrollLeft(),
                scrT	=$(window).scrollTop();

                // 可视区域内
                if(opt.viewArea)
                {
                    var
                    minL=-(parentL+parentML+parentBL+boxML)+scrL,
                    maxL=winW-boxW+minL,
                    minT=-(parentT+parentMT+parentBT+boxMT)+scrT,
                    maxT=winH-boxH+minT;
                    if(l1<minL)l1=minL;
                    if(t1<minT)t1=minT;
                    if(l1>maxL)l1=maxL;
                    if(t1>maxT)t1=maxT;
                }

                // 非ie6 && 固定定位
                if(ie!=6 && pos==='fixed')
                {
                    l1=x1-sL-scrL;
                    t1=y1-sT-scrT;
                    // 可视区域内
                    if(opt.viewArea)
                    {
                        var
                        minL=-boxML,
                        maxL=winW-boxW+minL,
                        minT=-boxMT,
                        maxT=winH-boxH+minT;
                        if(l1<minL)l1=minL;
                        if(t1<minT)t1=minT;
                        if(l1>maxL)l1=maxL;
                        if(t1>maxT)t1=maxT;
                    }
                }
                else
                {
                    $box.css('position','absolute');
                }

                $box.css('z-index',opt.zIndex);
                if(t1<0){
                    t1 = 0;
                }
                if(opt.direction=='x')$box.css('left',l1);
                if(opt.direction=='y')$box.css('top',t1);
                if(opt.direction=='xy')$box.css({'left':l1,'top':t1});

                if($.isFunction(opt.ondraging))opt.ondraging();
                return false;
            }
        });

        // 在document内鼠标弹起
        $(document).on('mouseup',function(e)
        {
            if(on_drag)
            {
                $(document.body).css('cursor','auto');
                var e=e||window.event;
                on_drag=0;
                $box.css({'z-index':z_idx});
                if($.isFunction(opt.ondragstop))opt.ondragstop();
            }
        });
        function NaN20(o)
        {
            return isNaN(o)?0:o;
        }
    });
};

////////////////////////////////多级联动下拉框///////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//http://www.itooy.com/demo/linkage/demo.html

//////////////////////////////////联动下拉框/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
$.fn.changeSelect = function(opts){
    if(opts.url=='' || opts.name==''){
        return false;
    }
    var defaults = {'_xsrf': '', 'url': '', 'name': '', 'hidden':''};
    opts = $.extend(true, {}, defaults, opts);
    var nownum = $(this, '#'+name).index()+1;
    var id = $(this).val();
    $('#'+opts.hidden).val(id);
     //清空过时的选项
    $("#"+opts.name).children("select").each(function(index){
        if(index+1 > nownum) {
            $(this).remove();
        }
    });
    if(id=='' ){
        return;
    }
    $.ajax({
        type: "POST",
        url: opts.url,
        data: {_xsrf: opts._xsrf, pid: id},
        datatype : "json",
        success: function(result){
            if(result!='[]'){
                var html = '';
                html += "<select class='form-control' id='"+opts.name+"_" + nownum + "' style='"+opts.css+"'>";
                html += "<option value=''>请选择……</option>";
                var datas = eval(result);
                $.each(datas, function(i,val){
                    html += "<option value='"+val.id+"' >"+val.name+"</option>";
                });
                html += "</select>";
                //清空过时的选项
                $("#"+opts.name).children("select").each(function(index){
                    if(index+1 > nownum) {
                        $(this).remove();
                    }
                });
                $("#"+opts.name).append(html);
                $("#"+opts.name+"_" + nownum).on('change', function(){
                    $(this).changeSelect(opts);
                });
            } else {
                $("#"+opts.name).children("select").each(function(index){
                    if(index+1 > nownum) {
                        $(this).remove();
                    }
                });
            };
        },
        error: false
    });
};

/////////////////////////////////日历控件////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
/**
 * 生成日历功能
 */
$.fn.Calendar = function(setting){
    var Calendar = {
        model:function(){} ,
        controller:function(){} ,
        view:function(){}
    };
    //视图层
    Calendar.view = function(){
        this.currDate = new Date();
        this.tds = null;
        this.days = null;
        this.backNode = null;
        this.disableDays = new Array();
    };
    //根据年份返回每月天数
    Calendar.view.getMonthDays = function(year){
        var feb = (year % 4 == 0)? 29:28;
        return new Array(31, feb , 31, 30, 31, 30, 31, 31, 30, 31, 30, 31);
    };
    //为单元格注册事件
    Calendar.view.prototype.addEventForTd = function(){
        for (var i=0;i<this.tds.length ;i++ )
        {
            this.tds[i].onclick = function(){
                var arr = this.getAttribute("dateValue").split("-");
                alert(arr[0] +"-"+ (parseInt(arr[1])+1) +"-"+ arr[2]);
            };
        }
    };
    //设定当前版面
    Calendar.view.prototype.setCurrMonth = function(y ,m){
        this.currDate.setFullYear(y);
        this.currDate.setMonth(m);
        this.currDate.setDate(1);
        this.loadDaysByMonth(y ,m);
    };
    //标示当前天
    Calendar.view.prototype.markCurrDate = function(bDay ,eDay){
        var temp = new Date();
        if( this.currDate.getFullYear() == temp.getFullYear() && this.currDate.getMonth() == temp.getMonth() )
        {
            for( var i=bDay; i<eDay; i++ )
            {
                if( this.tds[i].getAttribute("dateValue").split("-")[2] == temp.getDate() )
                {
                    if( this.backNode )
                    {
                        this.backNode.className = "";
                    }
                    this.tds[i].className = "currDay";
                    this.backNode = this.tds[i];
                    return false;
                }
            }
        }
    };
    //复位版面状态
    Calendar.view.prototype.reInState = function(){
        this.tds[35].parentNode.style.display = "none";
        if(this.backNode)
        {
            this.backNode.className = "";
        }
        for(var i=0;i<this.disableDays.length ;i++ )
        {
            this.disableDays[i].className = "dayStyle";
        }
        this.disableDays.length = 0;
    };
    //根据年月加载当前视图
    Calendar.view.prototype.loadDaysByMonth = function(y ,m){
        y = parseInt(y) ,m = parseInt(m);
        this.reInState();	//复位版面状态
        //参数定位
        var beginDay = this.currDate.getDay();
        var _m = (m == 0)?11 : (m-1);
        var m_ = (m == 11)?0 : (m+1);
        var _y = (m == 0)?(y-1) : y;
        var y_ = (m == 11)?(y+1) : y;

        var prevMonthDays = Calendar.view.getMonthDays(_y)[_m];
        var currMonthDays = Calendar.view.getMonthDays(y)[m];
        var prevFlag = prevMonthDays - beginDay + 1 ,currFlag = 1 ,nextFlag = 1;

        //加载上月信息
        for( var i=0;i<beginDay ;i++ )
        {
            this.tds[i].setAttribute("dateValue" ,_y +"-"+ _m +"-"+ prevFlag);
            this.days[i].innerHTML = prevFlag;
            this.days[i].className = "dayStyle disableText";
            this.disableDays.push(this.days[i]);
            prevFlag++;
        }

        //加载当月信息
        for (var i=beginDay;i<currMonthDays+beginDay ;i++ )
        {
            this.tds[i].setAttribute("dateValue" ,y +"-"+ m +"-"+ currFlag);
            this.days[i].innerHTML = currFlag;
            currFlag++;
        }

        //加载下月信息
        for (var i=currMonthDays+beginDay;i<this.days.length ;i++ )
        {
            this.tds[i].setAttribute("dateValue" ,y_ +"-"+ m_ +"-"+ nextFlag);
            this.days[i].innerHTML = nextFlag;
            this.days[i].className = "dayStyle disableText";
            this.disableDays.push(this.days[i]);
            nextFlag++;
        }

        //若当月数据显示到第7行，那么显示它
        if (this.tds[35].getAttribute("dateValue"))
        {
            if (this.tds[35].getAttribute("dateValue").split("-")[2] > 20)
            {
                this.tds[35].parentNode.style.display = "";
            }
        }
        //标示当前天
        this.markCurrDate(beginDay ,currMonthDays+beginDay);
    };
    //初始化
    Calendar.view.prototype.init = function(){
        this.setCurrMonth(new Date().getFullYear() ,new Date().getMonth());
        this.addEventForTd();
    };

    var getAllEles = function(obj, className){
        var rets = new Array();
        obj.find('.'+className).each(function(i,n){
            rets.push(n);
        });;
        return rets;
    };
    var created = function(obj) {
        view = new Calendar.view();
        view.tds = obj.children("#render").find("td");
        view.days = getAllEles(obj, "dayStyle");
        view.init();
        obj.find("#setDate").click(function(){
            view.setCurrMonth(obj.children("#testYear").val(), obj.children("#testMonth").val());
        });
    }
    created(this);
}

/////////////////////////////////气泡控件///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
/**
 * $('input[name='+val['name']+']').tip({content:'<span style="color:red">'+val['error']+'</span>', gravity:'n', trigger:'show', id:val['name'], html:true});
 * @param options  option里的id是唯一标示的
 * @returns {*}
 */
$.fn.tip = function(options) {
    opts = $.extend({}, $.fn.tip.defaults, options);
    function maybeCall(thing, ctx) {
        return (typeof thing == 'function') ? (thing.call(ctx)) : thing;
    };
    if(typeof(this)=='undefined') {
        console.log('获取不到对象');
        return false;
    }
    var $element = this;
    var cls_tmp = opts.form ? 'form-' : '';
    var get = function() {
        var find_tip = $("#tip-"+opts.id);
        if (find_tip.length==0){
            this.$tip = $('<div class="tip" id="tip-'+opts.id+'"></div>').html('<div class="'+cls_tmp+'tip-arrow"></div><div class="'+cls_tmp+'tip-inner"></div>');
        } else{
            this.$tip = find_tip;
        }
        return this.$tip;
    }
    var leave = function() {
        var $tip = get();
        $tip.remove();
    };
    var enter = function() {
        show();
    };
    var show = function(){
        var $tip = get();
        $tip.find('.'+cls_tmp+'tip-inner')[opts.html ? 'html' : 'text'](opts.content);
        $tip.className = 'tip';
        $tip.css({top: 0, left: 0, visibility: 'hidden', display: 'block'}).prependTo(document.body);
        var pos = $.extend({}, $element.offset(), {
                    width: $element[0].offsetWidth,
                    height: $element[0].offsetHeight
                });
        var actualWidth = $tip[0].offsetWidth,
                    actualHeight = $tip[0].offsetHeight,
                    gravity = maybeCall(opts.gravity, $element);
        var tp;
        var tmp_tip_gravity;
        switch (gravity.charAt(0)) {
            case 'n':
                tp = {top: pos.top + pos.height + opts.offset, left: pos.left + pos.width / 2 - actualWidth / 2};
                tmp_tip_gravity = {'top': 0, 'right': '10px'};
                break;
            case 's':
                tp = {top: pos.top - actualHeight - opts.offset, left: pos.left + pos.width / 2 - actualWidth / 2};
                tmp_tip_gravity = {'bottom': 0, 'right': '50%'};
                break;
            case 'e':
                tp = {top: pos.top + pos.height / 2 - actualHeight / 2, left: pos.left - actualWidth - opts.offset};
                tmp_tip_gravity = {top: '50%', 'right': '0'};
                break;
            case 'w':
                tp = {top: pos.top + pos.height / 2 - actualHeight / 2, left: pos.left + pos.width + opts.offset};
                tmp_tip_gravity = {top: '50%', 'left': '0'};
                break;
        }
        if (gravity.length == 2) {
            if (gravity.charAt(1) == 'w') {
                tp.left = pos.left + pos.width / 2 - 15;
            } else {
                tp.left = pos.left + pos.width / 2 - actualWidth + 15;
            }
        }
        $tip.css(tp).addClass('tip-' + gravity);
        $tip.find('.'+cls_tmp+'tip-arrow').className = cls_tmp+ 'tip-arrow '+cls_tmp+'tip-arrow-' + gravity.charAt(0);
        $tip.css({visibility: 'visible', opacity: opts.opacity});
        if( opts.color!='' )
        {
            $tip.find('.'+cls_tmp+'tip-inner').css({'border': '1px solid '+opts.color});

            $tip.find('.'+cls_tmp+'tip-arrow').css({    'border-color': opts.color,
                                                        'border-top-color': 'transparent',
                                                        'border-bottom-color': 'transparent',
                                                        'border-left-color': 'transparent',
                                                        'border-right-color': 'transparent',
                                                        'border-top-color': opts.color
            });
            $tip.find('.'+cls_tmp+'tip-arrow').css(tmp_tip_gravity);
        }
        return $tip;
    };
    if (opts.trigger != 'manual') {
        if(opts.trigger=='show'){
            return show();
        } else{
            var eventIn  = opts.trigger == 'hover' ? 'mouseenter' : 'focus',
            eventOut = opts.trigger == 'hover' ? 'mouseleave' : 'blur';
            $element.on(eventIn, enter).on(eventOut, leave);
        }
    }
}
$.fn.tip.defaults = {
        id: '',
        gravity: 'w',
        html: false,
        offset: 0,
        opacity: 0.8,
        title: 'title',
        trigger: 'hover',
        content: '',
        form: true,
        color: ''
};

/**
 * 移动滚动条到顶部停止
 * @param opts
 */
$.fn.stopOnTop = function(end_ele, dv_css) {
    var obj = this;
    var ie6 = /msie 6/i.test(navigator.userAgent)
    , dv = $(obj), st;
    var dv_left = dv.offset().left;
    dv.attr('otop', dv.offset().top); //存储原来的距离顶部的距离
    var end_ele_top = parseInt($('#'+end_ele).offset().top-dv.height());
    //获取
    $(window).scroll(function () {
        st = Math.max(document.body.scrollTop || document.documentElement.scrollTop);
        temp_top = parseInt(dv.attr('otop'));
        if(st>=temp_top)
        {
            if(ie6)
            {
                //IE6不支持fixed属性，所以只能靠设置position为absolute和top实现此效果
                dv.css({ position: 'absolute', top: st , left:dv_left, 'z-index':9999, 'display': 'block'});
            }
            else if(dv.css('position') != 'fixed')
            {
                dv.css({ 'position': 'fixed', top: 0 , left:dv_left, 'z-index':9999, 'display': 'block'});
            }

            if(end_ele_top<=st)
            {
                dv.css({'display':'none'});
            }
        }
        else if(st<temp_top)
        {
            if(dv_css){
                dv.removeAttr("style");
                dv.css(dv_css);
                dv.css({'display':'block'});
            }
            else{
                dv.css({ 'position':'static', 'display': 'block'});
            }
        }
    });
};

/**
 * 表单验证
 */
$.fn.formValidate = function(fields, callback, opts) {
    var defaults = {
        messages: {
            required: '%s不能为空',
            matches: '%s和%s不匹配',
            valid_email: '%s格式不正确',
            min_length: '%s最小长度为%s',
            max_length: '%s最大长度为%s',
            exact_length: '%s长度为%s',
            greater_than: '%s必须大于%s',
            less_than: '%s必须小于%s',
            alpha: '%s必须是字母',
            alpha_numeric: '%s必须是字母和数字',
            alpha_dash: '%s必须是字母，数字，下划线，破折号',
            numeric: '%s必须是数字',
            integer: '%s必须是整型',
            valid_credit_card: '%s必须是银行卡号'
        },
        callback: function(errors) {

        },
        showMsg: false
    };
    var ruleRegex = /^(.+)\[(.+)\]$/,
        numericRegex = /^[0-9]+$/,
        integerRegex = /^\-?[0-9]+$/,
        decimalRegex = /^\-?[0-9]*\.?[0-9]+$/,
        emailRegex = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/,
        alphaRegex = /^[a-z]+$/i,
        alphaNumericRegex = /^[a-z0-9]+$/i,
        alphaDashRegex = /^[a-z0-9_-]+$/i,
        urlRegex = /^((http|https):\/\/(\w+:{0,1}\w*@)?(\S+)|)(:[0-9]+)?(\/|\/([\w#!:.?+=&%@!\-\/]))?$/;
    var obj = this;
    var FormValidator = function(fields, callback){
        defaults = $.extend({}, defaults, opts);
        this.callback = callback || defaults.callback;
        this.errors = [];
        this.fields = {};
        this.messages = {};
        this.customs = [];
        this.form = $(obj) || $(obj).parent('form') || {};
        for (var i = 0, fieldLength = fields.length; i < fieldLength; i++) {
            var field = fields[i];
            if (!field.name || typeof field.rules=='undefined') {
                continue;
            }
            this.fields[field.name] = {
                name: field.name,
                rules: field.rules,
                display: field.display || field.name,
                type: null,
                value: null,
                checked: null,
                customs: field.customs,
                id: (field.id!=undefined) ? field.id : null,
                element: null,
                msg: field.msg
            }
        }
        return this._validateForm();
    };
    var attributeValue = function (element, attributeName) {
        var i;
        if ((element.length > 0) && (element[0].type === 'radio' || element[0].type === 'checkbox')) {
            console.log(element);
            for (i = 0, elementLength = element.length; i < elementLength; i++) {
                if (element[i].checked) {
                    return element[i][attributeName];
                }
            }
            return;
        }
        return element[attributeName];
    };
    FormValidator.prototype._validateForm = function() {
        this.errors = [];
        that = this;
        for (var key in this.fields) {
            if (that.fields.hasOwnProperty(key)) {
                var field = that.fields[key] || {}, element = $("input[name="+field.name+"]", that.form);
                if( typeof element=='undefined' ){
                    element = $("input[name="+field.id+"]", that.form);
                }
                //验证表单
                if( element && element !== undefined ){
                    field.id = attributeValue(element, 'id');
                    field.element = element;
                    field.type = (element.length > 0) ? element[0].type : element.type;
                    field.value = $("input[name="+field.name+"]", that.form).val();
                    field.checked = attributeValue(element, 'checked');
                }
                //验证字段
                that._validateField(field);
                //自定义的方法验证
                if (field.customs) {
                     $.each(field.customs, function(i,val){
                        if(typeof val['param']=='undefined'){
                            val['param'] = '';
                        }
                        if(val['method'].call(this, field, val['param'])==false) {
                            that.errors.push({'name':field.name, 'error':val['message']});
                        }
                        delete params;
                    });
                }
            }
        }
        if (typeof this.callback === 'function') {
            this.callback(this.errors);
        }

        if (this.errors.length > 0) {
            var errors = this.errors;
            //显示错误提示样式
            if(!defaults.showMsg){
                //判断是否执行默认的错误显示
                $.each(errors, function(i,val){
                    var old_val = $("input[name="+val.name+"]", that.form).val();
                    $("input[name="+val.name+"]", that.form).focus(function(){
                        $(this).siblings("#helpBlock").remove();
                    }).blur(function(){
                       $(this).siblings("#helpBlock").remove();
                       if($(this).val()===old_val) {
                            $(this).after('<div class="clearfix"  id="helpBlock"><span class="help-block help-msg">'+val['error']+'</span></div>');
                       }
                    }).blur();
                });
            }

            /*$(document).bind('click',function(e){
                if(!$.inArray(e.target, this.eles)){
                    $(that.form).find('#helpBlock').remove();
                    stopPropagation(e);
                }
            });*/
            return false;
        }
        return true;
    };
    FormValidator.prototype._validateField = function(field) {
        var rules = field.rules.split('|');
        if (field.rules.indexOf('valid_ueditor') === -1 && field.rules.indexOf('required') === -1 && (!field.value || field.value === '' || field.value === undefined)) {
            return;
        }
        for (var i = 0, ruleLength = rules.length; i < ruleLength; i++) {
            var method = rules[i],
                param = null,
                failed = false;
            //正则验证规则是否正确
            if (parts = ruleRegex.exec(method)) {
                method = parts[1];
                param = parts[2];
            }
            if (typeof this._hooks[method] === 'function') {
                if (!this._hooks[method].apply(this, [field, param])) {
                    failed = true;
                }
            }
            //提示信息的填充
            if (failed) {
                if(typeof this.fields[field.name].msg!='undefined' && this.fields[field.name].msg!=''){
                    this.errors.push({'name':field.name, 'error':this.fields[field.name].msg});
                    break;
                }
                var source = this.messages[method] || defaults.messages[method];
                if (source) {
                    var message = source.replace('%s', field.display);
                    if (param) {
                        message = message.replace('%s', (this.fields[param]) ? this.fields[param].display : param);
                    }
                    this.errors.push({'name':field.name, 'error':message});
                } else {
                    this.errors.push({'name':field.name, 'error':'An error has occurred with the ' + field.display + ' field.'});
                }
                break;
            }
        }
    };
    FormValidator.prototype._hooks = {
        required: function(field) {
            var value = field.value;
            if (field.type === 'checkbox' || field.type=='radio') {
                return (field.checked === true);
            }
            return (value !== null && value !== '' && value !== undefined);
        },
        matches: function(field, matchName) {
            if (el = $('input[name='+matchName+']', this.form)) {
                return field.value === el.val();
            }
            return false;
        },
        valid_email: function(field) {
            return emailRegex.test(field.value);
        },
        valid_url: function(field) {
            return (urlRegex.test(field.value));
        },
        min_length: function(field, length) {
            if (!numericRegex.test(length)) {
                return false;
            }
            return (field.value.length >= length);
        },
        max_length: function(field, length) {
            if (!numericRegex.test(length)) {
                return false;
            }
            return (field.value.length <= length);
        },
        exact_length: function(field, length) {
            if (!numericRegex.test(length)) {
                return false;
            }
            return (field.value.length == length);
        },
        greater_than: function(field, param) {
            if (!decimalRegex.test(field.value)) {
                return false;
            }
            return (parseFloat(field.value) > parseFloat(param));
        },
        less_than: function(field, param) {
            if (!decimalRegex.test(field.value)) {
                return false;
            }
            return (parseFloat(field.value) < parseFloat(param));
        },
        alpha: function(field) {
            return (alphaRegex.test(field.value));
        },
        alpha_numeric: function(field) {
            return (alphaNumericRegex.test(field.value));
        },
        alpha_dash: function(field) {
            return (alphaDashRegex.test(field.value));
        },
        numeric: function(field) {
            return (decimalRegex.test(field.value));
        },
        integer: function(field) {
            return (integerRegex.test(field.value));
        },
        decimal: function(field) {
            return (decimalRegex.test(field.value));
        },
        valid_credit_card: function(field){
            if (!numericDashRegex.test(field.value)) return false;
            var nCheck = 0, nDigit = 0, bEven = false;
            var strippedField = field.value.replace(/\D/g, "");
            for (var n = strippedField.length - 1; n >= 0; n--) {
                var cDigit = strippedField.charAt(n);
                nDigit = parseInt(cDigit, 10);
                if (bEven) {
                    if ((nDigit *= 2) > 9) nDigit -= 9;
                }
                nCheck += nDigit;
                bEven = !bEven;
            }
            return (nCheck % 10) === 0;
        },
        is_file_type: function(field,type) {
            if (field.type !== 'file') {
                return true;
            }
            var ext = field.value.substr((field.value.lastIndexOf('.') + 1)),
                typeArray = type.split(','),
                inArray = false,
                i = 0,
                len = typeArray.length;
            for (i; i < len; i++) {
                if (ext == typeArray[i]) inArray = true;
            }
            return inArray;
        }
    };
    FormValidator.prototype.setMessage = function(rule, message) {
        this.messages[rule] = message;
        return this;
    };
    return new FormValidator(fields, callback);
}

/////////////////////////////////////////////////////////////搜索下拉框 begin//////////////////////////////////////////////////////////////////////////////////
/**
 * https://github.com/lzwme/bootstrap-suggest-plugin/blob/master/bootstrap-suggest.js
 * var selectObj = $("#baidu").selectSearch(
        {   allowNoKeyword: false,
            multiWord: true,
            separator: ",",
            url: 'http://localhost:8881/test?wd=',
            initData: {'value': [{"word": "1234"}, {"word": "890"}]},
        }
);
 **/
$.fn.selectSearch = function(opts) {
    var self = this;
    var options = {
        url: null,
        jsonp: '',
        adjustWidth: false,
        cacheData: true,
        dataMethod: '',
        idField: "",
        keyField: "",
        indexKey: 0,    //每组数据的第几个数据，作为input输入框的内容
        indexId: 0,     //每组数据的第几个数据，作为input输入框的 data-id，设为 -1 且 idField 为空则不设置此值
        effectiveFields: [],
        effectiveFieldsAlias: {},       //有效字段的别名对象，用于 header 的显示
        showHeader: false,              //是否显示选择列表的 header
        separator: ",",                 //多关键字支持时的分隔符，默认为半角逗号
        multiWord: false,
        processData: '',       //格式化数据的方法，返回数据格式参考 data 参数
        listHoverCSS: 'jhover',               //提示框列表鼠标悬浮的样式名称
        listHoverStyle: 'background: #07d; color:#fff',             //提示框列表鼠标悬浮的样式
        listStyle: {
                    "padding-top": 0, "max-height": "375px", "max-width": "800px",
                    "overflow": "auto", "width": "auto",
                    "transition": "0.3s", "-webkit-transition": "0.3s", "-moz-transition": "0.3s", "-o-transition": "0.3s"
                    },
        listAlign: "left",    //提示列表对齐位置，left/right/auto
        initData: {'value':[]},
    };
    var selectSearchObj = function(opts) {
        options = $.extend({}, options, opts);
        //参数处理
        if( $.isFunction(options.processData) ) {
            processData = options.processData;
        }
        //默认配置，配置有效显示字段多于一个，则显示列表表头，否则不显示
        if( !options.showHeader && options.effectiveFields && options.effectiveFields.length > 1 ) {
            options.showHeader = true;
        }
        //鼠标滑动到条目样式 样式添加到head里
        $("head:eq(0)").append( '<style>.' +
                                    options.listHoverCSS + '{' + options.listHoverStyle + '}' +
                                '</style>');
        this.init();
        return true;
    };
    selectSearchObj.prototype.init = function(){
        var widget = this;
        return self.each(function(){
            var input_obj = $(this);
            var dropdown_menu_obj = widget.getDropDownMenu(input_obj);//input_obj.parent().find("ul.dropdown-menu");
            input_obj.removeClass("disabled").attr("disabled", false).attr("autocomplete", "off");
            dropdown_menu_obj.css(options.listStyle); //下拉列表添加样式
            dropdown_menu_obj.css("width", "auto");//设置下拉框的宽度

            //开始事件处理
            input_obj.on("keydown", function (event) {
                var current_list, tips_keyword = '';//提示列表上被选中的关键字
                if( dropdown_menu_obj.css('display')!=='none' ) {
                    current_list = dropdown_menu_obj.find('.' + options.listHoverCSS);
                    tips_keyword = '';//提示列表上被选中的关键字
                    if( event.keyCode===40 ) { //如果按的是向下方向键
                        if( current_list.length===0 ) {
                            //如果提示列表没有一个被选中,则将列表第一个选中
                            tips_keyword = widget.getPointKeyword(dropdown_menu_obj.find('table tbody tr:first').mouseover());
                        }
                        else if( current_list.next().length===0 ) {
                            //如果是最后一个被选中,则取消选中,即可认为是输入框被选中，并恢复输入的值
                            widget.unHoverAll(dropdown_menu_obj);
                            $(this).val($(this).attr('alt')).attr("data-id", "");
                        }
                        else
                        {
                            widget.unHoverAll(dropdown_menu_obj);
                            //将原先选中列的下一列选中
                            if( current_list.next().length!==0 ) {
                                tips_keyword = widget.getPointKeyword(current_list.next().mouseover());
                            }
                        }
                        //控制滑动条
                        widget.adjustScroll(input_obj, dropdown_menu_obj);
                    }
                    else if( event.keyCode===38 ) { //如果按的是向上方向键
                        if( current_list.length===0 ){
                            tips_keyword = widget.getPointKeyword(dropdown_menu_obj.find('table tbody tr:last').mouseover());
                        } else if( current_list.prev().length===0 ) {
                            //最顶端的一行
                            widget.unHoverAll(dropdown_menu_obj);
                            $(this).val($(this).attr('alt')).attr("data-id", "");
                        } else {
                            widget.unHoverAll(dropdown_menu_obj);
                            if( current_list.prev().length!==0 ) {
                                tips_keyword = widget.getPointKeyword(current_list.prev().mouseover());
                            }
                        }
                        //控制滑动条
                        widget.adjustScroll(input_obj, dropdown_menu_obj);
                    }
                    else if( event.keyCode===13) { //回车键
                        dropdown_menu_obj.hide().empty();
                        stopDefault(event);
                    } else {
                        $(this).attr("data-id", "");
                    }
                    //支持空格为分割的多个提示
                    if( tips_keyword && tips_keyword.key!=='' ){
                        widget.setValue($(this), tips_keyword);
                    }
                }
                if(options.adjustWidth){
                    widget.adjustDropMenuPos(input_obj, dropdown_menu_obj);
                }
            }).on("keyup", function (event) {
                var word, words;
                //如果弹起的键是回车、向上或向下方向键则返回
                if( event.keyCode===40 || event.keyCode===38 || event.keyCode===13 ) {
                    if(event.keyCode===13)
                        $(this).val($(this).val());//让鼠标输入跳到最后
                    widget.setBackground(input_obj);
                    return;
                }
                else {
                    $(this).attr("data-id", "");
                    widget.setBackground(input_obj);
                }
                word = $(this).val();
                //若输入框值没有改变或变为空则返回
                if(!options.adjustWidth){
                    if( $.trim(word)!=='' && word===$(this).attr('alt') ) {
                        return;
                    }
                }
                //当按下键之前记录输入框值,以方便查看键弹起时值有没有变
                $(this).attr('alt', $(this).val());
                if( options.multiWord ) {
                    words = word.split( options.separator || ' ');
                    word = words[words.length-1];
                }
                //空值不允许查询
                if( word.length===0 ) {
                    return;
                }
                widget.getData($.trim(word), input_obj);
                if(options.adjustWidth){
                    widget.adjustDropMenuPos(input_obj, dropdown_menu_obj);
                }
            }).on("focus", function () {
                widget.adjustDropMenuPos(input_obj, dropdown_menu_obj);
                if( input_obj.val()=='' )
                {
                    if( widget.checkData(options.initData) &&  options.initData.value.length!=0 )
                    {
                        widget.refreshDropMenu(input_obj, options.initData);
                    }
                }
            }).on('focusout', function(){
                if(options.adjustWidth){
                    widget.adjustDropMenuPos(input_obj, dropdown_menu_obj);
                }
            }).on("blur", function () {
                dropdown_menu_obj.css("display", "");

            }).on("click", function () {
                var word = $(this).val(), words;
                if(
                    $.trim(word)!=='' &&
                    word===$(this).attr('alt') &&
                    dropdown_menu_obj.find("table tr").length
                ){
                    return dropdown_menu_obj.show();
                }
                if( dropdown_menu_obj.css('display')!=='none' ) {
                    return;
                }
                if( options.multiWord ) {
                    words = word.split( options.separator || ' ');
                    word = words[words.length-1];
                }
                //是否允许空数据查询
                if( word.length===0 ) {
                    return;
                }
                widget.getData($.trim(word), input_obj);
            });
            //下拉按钮点击时
            input_obj.parent().find("button:eq(0)").attr("data-toggle", "").on("click", function(){
                var display;
                if( dropdown_menu_obj.css("display")==="none" ) {
                    display = "block";
                    if( options.url ) {
                        input_obj.click().focus();
                    } else {
                        widget.refreshDropMenu(input_obj, input_obj.data('ss_'+input_obj.val()), options);
                        widget.adjustDropMenuPos(input_obj, dropdown_menu_obj, options);
                    }
                } else {
                    display = "none";
                }
                dropdown_menu_obj.css("display", display);
            });
            //列表中滑动时，输入框失去焦点
            dropdown_menu_obj.on("mouseenter", function(){
                $(this).show();
            }).on("mouseleave", function(){
                input_obj.focus();
            });
        });
    };
    //调整选择菜单位置
    selectSearchObj.prototype.adjustDropMenuPos = function(input_obj, drop_down_menu){
        if( drop_down_menu.is(':visible') ) {
            return;
        }
        //列表对齐方式
        if( options.listAlign==="left" ) {
            if(options.adjustWidth) {
                var x = input_obj.position();
                left = x.left-input_obj.width();
            } else {
                left = input_obj.siblings("div").width() - input_obj.parent().width();
            }
            drop_down_menu.css({
                "left": left,
                "right": "auto"
            });
        }
        else if( options.listAlign==="right" ) {
            drop_down_menu.css({
                "left": "auto",
                "right": "0"
            });
        }
    };
    selectSearchObj.prototype.getData = function(keyword, input_obj) {
        var widget = this;
        var data, valid_data, filterData = {value:[]}, i, obj, URL, len;
        keyword = keyword || "";
        if( keyword=='' )
        {
            if( widget.checkData(options.initData) &&  options.initData.value.length!=0 )
            {
                widget.refreshDropMenu(input_obj, options.initData);
                input_obj.trigger("onDataRequestSuccess", options.initData);
                return;
            }
        }
        if( typeof input_obj.data("ss_"+keyword)==='undefined' )
        {
            var dataType = options.jsonp ? 'jsonp' : "json";
            URL = options.url + keyword;
            ajaxDelay.request({
                'url':URL,
                'mode':'ajax',
                'isAsync':true,
                'dataType': dataType,
                'timeout': 3000
            }).done(function(result) {
                widget.refreshDropMenu(input_obj, result);
                input_obj.trigger("onDataRequestSuccess", result);
                if (options.cacheData ) {
                    input_obj.data("ss_"+keyword, result)
                }
            }).fail(widget.handlerError);
        }
        /**没有给出url 参数，则从 data 参数获取或自行构造data帮助内容 **/
        else
        {
            data = input_obj.data("ss_" + keyword);
            valid_data = widget.checkData(data);
            //本地的 data 数据，则在本地过滤
            if(valid_data) {
                if(!keyword) {
                    filterData = data;
                }
                else {
                    len = data.value.length;
                    for(i=0; i<len; i++) {
                        for(obj in data.value[i]) {
                            if (
                                $.trim(data.value[i][obj]) &&
                                widget.inEffectiveFields(obj) &&
                                (data.value[i][obj].toString().indexOf(keyword) !== -1 || keyword.indexOf(data.value[i][obj]) !== -1)
                            ){
                                filterData.value.push(data.value[i]);
                                break;
                            }
                        }
                    }
                }
            }
            widget.refreshDropMenu(input_obj, filterData);
        }
    };
    //用来追踪函数的调用轨迹
    selectSearchObj.prototype.handlerError = function(e1, e2){
        console.trace(e1);
        if(e2) {
            console.trace(e2);
        }
    };
    // 数据格式检测
    // 检测 ajax 返回成功数据或 data 参数数据是否有效
    // data 格式：{"value": [{}, {}...]}
    //var checkData = function(data){return 'sss';};
    selectSearchObj.prototype.checkData = function(data){
        var is_empty = true;
        for( var o in data )
        {
            if( o==='value' )
            {
                is_empty = false;
                break;
            }
        }
        if( is_empty )
        {
            this.handlerError("返回数据格式错误!");
            return false;
        }
        if( data.value.length===0 )
        {
            return false;
        }
        return data;
    };
    //验证对象是否符合条件
    selectSearchObj.prototype.checkInput = function(target){
        var input_obj = $(target);
        var dropdown_menu_obj = input_obj.parent().find("ul.dropdown-menu");
        var data = input_obj.data('selectSearchObj');
        if(dropdown_menu_obj.length === 0)
        {
            return false;
        }
        //是否已经初始化的检测
        if(data){
            return false;
        }
        input.data('selectSearchObj',{target: target, options: options});
        return true;
    };
    //判断字段名是否在 effectiveFields 配置项中  effectiveFields 为空时始终返回 TRUE
    selectSearchObj.prototype.inEffectiveFields = function(filed){
        if(
            $.isArray(options.effectiveFields) &&
            options.effectiveFields.length > 0 &&
            $.inArray(filed, options.effectiveFields) === -1
        )
        {
            return false;
        }
        return true;
    };
    //获取当前tr列的关键字数据
    selectSearchObj.prototype.getPointKeyword = function(list){
        var data = {};
        data.id = list.attr('data-id');
        data.key = list.attr('data-key');
        return data;
    };
    //解除所有列表 hover 样式
    selectSearchObj.prototype.unHoverAll = function(dropdown_menu_obj){
        dropdown_menu_obj.find('tr.' + options.listHoverCSS).removeClass(options.listHoverCSS);
    };
    //获取当前tr列的关键字数据
    selectSearchObj.prototype.getPointKeyword = function(list){
        var data = {};
        data.id = list.attr('data-id');
        data.key = list.attr('data-key');
        return data;
    };
    //调整滑动条
    selectSearchObj.prototype.adjustScroll = function(input_obj, dropdown_menu_obj){
        var hover_obj = input_obj.parent().find("tbody tr." + options.listHoverCSS), pos, maxHeight;
        if( hover_obj.length>0 ){
            pos = (hover_obj.index() + 3) * hover_obj.height();
            maxHeight = Number(dropdown_menu_obj.css("max-height").replace("px", ""));
            if( pos>maxHeight || dropdown_menu_obj.scrollTop() > maxHeight) {
                dropdown_menu_obj.scrollTop(pos - maxHeight);
            } else {
                dropdown_menu_obj.scrollTop(0);
            }
        }
    };
    //设置输入框背景色  当设置了 indexId，而输入框的 data-id 为空时，输入框加载警告色
    selectSearchObj.prototype.setBackground = function(input_obj) {
        var inputbg, bg, warnbg;
        if( !options.idField ){
            return input_obj;
        }
        inputbg = input_obj.css("background-color").replace(/ /g, "").split(",", 3).join(",");
        bg = "rgba(255,255,255,0.1)";
        warnbg = "rgba(255,255,0,0.1)";
        if( !input_obj.val() || input_obj.attr("data-id") ) {
            return input_obj.css("background", bg);
        }
        //自由输入的内容，设置背景色
        if( -1===warnbg.indexOf(inputbg) ) {
            input_obj.trigger("onUnsetSelectValue"); //触发取消data-id事件
            input_obj.css("background", warnbg);
        }
        return input_obj;
    };

    selectSearchObj.prototype.getDropDownMenu = function(input_obj){
        if( input_obj.parent().find("ul.dropdown-menu").length>0 ) {
            drop_down_menu = input_obj.parent().find("ul.dropdown-menu");
        }
        else
        {
            drop_down_menu = input_obj.parent().find("ul");
            //判断是否存在ul对象
            if( drop_down_menu.length==0 ) {
                tmp = '<div class="input-group-btn">'+
                        '<ul class="dropdown-menu dropdown-menu-right" role="menu">'+
                        '</ul>'+
                    '</div>';
                input_obj.after(tmp);delete tmp;
                drop_down_menu = input_obj.parent().find("ul");
            }
        }
        return drop_down_menu;
    },
    //下拉框刷新
    selectSearchObj.prototype.refreshDropMenu = function(input_obj, data) {
        var drop_down_menu, len, i, j, index = 0,
            html = ['<table class="table table-condensed">'],
            thead, tr,
            idValue, keyValue; //作为输入框 data-id 和内容的字段值;
        var widget = this;

        drop_down_menu = this.getDropDownMenu(input_obj);

        if( !widget.checkData(data) || (len = data.value.length)===0 ){
            drop_down_menu.empty().hide();
            return input_obj;
        }
        //生成表头
        if( options.showHeader ) {
            thead = "<thead><tr style='height:35px;'>";
            for( j in data.value[0] ) {
                if( this.inEffectiveFields(j)===false ) {
                    continue;
                }
                if( index===0 ) {
                    //表头第一列记录总数
                    thead += '<th>' + (options.effectiveFieldsAlias[j] || j) + "(" + len + ")" + '</th>';
                } else {
                    thead += '<th>' + (options.effectiveFieldsAlias[j] || j) + '</th>';
                }
                index++;
            }
            thead += "</tr></thead>";
            html.push(thead);
        }
        html.push("<tbody>");
        //按列加数据
        for( i = 0; i<len; i++ ) {
            tr = "";
            idValue = data.value[i][options.idField] || "";
            keyValue = data.value[i][options.keyField] || "";
            index = 0;
            for( j in data.value[i] ) {
                if(!keyValue && options.indexKey===index) {
                    keyValue = data.value[i][j];
                }
                if(!idValue && options.indexId===index) {
                    idValue = data.value[i][j];
                }
                //过滤无效字段
                if( this.inEffectiveFields(j)===false ) {
                    continue;
                }
                if(keyValue && options.indexKey===index){
                    tr +='<td data-name="' + j + '">' + data.value[i][j] + '</td>';
                }
                index++;
            }
            tr = '<tr data-index="' + i + '" data-id="' + idValue +
                '" data-key="' + keyValue +'">' + tr + '</tr>';

            html.push(tr);
        }
        html.push('</tbody></table>');
        drop_down_menu.html(html.join("")).show();
        this.listEventBind(input_obj, drop_down_menu);

        drop_down_menu.find("table:eq(0)").css("margin-bottom", "8px");
        drop_down_menu.find("table td").css("line-height", "2");
        //scrollbar 存在时，调整 padding
        if(
            drop_down_menu.css("max-height") &&
            Number(drop_down_menu.css("max-height").replace("px", "")) < Number(drop_down_menu.find("table:eq(0)").css("height").replace("px", "")) &&
            Number(drop_down_menu.css("min-width").replace("px", "")) < Number(drop_down_menu.css("width").replace("px", ""))
        ){
            drop_down_menu.css("padding-right", "20px").find("table:eq(0)").css("margin-bottom", "8px");
        }
        return input_obj;
    };
    //绑定列表的 mouseover 事件监听
    selectSearchObj.prototype.listEventBind = function(input_obj, drop_down_menu){
        var widget = this;
        drop_down_menu.find('tbody tr').each(function (e) {
            $(this).off('mouseenter').on("mouseenter", function (e) {
                widget.unHoverAll(drop_down_menu);
                $(this).addClass(options.listHoverCSS);
            }).off('mousedown').on("mousedown", function (e) {
                widget.setValue(input_obj, widget.getPointKeyword($(this)));
                widget.setBackground(input_obj);
            });
        });
    };
    //设置取得的值
    selectSearchObj.prototype.setValue = function(input_obj, keywords){
        var _keywords = keywords || {},
            id = _keywords.id || "",
            key = _keywords.key || "",
            inputValList,
            inputIdList;

        //多关键字支持，只设置 val
        if( options.multiWord ) {
            inputValList = input_obj.val().split(options.separator || ' ');
            inputValList[inputValList.length - 1] = key;
            input_obj.val(inputValList.join(options.separator || ' ')).focus();
        }
        else
        {
            input_obj.attr("data-id", id).focus().val(key);
        }
        input_obj.trigger("onSetSelectValue", _keywords);
    };
    return new selectSearchObj(opts);
}

///////////////////////////////////////////////////////////搜索下拉框 end//////////////////////////////////////////////////////////////////////////////////

///////////////////////////////////////////////////////////tag标签管理 begin//////////////////////////////////////////////////////////////////////////////////
/**
 * https://github.com/bootstrap-tagsinput/bootstrap-tagsinput
 * @param opts
 */
$.fn.tagInput = function(opts) {
    var widget = this;
    var defaultOptions = {
        tagClass: function(item) {
          return 'label label-info';
        },
        itemValue: function(item) {
          return item ? item.toString() : item;
        },
        itemText: function(item) {
          return this.itemValue(item);
        },
        freeInput: true,
        addOnBlur: true,
        maxTags: undefined,
        maxChars: undefined,
        minWidth: false,
        confirmKeys: [13, 44],
        onTagExists: function(item, $tag) {
          $tag.hide().fadeIn();
        },
        trimValue: false,
        allowDuplicates: false,
        selectSearchOpt: false
    };
    var tagInputObj = function(element, options) {
        this.itemsArray = [];

        this.$element = $(element);
        this.$element.hide();
        this.objectItems = options && options.itemValue;
        this.placeholderText = element.hasAttribute('placeholder') ? this.$element.attr('placeholder') : '';
        this.inputSize = Math.max(1, this.placeholderText.length);
        this.$container = $('<div class="bootstrap-tagsinput"></div>');
        this.$input = $('<input data type="text" placeholder="' + this.placeholderText + '"/>').appendTo(this.$container);
        this.$element.after(this.$container);
        var inputWidth = (this.inputSize < 3 ? 3 : this.inputSize) + "em";
        this.$input.get(0).style.cssText = "width: " + inputWidth + " !important;";
        if( options && options.minWidth!=undefined ){
            this.$container.css('min-width', options.minWidth);
        }
        this.build(options);
    };
    tagInputObj.prototype = {
        constructor: tagInputObj,

        add: function(item, dontPushVal){
            var self = this;
            if( self.options.maxTags && self.itemsArray.length>=self.options.maxTags )
                return;
            if (item !== false && !item)
                return;
            // Trim value
            if (typeof item === "string" && self.options.trimValue)
                item = $.trim(item);

            if (typeof item === "object" && !self.objectItems)
                throw("Can't add objects when itemValue option is not set");

            // Ignore strings only containg whitespace
            if (item.toString().match(/^\s*$/))
                return;

            if (typeof item === "string" && this.$element[0].tagName === 'INPUT'){
                var items = item.split(',');
                if( items.length>1 ) {
                    for( var i = 0; i < items.length; i++ ) {
                        this.add(items[i], true);
                    }
                    if (!dontPushVal)
                        self.pushVal();
                    return;
                }
            }

            var itemValue = self.options.itemValue(item),
                itemText = self.options.itemText(item),
                tagClass = self.options.tagClass(item);
            // Ignore items allready added
            var existing = $.grep(self.itemsArray, function(item) { return self.options.itemValue(item) === itemValue; } )[0];
            if (existing && !self.options.allowDuplicates){
                if (self.options.onTagExists) {
                    var $existingTag = $(".tag", self.$container).filter(function() { return $(this).data("item") === existing; });
                    self.options.onTagExists(item, $existingTag);
                }
                return;
            }
            // if length greater than limit
            if (self.items().toString().length + item.length + 1 > self.options.maxInputLength)
                return;

            self.itemsArray.push(item);

            //add a tag element
            var $tag = $('<span class="tag ' + htmlEncode(tagClass) + '">' + htmlEncode(itemText) + '<span data-role="remove"></span></span>');
            $tag.data('item', item);
            self.findInputWrapper().before($tag);
            $tag.after(' ');

            if (!dontPushVal)
                self.pushVal();

            // Add class when reached maxTags
            if (self.options.maxTags === self.itemsArray.length || self.items().toString().length === self.options.maxInputLength)
                self.$container.addClass('bootstrap-tagsinput-max');

            self.$element.trigger($.Event('itemAdded', { item: item }));
        },
        /**
        * Returns the items added as tags
        */
        items: function() {
          return this.itemsArray;
        },

        pushVal: function(){
            var self = this,
                val = $.map(self.items(), function(item) {
                        return self.options.itemValue(item).toString();
                });
            self.$element.val(val, true).trigger('change');
        },
        /**
        * Initializes the tags input behaviour on the element
        */
        build: function(options) {
            var self = this;
            self.options = $.extend({}, defaultOptions, options);
            if (self.objectItems)
                self.options.freeInput = false;
            makeOptionItemFunction(self.options, 'itemValue');
            makeOptionItemFunction(self.options, 'itemText');
            makeOptionFunction(self.options, 'tagClass');

            //添加下拉搜索框提示
            if(self.options.selectSearchOpt) {
                self.$input.selectSearch(self.options.selectSearchOpt);
            }

            self.$container.on('click', $.proxy(function(event) {
                if( !self.$element.attr('disabled') ) {
                    self.$input.removeAttr('disabled');
                }
                self.$input.focus();
            }, self));

            if( self.options.addOnBlur && self.options.freeInput ) {
                self.$input.on('focusout', $.proxy(function(event) {
                    self.add(self.$input.val());
                    self.$input.val('');
                }, self));
            }

            self.$container.on('keydown', 'input', $.proxy(function(event) {
                var $input = $(event.target),
                    $inputWrapper = self.findInputWrapper();
                if (self.$element.attr('disabled')) {
                  self.$input.attr('disabled', 'disabled');
                  return;
                }
                switch (event.which) {
                    // BACKSPACE
                    case 8:
                        var prev = $inputWrapper.prev();
                        if(prev){
                            if($input.val()==''){
                                self.remove(prev.data('item'));
                            }
                        }
                        break;
                    // DELETE
                    case 46:
                        var next = $inputWrapper.next();
                        if(next){
                           self.remove(next.data('item'));
                        }
                        break;
                    //// LEFT ARROW
                    //case 37:
                    //    var $prevTag = $inputWrapper.prev();
                    //    $prevTag.before($inputWrapper);
                    //    $input.focus();
                    //    break;
                    //// RIGHT ARROW
                    //case 39:
                    //    var $nextTag = $inputWrapper.next();
                    //    if($input.val().length===0 && $nextTag[0]){
                    //        $nextTag.after($inputWrapper);
                    //        $input.focus();
                    //    }
                    //    break;
                    case 13:
                        self.add(self.$input.val());
                        self.$input.val('');
                        self.$input.focus();
                        break;
                    case 9: //tag key
                        if(self.$input.val()!=''){
                            self.add(self.$input.val());
                            self.$input.val('');
                            var isie = (document.all) ? true:false;
                            if(isie) {
                              event.keyCode=0;
                              event.returnValue=false;
                            } else {
                                event.which = 0;
                                event.preventDefault();
                            }
                        }

                        break;
                    default:
                        // ignore
                }
                var textLength = $input.val().length,
                    wordSpace = Math.ceil(textLength / 5),
                    size = textLength + wordSpace + 1;
                $input.attr('size', Math.max(this.inputSize, $input.val().length));
            }, self));

            // Remove icon clicked
            self.$container.on('click', '[data-role=remove]', $.proxy(function(event) {
                if (self.$element.attr('disabled')) {
                  return;
                }
                self.remove($(event.target).closest('.tag').data('item'));
            }, self));

            // Only add existing value as tags when using strings as tags
            if( self.options.itemValue===defaultOptions.itemValue ){
                if (self.$element[0].tagName === 'INPUT') {
                    self.add(self.$element.val());
                }
            }

        },
        /**
        * Removes the given item. Pass true to dontPushVal to prevent updating the
        * elements val()
        */
        remove: function(item, dontPushVal){
            var self = this;
            if(self.objectItems) {
                if (typeof item === "object")
                  item = $.grep(self.itemsArray, function(other) { return self.options.itemValue(other) ==  self.options.itemValue(item); } );
                else
                  item = $.grep(self.itemsArray, function(other) { return self.options.itemValue(other) ==  item; } );

                item = item[item.length-1];
            }
            if( item ) {
                var beforeItemRemoveEvent = $.Event('beforeItemRemove', { item: item, cancel: false });
                self.$element.trigger(beforeItemRemoveEvent);
                if (beforeItemRemoveEvent.cancel)
                  return;

                $('.tag', self.$container).filter(function() { return $(this).data('item') === item; }).remove();

                if( $.inArray(item, self.itemsArray)!==-1 )
                    self.itemsArray.splice($.inArray(item, self.itemsArray), 1);
            }
            if (!dontPushVal)
                self.pushVal();

            // Remove class when reached maxTags
            if (self.options.maxTags > self.itemsArray.length)
                self.$container.removeClass('bootstrap-tagsinput-max');

            self.$element.trigger($.Event('itemRemoved',  { item: item }));
        },
        /**
         * Returns the element which is wrapped around the internal input. This
         * is normally the $container, but typeahead.js moves the $input element.
         */
        findInputWrapper: function() {
          var elt = this.$input[0],
              container = this.$container[0];
          while(elt && elt.parentNode !== container)
            elt = elt.parentNode;

          return $(elt);
        }
    };

    /**
    * HtmlEncodes the given value
    */
    var htmlEncodeContainer = $('<div />');
    function htmlEncode(value) {
        if (value) {
          return htmlEncodeContainer.text(value).html();
        } else {
          return '';
        }
    }
    function makeOptionItemFunction(options, key) {
        if (typeof options[key] !== 'function') {
          var propertyName = options[key];
          options[key] = function(item) { return item[propertyName]; };
        }
    }
    function makeOptionFunction(options, key) {
        if (typeof options[key] !== 'function') {
          var value = options[key];
          options[key] = function() { return value; };
        }
    }

    var autoload = function(opts){
        var results = [];
        widget.each(function() {
            var tagsinput = $(this).data('tagsinput');
            // Initialize a new tags input
            if (!tagsinput) {
                tagsinput = new tagInputObj(this, opts);
                $(this).data('tagsinput', tagsinput);
                results.push(tagsinput);
                // Init tags from $(this).val()
                $(this).val($(this).val());
            } //else if(tagsinput[arg1] !== undefined) {
            //}
        });
        return results;
    };
    return autoload(opts);
}
//-----------------------------------------------------------tag标签管理 end----------------------------------------------------------------------------------

///////////////////////////////////////////////////////////ajax节制型提交 begin////////////////////////////////////////////////////////////////////
var ajaxDelay = (function() {
    var jqXhr = {},
        ajaxRequest = {};
    var t;
    var _settings = {
        type: 'GET',
        cache: false,
        success: function() {

        }
    };
    $.ajaxSingle = function (settings) {
        var options = $.extend({ className: 'DEFEARTNAME' }, $.ajaxSettings, settings);
        if(jqXhr[options.className]) {
            jqXhr[options.className].abort();
        }
        jqXhr[options.className] = $.ajax(options);
    };
    $.ajaxQueue = function (settings) {
        var options = $.extend({ className: 'DEFEARTNAME' }, $.ajaxSettings, settings);
        var _complete = options.complete;
        $.extend(options, {
            complete: function () {
                if (_complete)
                    _complete.apply(this, arguments);
                if ($(document).queue(options.className).length > 0) {
                    $(document).dequeue(options.className);
                } else {
                    ajaxRequest[options.className] = false;
                }
            }
        });
        $(document).queue(options.className, function () {
            $.ajax(options);
        });

        if ($(document).queue(options.className).length == 1 && !ajaxRequest[options.className]) {
            ajaxRequest[options.className] = true;
            $(document).dequeue(options.className);
        }
    };
    var t;
    $.ajaxSetTimeout = function (settings){
        var options = $.extend({ className: 'DEFEARTNAME', delaytime: 50 }, $.ajaxSettings, settings);
        clearTimeout(t);
        t = setTimeout(function(){
                $.ajax(options);
            }, options.delaytime);
    };
    return {
        request: function(opts) {
            var mode = opts.mode || 'ajax',
                isAsync = opts.isAsync || false;
            if( !opts.hasOwnProperty("mode") ||
                !opts.hasOwnProperty("isAsync") ||
                !opts.hasOwnProperty("url") ) {
                console.trace('缺少参数');
                return false;
            }
            var params = {
                url: opts.url,
                async: opts.isAsync,
                type: opts.type,
                data: opts.data
            };
            if( opts.hasOwnProperty('data') )
            {
                params.data = opts.data;
            }
            if( opts.hasOwnProperty('dataType') )
            {
                params.dataType = opts.dataType;
            }
            if( opts.hasOwnProperty('timeout') )
            {
                params.timeout = opts.timeout;
            }
            if( opts.hasOwnProperty("success") && typeof opts.success==='function' )
            {
                params.success = opts.success;
            }
            return $[mode]($.extend(_settings, params));
        }
    };
}());
///////////////////////////////////////////////////////////ajax节制型提交 end////////////////////////////////////////////////////////////////////

/////////////////////////////////////////////////////////////异步上传文件 begin//////////////////////////////////////////////////////////////////////////////////
//https://github.com/danielm/uploader
$.fn.uploadFile = function(options) {
    var defaults = {
        url: document.URL,
        method: 'POST',
        extraData: {},
        maxFileSize: 0,
        maxFiles: 0,
        allowedTypes: '*',
        validExtensions : ['gif','png','jpg','jpeg'],
        extFilter: null,
        dataType: null,
        fileName: 'file',
        onInit: function(){},
        onFallbackMode: function() {message},
        onNewFile: function(id, file){},
        onBeforeUpload: function(id){},
        onComplete: function(){},
        onUploadProgress: function(id, percent){},
        onUploadSuccess: function(id, data){},
        onUploadError: function(id, message){},
        onFileTypeError: function(file){},
        onFileSizeError: function(file){},
        onFileExtError: function(file){},
        onFilesMaxError: function(file){}
    };
    var UploadFile = function(element, options){
        this.element = $(element);
        this.settings = $.extend({}, defaults, options);
        this.iframe = false;
        if(!this.checkBrowser()){
            //通过iframe上传
            return false;
        }
        this.init();
        return true;
    };
    UploadFile.prototype.iframeUpload = function(){
        var frameName = 'upload_frame_' + Math.round(new Date().getTime() / 1000);
        var iframe = $('<iframe style="position:absolute;top:-9999px" />').attr('name', frameName);
        var form = $('<form method="post" style="display:none;" enctype="multipart/form-data" />').attr('name', 'form_' + frameName);
        form.attr("target", frameName).attr('action', this.settings.url);
        // form中增加数据域
        var formHtml = '<input type="file" name="' + this.settings.fileName + '">';
        for(key in this.settings.extraData) {
            formHtml += '<input type="hidden" name="' + key + '" value="' + this.settings.extraData[key] + '">';
        }
        form.append(formHtml);
        iframe.appendTo("body");
        form.appendTo("body");
        // iframe 在提交完成之后
        iframe.load(function() {
            var contents = $(this).contents().get(0);
            var data = $(contents).find('body').html();
            if ('json' == this.settings.dataType) {
                data = window.eval('(' + data + ')');
            }
            this.settings.onComplete(data);
            setTimeout(function() {
                iframe.remove();
                form.remove();
            }, 5000);
        });
         // 文件框
        var fileInput = $('input[type=file][name=' + this.settings.fileName + ']', form);
        fileInput.change(function() {
            form.submit();
        });
        fileInput.click();
        return true;
    };
    UploadFile.prototype.checkBrowser = function()
    {
        if(window.FormData === undefined){
            this.settings.onFallbackMode.call(this.element, 'Browser doesn\'t support Form API');
            return false;
        }
        if(this.element.find('input[type=file]').length > 0){
            return true;
        }
        /*if (!this.checkEvent('drop', this.element) || !this.checkEvent('dragstart', this.element)){
            this.settings.onFallbackMode.call(this.element, 'Browser doesn\'t support Ajax Drag and Drop');
            return false;
        }*/
        return true;
    };
    UploadFile.prototype.init = function()
    {
        var widget = this;
        widget.queue = new Array();
        widget.queuePos = -1;
        widget.queueRunning = false;
        // -- Drag and drop event
        /*widget.element.on('drop', function (evt){
          evt.preventDefault();
          var files = evt.originalEvent.dataTransfer.files;
          widget.queueFiles(files);
        });*/
        //-- Optional File input to make a clickable area
        widget.element.find('input[type=file]').on('change', function(evt){
          var files = evt.target.files;
          widget.queueFiles(files);
          $(this).val('');
        });
        this.settings.onInit.call(this.element);
    };
    UploadFile.prototype.queueFiles = function(files)
    {
        var j = this.queue.length;
        for (var i= 0; i < files.length; i++)
        {
          var file = files[i];
          // Check file size
          if((this.settings.maxFileSize > 0) && (file.size > this.settings.maxFileSize)){
            this.settings.onFileSizeError.call(this.element, file);
            continue;
          }
          // Check file type
          if((this.settings.allowedTypes != '*') && !file.type.match(this.settings.allowedTypes)){
            this.settings.onFileTypeError.call(this.element, file);
            continue;
          }
          // Check file extension
          if(this.settings.extFilter != null){
            var extList = this.settings.extFilter.toLowerCase().split(';');
            var ext = file.name.toLowerCase().split('.').pop();
            if($.inArray(ext, extList) < 0){
              this.settings.onFileExtError.call(this.element, file);
              continue;
            }
          }
          // Check max files
          if(this.settings.maxFiles > 0) {
            if(this.queue.length >= this.settings.maxFiles) {
              this.settings.onFilesMaxError.call(this.element, file);
              continue;
            }
          }
          this.queue.push(file);
          var index = this.queue.length - 1;
          this.settings.onNewFile.call(this.element, index, file);
        }
        // Only start Queue if we haven't!
        if(this.queueRunning){
          return false;
        }
        // and only if new Failes were successfully added
        if(this.queue.length == j){
          return false;
        }
        this.processQueue();
        return true;
    };
    UploadFile.prototype.processQueue = function()
    {
        var widget = this;
        widget.queuePos++;
        if(widget.queuePos >= widget.queue.length){
          // Cleanup
          widget.settings.onComplete.call(widget.element);
          // Wait until new files are droped
          widget.queuePos = (widget.queue.length - 1);
          widget.queueRunning = false;
          return;
        }
        var file = widget.queue[widget.queuePos];
        // Form Data
        var fd = new FormData();
        fd.append(widget.settings.fileName, file);
        // Return from client function (default === undefined)
        var can_continue = widget.settings.onBeforeUpload.call(widget.element, widget.queuePos);
        // If the client function doesn't return FALSE then continue
        if( false === can_continue ) {
          return;
        }
        // Append extra Form Data
        $.each(widget.settings.extraData, function(exKey, exVal){
          fd.append(exKey, exVal);
        });
        widget.queueRunning = true;
        // Ajax Submit
        $.ajax({
          url: widget.settings.url,
          type: widget.settings.method,
          dataType: widget.settings.dataType,
          data: fd,
          cache: false,
          contentType: false,
          processData: false,
          forceSync: false,
          xhr: function(){
            var xhrobj = $.ajaxSettings.xhr();
            if(xhrobj.upload){
              xhrobj.upload.addEventListener('progress', function(event) {
                var percent = 0;
                var position = event.loaded || event.position;
                var total = event.total || e.totalSize;
                if(event.lengthComputable){
                  percent = Math.ceil(position / total * 100);
                }
                widget.settings.onUploadProgress.call(widget.element, widget.queuePos, percent);
              }, false);
            }
            return xhrobj;
          },
          success: function (data, message, xhr){
              widget.settings.onUploadSuccess.call(widget.element, widget.queuePos, data, file);
          },
          error: function (xhr, status, errMsg){
              widget.settings.onUploadError.call(widget.element, widget.queuePos, errMsg);
          },
          complete: function(xhr, textStatus){
            widget.processQueue();
          }
        });
    }
    // -- Disable Document D&D events to prevent opening the file on browser when we drop them
    $(document).on('dragenter', function (e) { e.stopPropagation(); e.preventDefault(); });
    $(document).on('dragover', function (e) { e.stopPropagation(); e.preventDefault(); });
    $(document).on('drop', function (e) { e.stopPropagation(); e.preventDefault(); });
    var pluginName = 'tool-Uploader';
    return this.each(function(){
      if(!$.data(this, pluginName)){
        $.data(this, pluginName, new UploadFile(this, options));
      }
    });
}
$.uploadFileExt = $.extend({
    addFile: function(id, i, css) {
        var obj = $(id);
        var template = '<div class="progress progress-striped active '+css+'">'+
                           '<div class="progress-bar" role="progressbar" style="width: 0%;">'+
                               '<span class="sr-only">0% Complete</span>'+
                           '</div>'+
                       '</div>';
        var i = obj.attr('file-counter');
        i++;
        obj.attr('file-counter', i);
        obj.append(template);
    },
    updateFileProgress: function(i, percent, id) {
		$(id).find('div.progress-bar').width(percent);
		$(id).find('span.sr-only').html(percent + ' Complete');
	},
    humanizeSize: function(size) {
      var i = Math.floor( Math.log(size) / Math.log(1024) );
      return ( size / Math.pow(1024, i) ).toFixed(2) * 1 + ' ' + ['B', 'kB', 'MB', 'GB', 'TB'][i];
    }
}, $.uploadFileExt);
/////////////////////////////////////////////////////////////异步上传文件 end//////////////////////////////////////////////////////////////////////////////////

/**
 * 判断请求地址是否正确
 * @param str_url
 * @returns {boolean}
 * @constructor
 */
function IsURL(url){
    if(url)
    {
        var strRegex = "^((https|http):\/\/)?"
        + "(((([0-9]|1[0-9]{2}|[1-9][0-9]|2[0-4][0-9]|25[0-5])[.]{1}){3}([0-9]|1[0-9]{2}|[1-9][0-9]|2[0-4][0-9]|25[0-5]))" // IP形式的URL- 199.194.52.184
        + "|"
        + "([0-9a-zA-Z\u4E00-\u9FA5\uF900-\uFA2D-]+[.]{1})+[a-zA-Z-]+)" // DOMAIN（域名）形式的URL
        + "|"
        + "(localhost)"
        + "(:[0-9]{1,4})?" // 端口- :80
        + "((/?)|(/[0-9a-zA-Z_!~*'().;?:@&=+$,%#-]+)+/?)$";
        var re = new RegExp(strRegex);
        return re.test(url);
    }
}
/** 判断是否为图片 **/
function IsImg( str )
{
    str = JSON.stringify(str);
    if( str=='' )
    {
        return false;
    }
    if( str.indexOf(".")<=0 )
    {
        return false;
    }
    var tmp = str.toLocaleLowerCase().split('.');
    if( tmp[tmp.length-1]=='gif'|| tmp[tmp.length-1]=='jpg'|| tmp[tmp.length-1]=='bmp' || tmp[tmp.length-1]=='jpeg' || tmp[tmp.length-1]=='png' )
    {
        return true;
    }
    return false;
}
/** 随机字符串 **/
function getRndStr(k)
{
	var s=[];
	var a=parseInt(Math.random()*25)+(Math.random()>0.5?65:97);
	for (var i=0;i<k;i++)
	{s[i]=Math.random()>0.5?parseInt(Math.random()*9):String.fromCharCode(parseInt(Math.random()*25)+(Math.random()>0.5?65:97));}
	return s.join("");
}
/** 选中所有checkbox **/
function checkAll(obj, name)
{
	 var checkboxs = document.getElementsByName(name);
	 for(var i=0;i<checkboxs.length;i++)
	 {
		 checkboxs[i].checked = obj.checked;
	 }
}
/** 跳转 **/
function scrollTo(id) {
    var pos = $('#' + id).offset().top;
    if( typeof arguments[1]!='undefined' && !isNaN(arguments[1])){
        pos = pos + parseFloat(arguments[1])
    }
	$("html,body").animate({
		scrollTop : pos
	}, 600);
	return false;
}

/**
 * 回到顶部
 */
var toTopAnchor = function(){
    $("head:eq(0)").append(
        "<style> \
            .backToTop {            \
                position:fixed;     \
                bottom:0px;         \
                right:152px!important;\
                border: 1px solid #fff; \
                z-index: 100000;   \
                float: right; \
                background-color: #d9edf7; \
                background-repeat: repeat-x; \
                height: 30px;       \
                line-height: 30px;  \
                width: 30px;        \
                border-radius: 5px 5px 5px 5px; \
                text-align:center;  \
                cursor: pointer;    \
            }                       \
        </style>"
    );
    var $backToTopEle = $('<div class="backToTop"><span class="glyphicon glyphicon-arrow-up" aria-hidden="true"></span></div>').appendTo($("body"))
        .attr("title", '返回顶部').click(function() {
            $("html, body").animate({ scrollTop: 0 }, 120);
    }), $backToTopFun = function() {
        var st = $(document).scrollTop(), winh = $(window).height();
        (st > 100)? $backToTopEle.fadeIn(600): $backToTopEle.fadeOut(600);
        //IE6下的定位
        if (!window.XMLHttpRequest) {
            $backToTopEle.css("top", st + winh - 166);
        }
    };
    $(window).on("scroll", $backToTopFun);
    $backToTopFun();
};

/**
 *  回到描点
 */
$.fn.toAnchor = function(options){
    var defaults = {
        ieFreshFix: true,
        anchorSmooth: true,
        anchortag: "anchor",
        animateTime: 1000
    };
    var sets = $.extend({}, defaults, options || {});
    //修复IE下刷新锚点失效的问题
    if(sets.ieFreshFix){
        var url = window.location.toString();
        var id = url.split("#")[1];
        if(id){
            var t = $("#"+id).offset().top;
            $(window).scrollTop(t);
        }
    }
    //点击锚点跳转
    $(this).each(function(){
        $(this).find("a").click(function(){
            var aim = $(this).attr(sets.anchortag).replace(/#/g,"");	//跳转对象id
            if( $("#"+aim).offset()==null )
            {
                return false;
            }
            var pos = $("#"+aim).offset().top;
            if(sets.anchorSmooth){
                //平滑
                $("html,body").animate({scrollTop: pos}, sets.animateTime);
            }else{
                $(window).scrollTop(pos);
            }
            return false;
        });
    });
};

/**
 * 点击放大图片
 */
$.fn.imgZoom = function() {
    $(this).on('click', function(){
        var max_img = $(this).attr('data-href');
        var view_img = $(this).attr('data-rel')==="undefined" ? $(this).attr('data-rel') : max_img;
        if( $(this).find('.loading').length==0 )
            $(this).append('<span class="loading" title="Loading..">Loading..</span>');
        imgTool($(this), max_img, view_img);
        return false;
    });
    var loadImg = function(url, fn) {
        var img = new Image();
        img.src = url;
        if (img.complete) {
            fn.call(img);
        } else {
            img.onload = function() {
                fn.call(img);
            };
        }
    };
    var imgTool = function(on, max_img, view_img) {
        var width = 0, height = 0,
        tool = function(){
            on.find('.loading').remove();
            on.hide();
            if( on.next('.imgZoomBox').length!=0 ){
                return on.next('.imgZoomBox').show();
            }
            var max_width = on.parent().innerWidth();
            var max_height = on.parent().innerHeight();
            var real_width = on.attr('data-width');
            var real_height = on.attr('data-height');

            if( max_width>width ){
                width = real_width<max_width ? real_width : max_width;
            }
            if( max_height>height ){
                height = real_height<max_height ? real_height : max_height;
            }
            var html = '<div class="imgZoomBox">' +
                            '<div class="tool">' +
                                '<a class="hideImg" href="javascript:;" title="收起">收起</a>' +
                                '<a class="imgLeft" href="javascript:;" title="向左转">向左转</a>' +
                                '<a class="imgRight" href="javascript:;" title="向右转">向右转</a>' +
                                '<a class="viewImg" href="'+ view_img + '" title="查看原图">查看原图</a>' +
                            '</div>' +
                            '<a href="'+ view_img + '" class="maxImgLink">' +
                                '<img class="maxImg" style="width:'+width+'; height:'+height+';" src="' + max_img + '" />' +
                            '</a>' +
                        '</div>';
            on.after(html);
            var box = on.next('.imgZoomBox');
            box.hover(function() {
                box.addClass('js_hover');
            }, function() {
                box.removeClass('js_hover');
            });
            box.find('a').bind('click', function() {
                if($(this).hasClass('hideImg') || $(this).hasClass('maxImgLink')) {
                    box.hide();
                    box.prev().show();
                }
                if($(this).hasClass('imgLeft')) {
                    box.find('.maxImg').rotate('left');
                }
                if($(this).hasClass('imgRight')) {
                    box.find('.maxImg').rotate('right');
                }
                if($(this).hasClass('viewImg'))
                    window.open(view_img);
                return false;
            });
        };
        loadImg(max_img, function() {
            width = this.width;
            height = this.height;
            tool();
        });
        $.fn.rotate = function(p) {
            var img = $(this)[0], n = img.getAttribute('step');
            //if (!this.data('width') && !$(this).data('height')) {
            //    this.data('width', img.width);
            //    this.data('height', img.height);
            //}
            if(n==null) {
                n = 0;
            }
            if(p=='left') {
                (n==3) ? n = 0 : n++;
            } else if(p=='right') {
                (n==0) ? n = 3 : n--;
            }
            $(img).attr('step', n);
            if(document.all) {
                img.style.filter = 'progid:DXImageTransform.Microsoft.BasicImage(rotation=' + n + ')';
                if ($.browser.version == 8) {
                    switch (n) {
                        case 0:
                            this.parent().height('');
                            break;
                        case 1:
                            this.parent().height(this.data('width') + 10);
                            break;
                        case 2:
                            this.parent().height('');
                            break;
                        case 3:
                            this.parent().height(this.data('width') + 10);
                            break;
                    }
                }
            } else {
                var c = this.next('canvas')[0];
                if( this.next('canvas').length==0 ) {
                    this.css({ 'visibility': 'hidden', 'position': 'absolute'});
                    c = document.createElement('canvas');
                    c.setAttribute('class', 'maxImg canvas');
                    img.parentNode.appendChild(c);
                }
                var canvasContext = c.getContext('2d');
                switch(n) {
                    default:
                    case 0:
                        console.log(0);
                        console.log(img.width);
                        console.log(img.height);
                        c.setAttribute('width', img.width);
                        c.setAttribute('height', img.height);
                        canvasContext.rotate(0 * Math.PI / 180);
                        canvasContext.drawImage(img, 0, 0);
                        break;
                    case 1:
                        console.log(1);
                        console.log(img.width);
                        console.log(img.height);
                        c.setAttribute('width', img.height);
                        c.setAttribute('height', img.width);
                        canvasContext.rotate(90 * Math.PI / 180);
                        canvasContext.drawImage(img, 0, -img.height);
                        break;
                    case 2:
                        console.log(2);
                        console.log(img.width);
                        console.log(img.height);
                        c.setAttribute('width', img.width);
                        c.setAttribute('height', img.height);
                        canvasContext.rotate(180 * Math.PI / 180);
                        canvasContext.drawImage(img, -img.width, -img.height);
                        break;
                    case 3:
                        console.log(3);
                        console.log(img.width);
                        console.log(img.height);
                        c.setAttribute('width', img.height);
                        c.setAttribute('height', img.width);
                        canvasContext.rotate(270 * Math.PI / 180);
                        canvasContext.drawImage(img, -img.width, 0);
                        break;
                }
            }
        }
    };
};

/**
 *  获取cookie
 */
function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}
/**
 * 阻止事件发生
 * @param e
 */
function stopPropagation(e) {
    var e = e || window.event;
    var elem = e.target || e.srcElement;
    while (elem) {
        if (elem.className && elem.className.indexOf('dialog')>-1) {
            return;
        }
        elem = elem.parentNode;
    }
}
function stopDefault(e) {
    //如果提供了事件对象，则这是一个非IE浏览器
    if(e && e.preventDefault) {
    　　//阻止默认浏览器动作(W3C)
    　　e.preventDefault();
    } else {
    　　//IE中阻止函数器默认动作的方式
    　　window.event.returnValue = false;
    }
    return false;
}

//刷新验证码
function flushCaptcha(obj) {
    var url = arguments[1];
    if( typeof url=='undefined' ) {
        url = '/common/captcha';
    }
    $.ajax({
             type: "GET",
             url: url,
             data: {_xsrf: getCookie("_xsrf")},
             dataType: "json",
             success: function(data){
                $(obj).attr("src", 'data:image/gif;base64,'+data.res);
             }
         });
}

//判断是否为浮点型
function isFloat(str) {
 for(i=0;i<str.length;i++)  {
    if( (str.charat(i)<"0" || str.charat(i)>"9") && str.charat(i)!='.' ){
        return false;
    }
 }
 return true;
}

jQuery.postJSON = function(url, args, callback) {
    args._xsrf = getCookie("_xsrf");
    return $.ajax({url: url, data: $.param(args), dataType: "text", type: "POST",
            success: function(response) {
        if (callback) callback(eval("(" + response + ")"));
    }, error: function(response) {
        console.log("ERROR:", response)
    }});
};
jQuery.fn.formToDict = function() {
    var fields = this.serializeArray();
    var json = {}
    for (var i = 0; i < fields.length; i++) {
        json[fields[i].name] = fields[i].value;
    }
    if (json.next) delete json.next;
    return json;
};
jQuery.fn.disable = function() {
    this.enable(false);
    return this;
};
jQuery.fn.enable = function(opt_enable) {
    if (arguments.length && !opt_enable) {
        this.attr("disabled", "disabled");
    } else {
        this.removeAttr("disabled");
    }
    return this;
};
//判断是否在可视范围内
$.fn.isOnScreen = function(){
    var win = $(window);
    var viewport = {
        top : win.scrollTop(),
        left : win.scrollLeft()
    };
    viewport.right = viewport.left + win.width();
    viewport.bottom = viewport.top + win.height();
    var bounds = this.offset();
    bounds.right = bounds.left + this.outerWidth();
    bounds.bottom = bounds.top + this.outerHeight();
    return (!(viewport.right < bounds.left || viewport.left > bounds.right || viewport.bottom < bounds.top || viewport.top > bounds.bottom));

};

//输入框内输入限制字符
(function($){
  $.fn.limitTextarea = function(opts){
	  var defaults = {
        maxNumber:140,//允许输入的最大字数
		position:'.maxNum',//提示文字的位置，top：文本框上方，bottom：文本框下方
		onOk:function(){},//输入后，字数未超出时调用的函数
		onOver:function(){}//输入后，字数超出时调用的函数
	  }
	  var option = $.extend(defaults,opts);
	  this.each(function(){
		  var _this = $(this);
		  var fn = function(){
                temp_input_val = _this.val();
                temp_len = 0;
                temp_reg = temp_input_val.match(/\[map\](.*?)\[\/map\]/gi);
                if(null!=temp_reg) {
                    temp_input_val = temp_input_val.replace(/\[map\](.*?)\[\/map\]/gi, '');
                    temp_len = parseInt(temp_reg.length)*2;
                }
			    var extraNumber = option.maxNumber - temp_input_val.length - temp_len;
			    var $info = $(option.position);
                if(extraNumber>=0) {
                    option.onOk();
                    $info.html(extraNumber);
                } else {
                    this.value = this.value.substr(0, option.maxNumber);
                    option.onOver();
                }
		  };
		  //绑定输入事件监听器
		  if(window.addEventListener) { //先执行W3C
			_this.get(0).addEventListener("input", fn, false);
		  } else {
			_this.get(0).attachEvent("onpropertychange", fn);
		  }
		  if(window.VBArray && window.addEventListener) { //IE9
			_this.get(0).attachEvent("onkeydown", function() {
			  var key = window.event.keyCode;
			  (key == 8 || key == 46) && fn();//处理回退与删除
			});
			_this.get(0).attachEvent("oncut", fn);//处理粘贴
		  }
	  });
  }
})(jQuery);

//星星打分
$.fn.slideScore = function(){
    var obj = $(this);
    obj.children("i").hover(function(){
        var obj_i = $(this);
        var data_id = parseInt(obj_i.attr('data-id'));
        obj.children('i').each(function(){
            var tmp = $(this);
            var tmp_id = parseInt(tmp.attr('data-id'));
            if( data_id>=tmp_id ) {
                tmp.removeClass('c_g').addClass('c_r');
            } else {
                tmp.removeClass('c_r').addClass('c_g');
            }
        });

    }).mouseleave(function(){
        var rate_id = obj.attr('data-id');
        if( rate_id==0 ){
            obj.find('i').removeClass('c_r');
        } else {
            obj.children('i').each(function(){
                var tmp = $(this);
                var tmp_id = parseInt(tmp.attr('data-id'));
                if( rate_id>=tmp_id ) {
                    tmp.removeClass('c_g').addClass('c_r');
                } else {
                    tmp.removeClass('c_r').addClass('c_g');
                }
            });
        }
    });
    obj.children("i").on('click', function(){
        var obj_i = $(this);
        var data_id = parseInt(obj_i.attr('data-id'));
        obj.children('i').each(function(){
            var tmp = $(this);
            var tmp_id = parseInt(tmp.attr('data-id'));
            if( data_id>=tmp_id ) {
                tmp.removeClass('c_g').addClass('c_r');
            } else {
                tmp.removeClass('c_r').addClass('c_g');
            }
        });
        if(obj_i.hasClass('c_r') && obj.attr('data-id')==data_id )
        {
            obj.find('i').removeClass('c_r');data_id=0;
            obj.find('i').addClass('c_g');
        }
        obj.attr('data-id', data_id);
    });
};

//渐渐消失提示
function slowOutMsg(type, content, mssec) {
    var color_show = '';
    switch(type) {
        case 'success':
            color_show = '#dff0d8';
            break;
        case 'info':
            color_show = '#d9edf7';
            break;
        case 'warning':
            color_show = '#fcf8e3';
            break;
        case 'danger':
            color_show = '#f2dede';
            break;
        default:
            color_show = '#d9edf7';
            break;
    }
    var div_obj = '<div class="show_msg" >'+content+'</div>';
    $('body').append(div_obj);
    mssec = mssec || 3000;
    var obj = $('.show_msg');
    obj.autoCenter(0, obj.height());
    $('.show_msg').css({'background-color': color_show}).fadeOut(mssec);
}

//div居中
$.fn.autoCenter = function(width, height){
    var screen_width = $(window).width(), screen_height = $(window).height();  //当前浏览器窗口的 宽高
    var scroll_top = $(document).scrollTop(); //获取当前窗口距离页面顶部高度
    var scroll_left = $(document).scrollLeft();
    var obj_left = (screen_width - width)/2 + scroll_left;
    var obj_top = (screen_height - height)/2 + scroll_top;
    $(this).css({'left': obj_left + 'px', 'top': obj_top + 'px','display': 'block'});
};

//获取当前时间
function curentDateTime() {
    var now = new Date();
    var year = now.getFullYear();       //年
    var month = now.getMonth() + 1;     //月
    var day = now.getDate();            //日
    var hh = now.getHours();            //时
    var mm = now.getMinutes();          //分
    var clock = year + "-";
    if(month < 10)
        clock += "0";
    clock += month + "-";

    if(day < 10)
        clock += "0";

    clock += day + " ";

    if(hh < 10)
        clock += "0";

    clock += hh + ":";
    if (mm < 10) clock += '0';
    clock += mm;
    return(clock);
}

//判断是否为拷贝
function interceptKeys(evt) {
    evt = evt||window.event // IE support
    var c = evt.keyCode
    var ctrlDown = evt.ctrlKey||evt.metaKey // Mac support

    // Check for Alt+Gr (http://en.wikipedia.org/wiki/AltGr_key)
    if (ctrlDown && evt.altKey) return true

    // Check for ctrl+c, v and x
    else if (ctrlDown && c==67) return false // c
    else if (ctrlDown && c==86) return false // v
    else if (ctrlDown && c==88) return false // x

    // Otherwise allow
    return true
}
