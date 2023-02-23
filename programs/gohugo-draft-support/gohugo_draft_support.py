"""
Copyright (c) 2023 SERVER (also known as Angolmois)
This software is released under the MIT License, see LICENSE.
"""
import argparse
import datetime
import io
import json
import os
import pathlib
import re
import subprocess
import sys
import textwrap
import traceback
import typing
from enum import IntEnum

import argcomplete
import ruamel.yaml
import ruamel.yaml.string
import toml
from ruamel.yaml.compat import StringIO

sys.path.append(os.path.join(os.path.dirname(__file__), '../'))
from libs_python.terminal_utils import TerminalColor, TerminalUtil

"""
Develop Operations
"""
def do_develop():
    pass

"""
Release Operations
"""
def do_release():
    pass

"""
Draft Operations
"""
def do_draft():
    pass

def do_draft_new(args) -> bool:
    section_path = pathlib.Path(f"{HUGO_PROJECT_ROOT}/content/posts/{args.target}")
    # パスが不正な場合はエラー
    path_validated = valid_section(section_path.absolute(), exists=False)
    if not path_validated:
        return print_error("既に記事が存在します。", exitcode=EXIT_ERR_DRAFT|FLAG_ERR_DRAFT_NEW)

    # 新記事作成コマンドを実行
    process = command(f"hugo new posts/{args.target}/index.md", cwd=HUGO_PROJECT_ROOT)
    if process.returncode != 0: return print_error(process.stderr, exitcode=EXIT_ERR_DRAFT|FLAG_ERR_DRAFT_NEW)
    print_success(f"generate new\t= {section_path.joinpath('index.md').absolute()}")

    return _draft_edit(args)

def do_draft_edit(args) -> bool:
    section_path = pathlib.Path(f"{HUGO_PROJECT_ROOT}/content/posts/{args.target}")
    # パスが不正な場合はエラー（存在しない場合はエラー）
    path_validated = valid_section(section_path.absolute(), exists=True)
    if not path_validated:
        return print_error("指定の記事は存在しません。", exitcode=EXIT_ERR_DRAFT|FLAG_ERR_DRAFT_NEW)

    return _draft_edit(args)

#
# ドラフト編集共通処理
#
def _draft_edit(args) -> bool:
    if not arg_is_available(args, "target"):
        return print_error("記事が指定されていません。", exitcode=EXIT_ERR_DRAFT|FLAG_ERR_DRAFT_EDIT)
    
    # check path
    draft_path = pathlib.Path(f"{HUGO_PROJECT_ROOT}/content/posts/{args.target}/index.md")
    if not draft_path.exists():
        return print_error("記事が存在しないか、不正なパスです。", exitcode=EXIT_ERR_DRAFT|FLAG_ERR_DRAFT_EDIT)

    markdown = draft_path.absolute()
    print_success(f"target\t= {markdown}")

    # TODO ISSUE フロントマターはOSコマンドを使わずに書き換える

    markdown_data = read_front_matter(markdown_path=markdown, language="yaml")
    front_matter:dict = markdown_data.get("result")

    # 日付
    if arg_is_available(args, "date"):
        front_matter["date"] = create_formatted_date_from_date(args.date)

    # タイトル
    if arg_is_available(args, "title"):
        front_matter["title"] = args.title
    
    # 概要
    if arg_is_available(args, "description"):
        front_matter["description"] = args.description
        front_matter["subtitle"] = args.description

    # タグ
    if arg_is_available(args, "tags"):
        front_matter["tags"] = list(map(lambda x: x, args.tags.split()))
    
    # カテゴリ
    if arg_is_available(args, "categories"):
        front_matter["categories"] = list(map(lambda x: x, args.categories.split()))
    
    # イメージ生成前に一度書き込み
    if not write_front_matter(markdown_path=markdown, language="yaml", print_detail=True, **markdown_data):
        return print_error("フロントマターの更新に失敗しました。", exitcode=EXIT_ERR_DRAFT|FLAG_ERR_DRAFT_EDIT)

    # TCardgen Image
    if arg_is_available(args, "images") and (args.images == True):
        out_image = markdown.parent.joinpath('index.png').absolute()

        use_image_title = arg_is_available(args, "ititle")
        saved_title = None
        
        # 画像生成用にタイトルを一時設定
        if use_image_title:
            fm = read_front_matter(markdown_path=markdown, language="yaml")
            saved_title = fm.get("result")["title"]
            fm.get("result")["title"] = args.ititle
            if not write_front_matter(markdown_path=markdown, language="yaml", print_detail=False, **fm):
                return print_error("画像生成(title->ititleの設定)に失敗しました。", exitcode=EXIT_ERR_DRAFT|FLAG_ERR_DRAFT_EDIT)
            print_success(f"set title\t= {args.ititle}")

        # 画像生成
        process = command(f"{TCARDGEN_BIN} -f {TCARDGEN_FONT_DIR} -c {TCARDGEN_CONF} -o {out_image} {markdown} >/dev/null", cwd=HUGO_PROJECT_ROOT)
        if process.returncode != 0: return print_error(process.stderr, exitcode=EXIT_ERR_DRAFT|FLAG_ERR_DRAFT_NEW)
        print_success(f"generate img\t= {out_image}")

        # 画像生成用のタイトル一時設定を戻す
        if use_image_title:
            fm = read_front_matter(markdown_path=markdown, language="yaml")
            fm.get("result")["title"] = saved_title
            if not write_front_matter(markdown_path=markdown, language="yaml", print_detail=False, **fm):
                return print_error("画像生成(ititle->titleの設定)に失敗しました。", exitcode=EXIT_ERR_DRAFT|FLAG_ERR_DRAFT_EDIT)
            print_success(f"set title\t= {saved_title}")
    
    return print_success()

