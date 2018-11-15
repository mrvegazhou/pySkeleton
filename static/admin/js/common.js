//获取cookie
function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}
//提交表单
function submitFormByAjax(form_id, url){
    $.ajax({
        type: "POST",
        url:url,
        data:$(form_id).serialize(),
        async: false,
        error: function(xhr, ajaxOptions, thrownError) {
            var err = eval("(" + xhr.responseText + ")");
            alert(err.Message);
        },
        success: function(data) {
            data = jQuery.parseJSON(data);
            if(data.code=='success'){
                alert('提交成功！');
            } else{
                alert("提交失败！");
            }
            return data;
        }
    });
}
//ajax请求
function sendAjax(url, datas, success_func, dialog_obj) {
    if(url==''){
        alert('请输入请求地址！');
        return false;
    }
    var _xsrf = getCookie("_xsrf");
    var json = {};
    json['_xsrf'] = _xsrf;
    $.each(datas, function(key, value) {
      json[key] = value;
    });
    var res = '';
    $.ajax({
        type:"POST",
        url:url,
        data:json,
        async:false,
        datatype: "json",
        success:function(data){
            try{
                data = JSON.parse(data);
            } catch (e){
                alert(e);
                return false;
            }
            if( data.code=='success' )
            {
                if(success_func!=''){
                    success_func;
                }
                if(dialog_obj!=''){
                    dialog_obj.dialog( "close" );
                }
            } else if( data.code=='error' ){
                if(data.msg){
                    alert(data.msg);
                }else{
                    alert('服务器错误！');
                }
                if(dialog_obj!=''){
                    dialog_obj.dialog( "close" );
                }
                return false;
            }
            res = data;
        }
    });
    return res;
}
//判断表单数据
function getDataRequireInput(datas, obj, error) {
    var flag = true;
    var chks = '';
    //通过判断是否存在require-data为是否提交的表单
    $("[data-require]", obj).each(function(){
       var msg = $(this).attr('data-require');
       var name = $(this).attr('name');
       var type = $(this).prop("type").toLowerCase();
       if(type=='radio'){
           if($(this).is(':checked')==true){
              var val = $(this).filter(':checked').val();
              datas[name] = val;
           }
       } else if(type=='checkbox'){
           if($(this).prop("checked")==true){
              chks += $(this).val()+',';
              datas[name] = chks.substring(0, chks.length-1);
           }
       } else{
           var val = $(this).val();
           datas[name] = val;
       }
       if(msg!='' && val=='' && error==true)
       {
           alert(msg);
           flag = false;
           return false;
       }
    });
    return datas;
}
//填充数据
function editDataRequireInput(id, url, form) {
    var datas = {act: 'edit-info', id: id};
    form_datas = sendAjax(url, datas, '', '');
    var require_form_obj;
    var arr = '';
    //判断
    if(form!=''){
        require_form_obj = $("[data-require]", form);
    } else{
        require_form_obj = $("[data-require]");
    }
    require_form_obj.each(function(){
        var name = $(this).attr('name');
        var type = $(this).prop("type").toLowerCase();
        if(type=='radio'){
            if($(this).val()==form_datas[name]){
                $(this).attr("checked", true);
            }
        } else if(type=='checkbox'){
            if(arr==''){
                var tmp = form_datas[name];
                arr = tmp.split(',');
            }
            for (var i=0; i<arr.length; i++) {
                if (arr[i] === $(this).val()) {
                    $(this).attr("checked", 'true');
                }
            }
        } else if(type=='select-one'){
            $(this).get(0).value = form_datas[name];
        } else{
            $(this).attr("value", form_datas[name]);
        }
    });
}
//更新表格里的行数据
function updateTableRowData(datas) {
    for(var item in datas){
        var obj = $("#table-td-"+item+"-"+datas['id']);
        if(obj){
            if(item=='status') {
                if(datas['status']==1){
                    obj.html('<span class="label label-sm label-info arrowed arrowed-righ">正常</span>');
                } else if(datas['status']==0){
                    obj.html('<span class="label label-sm label-error arrowed arrowed-righ">禁止</span>');
                }
            } else{
                obj.html(datas[item]);
            }
        }
    }
}
//更新表单窗口操作
function tableEdit(obj){
    var url = $(obj).attr('data-url');
    //填充数据
    var tmp = $(obj).attr('data-action');
    var form = '';
    if($(obj).attr('data-form')){
        form = $('#'+$(obj).attr('data-form'));
    }
    var id = tmp.substring(tmp.lastIndexOf('-')+1, tmp.length);
    if(id==''){
        alert('id为空');
        return false;
    }
    //通过id从后台获取数据并填充
    editDataRequireInput(id, url, form);
    var dialog = $( "#dialog-message-edit" ).removeClass('hide').dialog({
                    modal: true,
                    width:450,
                    buttons: [
                        {
                            text: "取消",
                            "class" : "btn btn-xs",
                            click: function() {
                                $( this ).dialog( "close" );
                            }
                        },
                        {
                            text: "确定",
                            "class" : "btn btn-primary btn-xs",
                            click: function() {
                                var dialog_obj = $(this);
                                var datas = {act: 'edit', id:id}
                                tmp = getDataRequireInput(datas, $( "#dialog-message-edit" ), true);
                                if(!tmp)
                                {
                                    return false;
                                }
                                res = sendAjax(url, datas, '', dialog_obj);
                                updateTableRowData(res['new_data']);
                            }
                        }
                    ]
                });
}
//行内添加操作
function tableAdd(obj){
    var url = $(obj).attr('data-url');
    var dialog = $( "#dialog-message-edit" ).removeClass('hide').dialog({
                    modal: true,
                    width:450,
                    buttons: [
                        {
                            text: "取消",
                            "class" : "btn btn-xs",
                            click: function() {
                                $( this ).dialog( "close" );
                            }
                        },
                        {
                            text: "确定",
                            "class" : "btn btn-primary btn-xs",
                            click: function() {
                                var dialog_obj = $(this);
                                var datas = {act: 'add'}
                                tmp = getDataRequireInput(datas, $( "#dialog-message-edit" ), true);
                                if(!tmp)
                                {
                                    return false;
                                }
                                sendAjax(url, datas, '', dialog_obj);
                            }
                        }
                    ]
                });
}
//行内删除操作
function tableDel(obj){
    var url = $(obj).attr('data-url');
    var tmp = $(obj).attr('data-action');
    var id = tmp.substring(tmp.lastIndexOf('-')+1, tmp.length);
    $( "#dialog-confirm" ).removeClass('hide').dialog({
        resizable: false,
            modal: true,
            buttons: [
                  {
                    html: "<i class='icon-trash bigger-110'></i>确定",
                    "class" : "btn btn-danger btn-xs",
                    click: function() {
                        var dialog_obj = $(this);
                        var successFunc = function(){
                            id = arguments[0];
                            if( $("#table-td-status-"+id) )
                            {
                                $("#table-td-status-"+id).html('<span class="label label-sm label-error arrowed arrowed-righ">禁止</span>');
                            }
                            else
                            {
                                $('#table-tr-'+id).remove();
                            }
                        }
                        var datas = {act: 'delete-one', id: id};
                        sendAjax(url, datas, successFunc(id), dialog_obj);
                    }
                },
                {
                    html: "<i class='icon-remove bigger-110'></i>取消",
                    "class" : "btn btn-xs",
                    click: function() {
                        $(this).dialog( "close" );
                    }
                }
            ]
    });
}
//绑定添加数据到btn中，并更新jqgrid控件
function operateInfoAndRefresh(obj, form_id, grid_id){
    var action = $(obj).attr('data-action');
    var url = $(obj).attr('data-url');
    if(action!='' || url!=''){
        var data = {};
        var filtersStr;
        data = filtersStr = getDataRequireInput(data, $('#'+form_id), false);
        if(action=='jqgrid-add'){
            data['act'] = 'add';
        } else if(action=='jqgrid-delete'){
             data['act'] = 'delete';
        } else if(action=='jqgrid-update'){
             data['act'] = 'update';
        } else if(action=='jqgrid-search'){
              data['act'] = 'list';
              var postData = $("#"+grid_id).jqGrid("getGridParam", "postData");
              $.extend(postData, {filters:  JSON.stringify(filtersStr)});
              $("#"+grid_id).jqGrid("setGridParam", {
                search: true
              }).trigger("reloadGrid", [{page:1}]);;
              return false;
        }
        if($("#"+form_id).valid()){
            res = sendAjax(url, data, '', '');
            if(res.code!='undefined' && res.code=='success'){
                $('#'+grid_id).trigger("reloadGrid", [{page:1}]);
            } else{
                $('#form-error').html(res.msg+'<button class="close" data-dismiss="alert"><i class="icon-remove"></i></button>');
                $('#form-error').removeClass('hide');
                return false;
            }
        } else{
            return false;
        }
    }
    return false;
}
jQuery(function($){
    $('table th input:checkbox').on('click' , function(){
        var that = this;
        $(this).closest('table').find('tr > td:first-child input:checkbox')
        .each(function(){
            this.checked = that.checked;
            $(this).closest('tr').toggleClass('selected');
        });
    });
    //单条信息删除
    $("a[data-action^='table-delete-id-']").on('click', function (e) {
        e.preventDefault();
        tableDel(this);
    });
    //多条信息删除
    $("a[data-action='table-delete']").on('click', function (e) {
        e.preventDefault();
        var url = $(this).attr('data-url');
        var chk = $("table[name='table-list']").find(':checkbox:eq(0)');
        var res = '';
        var res_arr = new Array();
        $("table[name='table-list']").find('tr > td:first-child input:checkbox')
        .each(function(){
           if($(this).is(':checked')==true)
           {
               res += $(this).attr('value')+',';
               res_arr.push($(this).attr('value'));
           }
        });
        res = res.substring(0, res.length-1);
        if( res!='' )
        {
            $( "#dialog-confirm" ).removeClass('hide').dialog({
                resizable: false,
                modal: true,
                buttons: [
                    {
                        html: "<i class='icon-trash bigger-110'></i>确定",
                        "class" : "btn btn-danger btn-xs",
                        click: function() {
                            var dialog_obj = $(this);
                            var datas = {act: 'delete', ids: res};
                            var successFunc = function(){
                                res_arr = arguments[0];
                                for (var i = 0; i<res_arr.length; i++)
                                {
                                    if( $("#table-td-status-"+res_arr[i]) )
                                    {
                                        $("#table-td-status-"+res_arr[i]).html('<span class="label label-sm label-error arrowed arrowed-righ">禁止</span>');
                                    }
                                    else
                                    {
                                        $('#table-tr-'+res_arr[i]).remove();
                                    }
                                }
                            }
                            sendAjax(url, datas, successFunc(res_arr), dialog_obj);
                        }
                    },
                    {
                        html: "<i class='icon-remove bigger-110'></i>取消",
                        "class" : "btn btn-xs",
                        click: function() {
                            $(this).dialog( "close" );
                        }
                    }
                ]
            });
        }
    });
    //添加新信息
    $("a[data-action='table-add']").on('click', function (e) {
        e.preventDefault();
        tableAdd(this);
    });
    //修改信息
    $("a[data-action^='table-edit-']").on('click', function (e) {
        e.preventDefault();
        tableEdit(this);
    });
    //分页
    $("a[data-action^='table-page-']").on('click', function (e) {
        var data_action = $(this).attr('data-action');
        var page_num = data_action.substring(data_action.lastIndexOf('-')+1, data_action.length);
        var url = $(this).attr('data-url');
        var tbl_tbody = $("table[name='table-list'] tbody");
        var columns = new Array();
        tbl_tbody.find("tr:eq(0) > td[id^=table-td-]").each(function() {
            if($(this).attr('id')!='table-td-operate'){
                //获取字段
                var td_id = $(this).attr('id');
                var arr_td_id = td_id.split('-');
                var td_id_name = arr_td_id[2];
                columns.push(td_id_name);
            }
        });
        var table_td_operate = '<td id="table-td-operate"><div class="visible-md visible-lg hidden-sm hidden-xs action-buttons">';
        tbl_tbody.find("tr:eq(0) > td[id=table-td-operate]").find('a').each(function() {
            var types = ($(this).attr('data-action')).split('-');
            if(types[1]=='edit'){
                table_td_operate += '<a href="javascript:;" onclick="tableEdit(this);" class="'+$(this).attr('class')+'" data-url="'+$(this).attr('data-url')+'" data-action="'+$(this).attr('data-action')+'">'
                                +$(this).html()
                                +'</a>';
            } else if(types[1]=='delete'){
                table_td_operate += '<a href="javascript:;" onclick="tableDel(this);" class="'+$(this).attr('class')+'" data-url="'+$(this).attr('data-url')+'" data-action="'+$(this).attr('data-action')+'">'
                                +$(this).html()
                                +'</a>';
            } else if(types[1]=='check'){

            }
        });
        table_td_operate += '</div></td>';
        tbl_tbody.html('');
        var datas = {act:'list', page:page_num}
        var res = sendAjax(url, datas, '', '');
        var tbody_html = '';
        $.each(res, function(key, item) {
            tbody_html += '<tr id="table-tr-'+item['id']+'">';
            for(var i=0;i<columns.length;i++){
                if(columns[i]=='id'){
                    tbody_html += '<td class="center"  id="table-td-id-'+item[columns[i]]+'" >'+
                                        '<label><input type="checkbox" class="ace" value="'+item[columns[i]]+'"/><span class="lbl"></span>'+
                                        '</label>'+
                                    '</td>';
                }
                else if(columns[i]=='status'){
                    tbody_html += '<td id="table-td-status-'+item['id']+'">';
                    if(item[columns[i]]==1){
                       tbody_html += '<span class="label label-sm label-info arrowed arrowed-righ">正常</span>';
                    } else{
                       tbody_html += '<span class="label label-sm label-error arrowed arrowed-righ">禁止</span>';
                    }
                    tbody_html += '</td>';
                }
                else if(columns[i]=='update_time'){
                    if(item[columns[i]]=='' || null==item[columns[i]]){
                        tbody_html += '<td id="table-td-'+columns[i]+'-'+item['id']+'" >无</td>';
                    } else{
                        tbody_html += '<td id="table-td-'+columns[i]+'-'+item['id']+'" >'+item[columns[i]]+'</td>';
                    }
                }
                else{
                    tbody_html += '<td id="table-td-'+columns[i]+'-'+item['id']+'" >'+item[columns[i]]+'</td>';
                }
            }
            tbody_html += table_td_operate;
            tbody_html += '</tr>';
        });
        tbl_tbody.html(tbody_html);
        delete tbody_html;
        delete res;
    });

    //控制分页按钮的样式
    $("ul[name='pagination'] > li").on('click', function (e) {
        var len = $("ul[name='pagination'] > li").length-2;
        if(len<0){
            len = 1;
        }
        var cls = $(this).attr('class');
        var func = function(obj, len){
            $(obj).siblings().each(function(i, item){
                var li_cls = $(item).attr('class');
                var tmp = $(this).find('a[data-action=table-page-'+len+']');
                if(tmp.length==1 && li_cls!='prev' && li_cls!='next'){
                    tmp.parent('li').attr('class', 'active');
                } else{
                    if(li_cls!='prev' && li_cls!='next'){
                        $(item).removeClass();
                    }
                }
            });
        };
        if(cls=='prev'){
            func(this, 1);
        } else if(cls=='next'){
            func(this, len);
        } else{
            var li_cls = $(this).attr('class');
            $(this).attr('class', 'active');
            $(this).siblings().not('[class=prev],[class=next]').removeClass();
        }
    });
});

