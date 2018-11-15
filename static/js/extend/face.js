$(function() {
	if($('#face-css').length==0){
		$("head:eq(0)").append("<style id='face-css'>\
								#FaceBox{min-width: 210px;height:auto;position:relative;margin:10px auto;min-height:160px;}	\
								#FaceBox .face:hover,.face.in{background-position:0px -120px;}	\
								#FaceBox img{ border:0 none;display:block;width:25px;height:25px;}	\
								#SmohanFaceBox{ display:block; width:210px; height:277px; position:absolute; top:95px; left:-50px; z-index:9999;}	\
								#SmohanFaceBox .Corner{ display:block; width:28px; height:15px; background:url(/static/img/face/facebg_1.png) -32px -100px no-repeat; position:absolute; left:45px; top:0; z-index:100;}	\
								#SmohanFaceBox .Content{ display:block; width:210px; height:277px; padding:10px; background:#ffffff;border:1px solid #cfcfcf; z-index:99; margin:14px 0px 0px 0px; border-radius:2px;}	\
								#SmohanFaceBox .Content h3{ margin:0; padding:0; width:190px; height:20px; line-height:20px; display:block; font-size:12px; text-align:left;}	\
								#SmohanFaceBox .Content h3 span{ float:left;}	\
								#SmohanFaceBox .Content h3 .close{ height:20px;line-height:20px;display:inline-block; width:16px; height:16px;float:right; cursor:pointer;}	\
								#SmohanFaceBox .Content h3 .close:hover{}	\
								#SmohanFaceBox .Content ul{ margin:5px 0px 0px 0px; padding:0; list-style-type:none;}	\
								#SmohanFaceBox .Content ul li{ display:inline-block; width:26px; height:26px; padding:2px; border:1px solid #f8f8f8; float:left;}	\
								#SmohanFaceBox .Content ul li:hover{ border-color:#6C3;}	\
								#Zones{ display:block; width:696px; height:auto; padding:26px; position:relative; background:#fff; border:2px dashed #cacaca; margin:30px auto; display:none;}\
								</style>");
	}
	$.fn.facebox = function(options) {
		var defaults = {
			Event : "click", //响应事件
			textid : "TextArea", //文本框ID
			imgsrc : "localhost",
			imgs : ""
		};
		var options = $.extend(defaults, options);
		var $btn = $(this);//取得触发事件的ID
		//创建表情框
		var faceimg = '';
		if( options.imgs=='' ) {
			for(i=0;i<60;i++) {  //通过循环创建60个表情，可扩展
				faceimg+='<li><a href="javascript:void(0)"><img src="'+options.imgsrc+(i+1)+'.gif" face="[&'+i+'&]"/></a></li>';
			}
		} else {
			faceimg = options.imgs;
		}

		$(this).after("<div id='SmohanFaceBox'><span class='Corner'></span><div class='Content'><h3><span>常用表情</span><a class='close' title='关闭'>×</a></h3><ul>"+faceimg+"</ul></div></div>");
	     $('#SmohanFaceBox').css("display",'none');//创建完成后先将其隐藏
		//创建表情框结束
		
		var $facepic = $("#SmohanFaceBox li img");
		//BTN触发事件，显示或隐藏表情层
		$btn.on(options.Event,function(e) {
			var box_tmp = $('#SmohanFaceBox');
			box_tmp.css({'top': $btn.position().top+20});
			if(box_tmp.is(":hidden")){
				box_tmp.show(360);
				$btn.addClass('in');
			}else{
				box_tmp.hide(360);
				$btn.removeClass('in');
			}
		});
		//插入表情
		$facepic.off().click(function(){
		     $('#SmohanFaceBox').hide(360);
			 $("#"+options.textid).off().insertContent($(this).attr("face"));
			 $btn.removeClass('in');
		});
		//关闭表情层
		$('#SmohanFaceBox h3 a.close').click(function() {
			$('#SmohanFaceBox').hide(360);
			 $btn.removeClass('in');
		});
		//当鼠标移开时，隐藏表情层，如果不需要，可注释掉
		 $('#SmohanFaceBox').mouseleave(function(){
			 $('#SmohanFaceBox').hide(560);
			 $btn.removeClass('in');
		 });

  };  
  	//光标定位插件
	$.fn.extend({  
		insertContent : function(myValue, t) {  
			var $t = $(this)[0];  
			if (document.selection) {  
				this.focus();  
				var sel = document.selection.createRange();  
				sel.text = myValue;  
				this.focus();  
				sel.moveStart('character', -l);  
				var wee = sel.text.length;  
				if (arguments.length == 2) {  
				var l = $t.value.length;  
				sel.moveEnd("character", wee + t);  
				t <= 0 ? sel.moveStart("character", wee - 2 * t	- myValue.length) : sel.moveStart("character", wee - t - myValue.length);  
				sel.select();  
				}  
			} else if ($t.selectionStart || $t.selectionStart == '0') {  
				var startPos = $t.selectionStart;  
				var endPos = $t.selectionEnd;  
				var scrollTop = $t.scrollTop;  
				$t.value = $t.value.substring(0, startPos) + myValue + $t.value.substring(endPos,$t.value.length);  
				this.focus();  
				$t.selectionStart = startPos + myValue.length;  
				$t.selectionEnd = startPos + myValue.length;  
				$t.scrollTop = scrollTop;  
				if (arguments.length == 2) { 
					$t.setSelectionRange(startPos - t,$t.selectionEnd + t);  
					this.focus(); 
				}  
			} else {                              
				this.value += myValue;                              
				this.focus();  
			}  
		}  
	});
 
	//表情解析
	$.fn.extend({
	  replaceface : function(faces){
		  for(i=0;i<60;i++){
			  faces=faces.replace('<emt>'+ (i+1) +'</emt>','<img src="../../img/face/'+(i+1)+'.gif">');
			  }
		   $(this).html(faces);
		   }
	});
	  
  
});