def do_draft_stage(args):
    pass

def do_draft_unstage():
    pass

"""
Common Functions: Hugo Draft
"""
def valid_section(path: pathlib.Path, exists=True) -> bool:
    # 半角英数、ハイフン、アンダースコア以外はエラー
    check_name = re.match(f'^[a-zA-Z_\-0-9]+$', path.name)
    if (check_name is None) or (check_name.group() is None):
        return print_error(f"Invalid Path: {path.name}")
    # チェックしたい状態と実パスの状態が不一致ならエラー
    if exists != path.exists():
        return print_error(f"{path.absolute()} exists = {path.exists()}")
    return True

def create_default_date() -> str:
    t_delta = datetime.timedelta(hours=9)
    JST = datetime.timezone(t_delta, 'JST')
    now = datetime.datetime.now(JST)
    return now.strftime('%Y%m%d%H%M%S')

def create_formatted_date_from_date(datestr: str) -> str:
    try:
        d = datetime.datetime.strptime(datestr,"%Y%m%d%H%M%S")
        return d.strftime('%Y-%m-%dT%H:%M:%S+09:00')
    except:
        raise ValueError("日付の形式が不正です。(YYYYmmddHHMMSSで指定)")

"""
Common Functions: I/O
"""

#
# 設定読み込み
#
def load_config(config: pathlib.Path):
    global DEBUG
    global HUGO_PROJECT_ROOT
    global TCARDGEN_BIN
    global TCARDGEN_CONF
    global TCARDGEN_FONT_DIR
    global REMOTE
    global BRANCH_MAIN
    global BRANCH_DEVELOP
    global BRANCH_DRAFT
    with open(config) as file:
        y = yaml.load(file)
        settings = y["gohugo"]["settings"]
        HUGO_PROJECT_ROOT = settings["hugo_project_root"]
        DEBUG = bool(settings["debug"])
        TCARDGEN_BIN = settings["tcardgen_bin"]
        TCARDGEN_CONF = settings["tcardgen_conf"]
        TCARDGEN_FONT_DIR = settings["tcardgen_font_dir"]
        git = y["gohugo"]["git"]
        REMOTE = git["remote"]
        BRANCH_MAIN = git["branches"]["main"]
        BRANCH_DEVELOP = git["branches"]["develop"]
        BRANCH_DRAFT = git["branches"]["draft"]

def read_front_matter(markdown_path: pathlib.Path, language="yaml"):
    text = markdown_path.read_text()
    # pattern_fm_json = re.compile(r"{(.|\s)*?}\n")
    # pattern_fm_toml = re.compile(r"\n?\-\-\-(.|\s)*?\-\-\-\n")

    # TODO ISSUE follow json, toml

    if language == "yaml":
        pattern_fm_toml = re.compile(r"\n?\-\-\-\n(.|\s)*?\-\-\-\n")
        m = pattern_fm_toml.search(text)
        fm_start = m.start() + 4
        fm_end = m.end() - 5
        before_text = text[0:fm_start]
        front_matter = text[fm_start:fm_end]
        after_text = text[fm_end+1:len(text)]
        result = yaml.load(front_matter)
        return {'start': fm_start, 'end': fm_end, 'before_text': before_text, 'after_text': after_text, 'result': result}
    else:
        return print_error(f"language unknown [{language}]. support only toml,yaml or json.")