function style_edit_form(form) {
    //enable datepicker on "sdate" field and switches for "stock" field
    form.find('input[name=sdate]').datepicker({format:'yyyy-mm-dd' , autoclose:true})
        .end().find('input[name=stock]')
              .addClass('ace ace-switch ace-switch-5').wrap('<label class="inline" />').after('<span class="lbl"></span>');

    //update buttons classes
    var buttons = form.next().find('.EditButton .fm-button');
    buttons.addClass('btn btn-sm').find('[class*="-icon"]').remove();//ui-icon, s-icon
    buttons.eq(0).addClass('btn-primary').prepend('<i class="icon-ok"></i>');
    buttons.eq(1).prepend('<i class="icon-remove"></i>')

    buttons = form.next().find('.navButton a');
    buttons.find('.ui-icon').remove();
    buttons.eq(0).append('<i class="icon-chevron-left"></i>');
    buttons.eq(1).append('<i class="icon-chevron-right"></i>');
}
function style_delete_form(form) {
    var buttons = form.next().find('.EditButton .fm-button');
    buttons.addClass('btn btn-sm').find('[class*="-icon"]').remove();//ui-icon, s-icon
    buttons.eq(0).addClass('btn-danger').prepend('<i class="icon-trash"></i>');
    buttons.eq(1).prepend('<i class="icon-remove"></i>')
}
function style_search_filters(form) {
    form.find('.delete-rule').val('X');
    form.find('.add-rule').addClass('btn btn-xs btn-primary');
    form.find('.add-group').addClass('btn btn-xs btn-success');
    form.find('.delete-group').addClass('btn btn-xs btn-danger');
}
function style_search_form(form) {
    var dialog = form.closest('.ui-jqdialog');
    var buttons = dialog.find('.EditTable')
    buttons.find('.EditButton a[id*="_reset"]').addClass('btn btn-sm btn-info').find('.ui-icon').attr('class', 'icon-retweet');
    buttons.find('.EditButton a[id*="_query"]').addClass('btn btn-sm btn-inverse').find('.ui-icon').attr('class', 'icon-comment-alt');
    buttons.find('.EditButton a[id*="_search"]').addClass('btn btn-sm btn-purple').find('.ui-icon').attr('class', 'icon-search');
}

