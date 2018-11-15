$(document).ready(function() {
  $('#summernote').summernote({
      lang: 'zh-CN',
      height: 500,
      toolbar:[
              ['style', ['bold', 'italic', 'underline', 'clear']],
              ['color', ['color']],
              ['para', ['ul', 'ol', 'paragraph']],
              ['insert', ['link', 'picture', 'video']]
      ],
      disableDragAndDrop: false,
      callbacks: {
            onImageUpload: function(files) {
                var $editor = $(this);
                var data = new FormData();
                data.append('note_img', files[0]);
                data.append('_xsrf', getCookie("_xsrf"));
                $.ajax({
                  url: '/ucenter/uploadimg',
                  method: 'POST',
                  data: data,
                  processData: false,
                  contentType: false,
                  success: function(res) {
                      if(res['code']=='success') {
                        $editor.summernote('insertImage', res['res']['url']);
                      } else {
                        slowOutMsg('danger', res['msg']);
                      }
                  }
                });
            },
            onPaste: function (e) {
                var bufferText = ((e.originalEvent || e).clipboardData || window.clipboardData).getData('Text');
                e.preventDefault();
                document.execCommand('insertText', false, $.trim(bufferText));
            },
            onMediaDelete : function($target, editor, $editable) {
                $target.remove();
                $.ajax({
                    url: '/ucenter/deleteimg',
                    method:'post',
                    data:{url:$target[0].src, '_xsrf':getCookie("_xsrf")},
                    success: function(res) {
                        if(res['code']!='success') {
                            slowOutMsg('danger', res['msg']);
                        }
                    }
                });
            },
      }
  });

});

if($('#tags').val()==''){
    $('#tags').val('');
}
//标签管理
var tag_obj = $('#tags').tagInput({maxTags:5, minWidth: '500px', selectSearchOpt:{
            allowNoKeyword: false,
            multiWord: true,
            separator: ",",
            url: url+'/feedback/gettags/?q=',
            indexId: 0,
            indexKey: 1,
            idField: 'id',
            adjustWidth:true,
            keyField: 'name'
}});
//点击标签

//正则过滤富文本编辑内容
function filterContent() {
    var content = $('#summernote').summernote('code');
    tmp_content = content.match(/<(p)[^>]*>([\s\S]*?)(?=<\/\1>)/gi);
    if(tmp_content==null) {
        return content;
    }
    content = tmp_content.join('').split(/<p[^>]*>/)[1];
    if(content=='<br>') {
        content = '';
    }
    return content;
}

//验证编辑内容
function checkNoteContent(){
    if($('#summernote').summernote('isEmpty')){
        return false;
    }
    return true;
}
//发布内容
function publicNoteSubmit()
{
    var title = $.trim($('#title').val());
    var content = $.trim(filterContent());
    var is_open = $("input[name='is_open']:checked").val();
    var is_comment = $("input[name='is_comment']").val();
    var tags = $("#tags").val();
    $('#note-form').formValidate(
        [
            {name: 'title', rules: 'required', display: '标题'},
            {name: 'content', rules: '', customs: [{'method':checkNoteContent, 'message':'内容不能为空', 'param': {} }]},
        ],
        function(errors){
            if(errors.length==0) {
                $.ajax({
                    type: "POST",
                    url: '/ucenter/note',
                    data: {'title': title, 'content': content, 'is_open': is_open, 'is_comment': is_comment, 'tags': tags, _xsrf: getCookie("_xsrf")},
                    dataType:"json",
                    success: function(data) {
                        if( data.code=='success' ) {
                            slowOutMsg('info', '发表成功');
                            window.location.href = '';
                        } else {
                            slowOutMsg('danger', data.msg);
                            return;
                        }
                    },
                    error: function(XMLHttpRequest, textStatus, errorThrown) {
                        slowOutMsg('danger', '系统错误');
                        return;
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

//添加已经存在的tag
function addTagName(name) {
    if( typeof tag_obj[0]!==undefined ){
        tag_obj[0].add(name);
    }
}