def write_front_matter(markdown_path: pathlib.Path, start, end, before_text, after_text, result, language="yaml", print_detail=True) -> bool:
    try:
        stream = StringIO()
        yaml.dump(data=result, stream=stream)
        fm = stream.getvalue()
        if print_detail:
            print_success(f"\n===\n[REWRITE FRONT MATTER]\n===\n{fm}")
        out_buffer = before_text + fm + after_text
        markdown_path.write_text(data=out_buffer, encoding="utf-8")
    except Exception as e:
        t = list(traceback.TracebackException.from_exception(e).format())
        return print_error(f"front matter update error.\ncaused by: {t}")
    return True

#
# SUCCESSを表示してreturn True
#
def print_success(message=None) -> bool:
    if message is None:
        text = f'''
            {TerminalColor.code(32)}  SUCCESS{TerminalColor.RESET}
        '''
        print(textwrap.dedent(text)[0:])
    else: 
        text = f'''
            {TerminalColor.code(32)}  {message}{TerminalColor.RESET}
        '''
        print(textwrap.dedent(text)[1:-1])
    return True

#
# ERRORを表示してreturn False
#
def print_error(err, exitcode: int =None) -> bool:
    text = f'''
        {TerminalColor.code(31)} ERROR: {err}{TerminalColor.RESET}
    '''
    print(textwrap.dedent(text)[1:-1])
    if exitcode != None: return sys.exit(exitcode)
    return False

"""
Common Functions: OS Command
"""
#
# OSのシステムコマンドを実行（DEBUG=Trueで実行コマンドを出力する）
#
def command(cmd, cwd=".") -> subprocess.CompletedProcess:
    if DEBUG: print(f"{cwd} # -> {cmd}")
    return subprocess.run(cmd, shell=True, encoding="utf-8", cwd=cwd)

# #
# # フロントマターの任意の値を直接書き換える
# #
# def command_sed_frontmatter(markdown_path: str, key: str, value: str, backup_suffix: str="") -> subprocess.CompletedProcess:
#     return command(cmd=f'sed -i{backup_suffix} -e \'0,/^{key}:/ s/^\({key}\):.*$/\\1: {value}/\' {markdown_path}', cwd=HUGO_PROJECT_ROOT)

# #
# # フロントマター書き換え時にバックアップしたファイルを元に戻す時用の関数
# #
# def restore_markdown(markdown_path: str, backup_suffix: str) -> subprocess.CompletedProcess:
#     file_path = pathlib.Path(markdown_path)
#     orig_path = pathlib.Path(f'{markdown_path}{backup_suffix}')
#     if (not file_path.exists()) or (not orig_path.exists()):
#         return print_error("File Not Found")
#     return command(cmd=f'mv {markdown_path}{backup_suffix} {markdown_path}', cwd=HUGO_PROJECT_ROOT)

"""
Common Functions: Git
"""
def git_operation():
    pass

def _git_operation_commit():
    pass

def _git_operation_merge():
    pass

def _git_operation_delete():
    pass

def _git_operation_checkout_files():
    pass

"""
Common Functions: argparse
"""
#
# argparseの引数が存在、且つ、Noneではない
#
def arg_is_available(args: argparse.Namespace, key: str):
    return hasattr(args, key) and (getattr(args, key) is not None)

# =====================================================================================================================
# 以下、MAIN前の処理
# =====================================================================================================================

# EXIT_CODE
EXIT_SUCCESS = 0
EXIT_ERR_DRAFT = 10
FLAG_ERR_DRAFT_NEW = 1
FLAG_ERR_DRAFT_STAGE = 2
FLAG_ERR_DRAFT_UNSTAGE = 16
FLAG_ERR_DRAFT_EDIT = 32
# FLAG_ERR_GIT = 32
# FLAG_ERR_SHELL = 64

DEBUG = None
HUGO_PROJECT_ROOT = None
TCARDGEN_BIN = None
TCARDGEN_CONF = None
TCARDGEN_FONT_DIR = None
REMOTE = None
BRANCH_MAIN = None
BRANCH_DEVELOP = None
BRANCH_DRAFT = None
BRANCH_HOTFIX = None

yaml: ruamel.yaml.YAML = ruamel.yaml.YAML()
yaml.allow_unicode = True
yaml.default_flow_style = True

GOHUGO_DRAFT_SUPPORT_CONFIG = f"{pathlib.Path(__file__).parent}/gohugo_draft_support-conf.yaml"
load_config(GOHUGO_DRAFT_SUPPORT_CONFIG)
TerminalUtil.set_ansimode_if_windows()
TerminalUtil.set_text_io_wrapper()

main_parser = argparse.ArgumentParser(prog="gohugo-draft-support", description="Hugo Draft Edit Utility.")
subparsers = main_parser.add_subparsers()