function beforeDeleteCallback(e) {
    var form = $(e[0]);
    if(form.data('styled')) return false;
    form.closest('.ui-jqdialog').find('.ui-jqdialog-titlebar').wrapInner('<div class="widget-header" />')
    style_delete_form(form);
    form.data('styled', true);
}
function beforeEditCallback(e) {
    var form = $(e[0]);
    form.closest('.ui-jqdialog').find('.ui-jqdialog-titlebar').wrapInner('<div class="widget-header" />')
    style_edit_form(form);
}
//it causes some flicker when reloading or navigating grid
//it may be possible to have some custom formatter to do this as the grid is being created to prevent this
//or go back to default browser checkbox styles for the grid
function styleCheckbox(table) {
/**
    $(table).find('input:checkbox').addClass('ace')
    .wrap('<label />')
    .after('<span class="lbl align-top" />')
    $('.ui-jqgrid-labels th[id*="_cb"]:first-child')
    .find('input.cbox[type=checkbox]').addClass('ace')
    .wrap('<label />').after('<span class="lbl align-top" />');
*/
}

//unlike navButtons icons, action icons in rows seem to be hard-coded
//you can change them like this in here if you want
function updateActionIcons(table) {
    /**
    var replacement =
    {
        'ui-icon-pencil' : 'icon-pencil blue',
        'ui-icon-trash' : 'icon-trash red',
        'ui-icon-disk' : 'icon-ok green',
        'ui-icon-cancel' : 'icon-remove red'
    };
    $(table).find('.ui-pg-div span.ui-icon').each(function(){
        var icon = $(this);
        var $class = $.trim(icon.attr('class').replace('ui-icon', ''));
        if($class in replacement) icon.attr('class', 'ui-icon '+replacement[$class]);
    })
    */
}
//replace icons with FontAwesome icons like above
function updatePagerIcons(table) {
    var replacement =
    {
        'ui-icon-seek-first' : 'icon-double-angle-left bigger-140',
        'ui-icon-seek-prev' : 'icon-angle-left bigger-140',
        'ui-icon-seek-next' : 'icon-angle-right bigger-140',
        'ui-icon-seek-end' : 'icon-double-angle-right bigger-140'
    };
    $('.ui-pg-table:not(.navtable) > tbody > tr > .ui-pg-button > .ui-icon').each(function(){
        var icon = $(this);
        var $class = $.trim(icon.attr('class').replace('ui-icon', ''));
        if($class in replacement) icon.attr('class', 'ui-icon '+replacement[$class]);
    })
}
function enableTooltips(table) {
    $('.navtable .ui-pg-button').tooltip({container:'body'});
    $(table).find('.ui-pg-div').tooltip({container:'body'});
}
function checkidcard(num) {
    var len = num.length, re;
    if (len == 15)
        re = new RegExp(/^(\d{6})()?(\d{2})(\d{2})(\d{2})(\d{3})$/);
    else if (len == 18)
        re = new RegExp(/^(\d{6})()?(\d{4})(\d{2})(\d{2})(\d{3})(\d)$/);
    else {
        //alert("请输入15或18位身份证号,您输入的是 "+len+ "位");
        return false;
    }
    var a = num.match(re);
    if (a != null) {
        if (len == 15) {
            var D = new Date("19" + a[3] + "/" + a[4] + "/" + a[5]);
            var B = D.getYear() == a[3] && (D.getMonth() + 1) == a[4] && D.getDate() == a[5];
        } else {
            var D = new Date(a[3] + "/" + a[4] + "/" + a[5]);
            var B = D.getFullYear() == a[3] && (D.getMonth() + 1) == a[4] && D.getDate() == a[5];
        }
        if (!B) {
            //alert("输入的身份证号 "+ a[0] +" 里出生日期不对！");
            return false;
        }
    }
    return true;
}
