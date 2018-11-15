# -*- coding: utf-8 -*-
from tornado import locale
#国际化
locale.load_translations("./protected/translations")
locale.set_default_locale("zh_CN")
_locale = locale.get()
class AdminErrorMessage(object):
    error_message = {
        '001': _locale.translate('admin_userinfo_incomplete').encode("utf-8"),#填写信息不完整
        '002': _locale.translate('admin_user_not_exist').encode("utf-8"),#'该用户不存在'
        '003': _locale.translate('admin_password_no_correct').encode("utf-8"),#'密码错误'
        '004': _locale.translate('admin_session_had_expired').encode("utf-8"),#'您的会话已经过期'
        '005': _locale.translate('admin_delete_error').encode("utf-8"),#'删除失败'
        '006': _locale.translate('admin_add_error').encode("utf-8"),#'添加失败'
        '007': _locale.translate('admin_update_error').encode("utf-8"),#'修改失败'
        '008': _locale.translate('admin_same_error').encode("utf-8"),#'存在相同记录'
    }

class ErrorMessage(object):
    error_message = {
        '001': _locale.translate('login_fail').encode("utf-8"), #登录失败
        '002': _locale.translate('no_login').encode("utf-8"), #请登录
        '003': _locale.translate('email_not_exist').encode("utf-8"), #该邮箱不存在
        '004': _locale.translate('password_no_correct').encode("utf-8"), #密码错误
        '005': _locale.translate('email_nocorrect').encode("utf-8"), #密码错误
        '006': _locale.translate('password_less_six').encode("utf-8"), #密码长度小于6位
        '007': _locale.translate('password_not_same').encode("utf-8"), #确认密码不匹配
        '008': _locale.translate('clause_no_checked').encode("utf-8"), #您没有同意注册条款
        '009': _locale.translate('area_no_selected').encode("utf-8"), #您没有同意注册条款
        '010': _locale.translate('error_network').encode("utf-8"), #网络异常
        '011': _locale.translate('email_has_existed').encode("utf-8"), #邮箱已经存在
        '012': _locale.translate('username_has_existed').encode("utf-8"), #用户名已经存在
        '013': _locale.translate('gender_no_checked').encode("utf-8"), #请选择性别
        '014': _locale.translate('reg_update_error').encode("utf-8"), #注册信息修改失败
        '015': _locale.translate('send_email_error').encode("utf-8"), #发送邮件失败
        '016': _locale.translate('forget_email_token').encode("utf-8"), #请到邮箱确认注册信息
        '017': _locale.translate('forget_send_email').encode("utf-8"), #重新发送验证地址到邮箱
        '018': _locale.translate('yet_send_email').encode("utf-8"), #已经发送过验证邮件
        '019': _locale.translate('reg_no_email_or_expire').encode("utf-8"), #请确认已经填写过邮箱或邮件已经过期
        '020': _locale.translate('check_file_exist_email').encode("utf-8"), #请检查文件是否存在邮件列表
        '021': _locale.translate('save_email_file_error').encode("utf-8"), #保存邮件列表失败
        '022': _locale.translate('reg_error').encode("utf-8"), #请按照流程注册信息
        '023': _locale.translate('save_character_test_error').encode("utf-8"), #保存您的性格特点失败，请确认您填写完整
        '024': _locale.translate('failure_uid').encode("utf-8"), #注册用户已经失效
        '025': _locale.translate('error_email_token').encode("utf-8"), #验证失败，请确定发送的链接是正确的
        '026': _locale.translate('failure_verify_url_token').encode("utf-8"), #发送到您注册邮箱的确认地址已经失效
        '027': _locale.translate('has_verify_url_token').encode("utf-8"), #您已经验证过注册确认地址
        '028': _locale.translate('feedback_title_null').encode("utf-8"), #反馈标题为空
        '029': _locale.translate('feedback_content_null').encode("utf-8"), #反馈内容为空
        '030': _locale.translate('feedback_email_null').encode("utf-8"), #反馈邮箱为空
        '031': _locale.translate('failure_save_feedback').encode("utf-8"), #保存反馈信息失败
        '032': _locale.translate('email_format_error').encode("utf-8"), #邮箱格式错误
        '033': _locale.translate('captcha_empty').encode("utf-8"), #验证码为空
        '034': _locale.translate('captcha_error').encode("utf-8"), #验证码验证失败
        '035': _locale.translate('comment_null_error').encode("utf-8"), #评论不能为空
        '036': _locale.translate('feedback_id_null_error').encode("utf-8"), #您评论的反馈不存在
        '037': _locale.translate('uid_null_error').encode("utf-8"), #您未登录，无法发表
        '038': _locale.translate('feeback_comment_save_error').encode("utf-8"), #保存反馈评论失败
        '039': _locale.translate('frequent_operation_error').encode("utf-8"), #您操作太频繁
        '040': _locale.translate('vote_error').encode("utf-8"), #投票失败
        '041': _locale.translate('no_login').encode("utf-8"), #请登录
        '042': _locale.translate('sys_param_error').encode("utf-8"), #系统参数错误
        '043': _locale.translate('so_fast_notice').encode("utf-8"), #评论过快，请稍后重试
        '044': _locale.translate('comment_not_exist').encode("utf-8"), #您投诉的评论不存在
        '045': _locale.translate('complaint_error').encode("utf-8"), #投诉失败
        '046': _locale.translate('complaint_reason_null_error').encode("utf-8"), #投诉内容不能为空
        '047': _locale.translate('has_vote_error').encode("utf-8"), #已经投票
        '048': _locale.translate('system_eror').encode("utf-8"), #系统错误
        '049': _locale.translate('user_not_exist').encode("utf-8"), #用户不存在
        '050': _locale.translate('error_filesize').encode("utf-8"), #文件大小超出限制
        '051': _locale.translate('error_type_not_allowed').encode("utf-8"), #文件类型不允许
        '052': _locale.translate('newsfeed_content_null_error').encode("utf-8"), #状态内容不能为空
        '053': _locale.translate('badword_error').encode("utf-8"), #很抱歉，您的内容里有敏感字，它们会被*替换
        '054': _locale.translate('activity_not_exist').encode("utf-8"), #您还没有参加活动
        '055': _locale.translate('title_is_null').encode("utf-8"), #标题不能为空
        '056': _locale.translate('content_is_null').encode("utf-8"), #内容不能为空
        '057': _locale.translate('has_badword').encode("utf-8"), #很抱歉，您的内容里有敏感字
        '058': _locale.translate('url_error').encode("utf-8"), #路径错误
    }


class SuccessMessage(object):
    success_message = {
        '001': _locale.translate('login_success').encode("utf-8"), #登录成功
        '002': _locale.translate('clear_account_success').encode("utf-8"), #登录成功
        '003': _locale.translate('send_email_success').encode("utf-8"), #发送邮件成功
        '004': _locale.translate('save_email_success').encode("utf-8"), #保存成功
        '005': _locale.translate('success_verify_url').encode("utf-8"), #验证成功，谢谢注册
        '006': _locale.translate('save_comment_success').encode("utf-8"), #保存评论成功
        '007': _locale.translate('approval_votes_success').encode("utf-8"), #非常感谢
        '008': _locale.translate('oppose_votes_success').encode("utf-8"), #非常遗憾
        '009': _locale.translate('complaint_success').encode("utf-8"), #投诉成功
    }