# =========================================================
# Draft 
# =========================================================
p_draft = subparsers.add_parser("draft", help="", description="")
draft_sp = p_draft.add_subparsers()
# ---------------------------------------------------------
# draft new
# ---------------------------------------------------------
sp_draft_new = draft_sp.add_parser("new", help="記事を新規作成します", description="")
sp_draft_new.add_argument("--target", required=True, help="content/posts配下に作成するセクション(URL部分)を指定します。（必須）")
sp_draft_new.add_argument("--title", required=False, help="記事タイトルを指定します。")
sp_draft_new.add_argument("--description", metavar="DESC", required=False, help="概要テキストを指定します。")
sp_draft_new.add_argument("--categories", metavar="CATGS", required=False, help="カテゴリを半角スペース区切りで指定します。")
sp_draft_new.add_argument("--tags", required=False, help="タグを半角スペース区切りで指定します。")
sp_draft_new.add_argument("--date", default=create_default_date(), required=False, help="投稿日時を「YYYYmmddHHMMSS」形式指定します。")
sp_draft_new_tcg = sp_draft_new.add_argument_group("Use TCardgen Option", description="これらのオプションを使うにはTCardgenがインストールされている必要があります。")
sp_draft_new_tcg.add_argument("--images", action="store_true", required=False, help="TCardgenでデフォルトアイキャッチを生成します。")
sp_draft_new_tcg.add_argument("--ititle", metavar="ITITLE", required=False, help="デフォルトアイキャッチに表示するタイトルテキストを指定します。")
sp_draft_new.set_defaults(handler=do_draft_new)

# ---------------------------------------------------------
# draft edit
# ---------------------------------------------------------
sp_draft_edit = draft_sp.add_parser("edit", help="stageされていない、任意のドラフト記事を編集します。", description="")
sp_draft_edit.add_argument("--target", required=True, help="content/posts配下のセクション(URL部分)を指定します。（必須）")
sp_draft_edit.add_argument("--title", required=False, help="記事タイトルを指定します。")
sp_draft_edit.add_argument("--description", metavar="DESC", required=False, help="概要テキストを指定します。")
sp_draft_edit.add_argument("--categories", metavar="CATGS", required=False, help="カテゴリを半角スペース区切りで指定します。")
sp_draft_edit.add_argument("--tags", required=False, help="タグを半角スペース区切りで指定します。")
sp_draft_edit.add_argument("--date", required=False, help="投稿日時を「YYYYmmddHHMMSS」形式指定します。")
sp_draft_edit_tcg = sp_draft_edit.add_argument_group("Use TCardgen Option", description="これらのオプションを使うにはTCardgenがインストールされている必要があります。")
sp_draft_edit_tcg.add_argument("--images", action="store_true", required=False, help="デフォルトアイキャッチを上書き生成します。")
sp_draft_edit_tcg.add_argument("--ititle", metavar="ITITLE", required=False, help="デフォルトアイキャッチに表示するタイトルテキストを指定します。")
sp_draft_edit.set_defaults(handler=do_draft_edit)

# ---------------------------------------------------------
# TODO draft stage
# ---------------------------------------------------------
sp_draft_stage = draft_sp.add_parser("stage", help=f"任意のドラフト記事を『{BRANCH_DRAFT}』ブランチから『{BRANCH_DEVELOP}』ブランチへマージします。", description="")
sp_draft_stage.add_argument("--target", required=True, help="content/posts配下のセクション(URL部分)を指定します。（必須）")
sp_draft_stage.set_defaults(handler=do_draft_stage)

# ---------------------------------------------------------
# TODO draft unstage
# ---------------------------------------------------------
sp_draft_unstage = draft_sp.add_parser("unstage", help=f"任意のドラフト記事を『{BRANCH_DEVELOP}』ブランチから削除します。", description="")
sp_draft_unstage.set_defaults(handler=do_draft_unstage)

p_draft.set_defaults(handler=do_draft)

# =========================================================
# TODO Develop
# =========================================================
p_develop = subparsers.add_parser("develop", help="便利コマンド群", description="")
# =========================================================
# TODO Release
# =========================================================
p_release = subparsers.add_parser("release", help=f"『{BRANCH_MAIN}』ブランチにリリースする際の専用コマンド", description="")

# =========================================================
# DO MAIN
# =========================================================
def main(args):
    if arg_is_available(args, "handler"):
        args.handler(args)
    else:
        print_error("引数エラー", exitcode=-1)
    pass

# argcomplete.autocomplete(main_parser)
parse_args = main_parser.parse_args()
if __name__ == '__main__':
    main(parse_args)
