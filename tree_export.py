#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import argparse

def write_folder_structure(root_path: str, output_file: str):
    """
    root_path 以下のフォルダ構成をツリー形式で出力ファイルに書き込む。
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        for dirpath, dirnames, filenames in os.walk(root_path):
            # root_path からの相対パスで深さを計算
            rel_path = os.path.relpath(dirpath, root_path)
            depth = 0 if rel_path == '.' else rel_path.count(os.sep) + 1
            indent = '    ' * (depth - 1) if depth > 0 else ''
            # ディレクトリ名を書き込み
            dirname = os.path.basename(dirpath) if rel_path != '.' else os.path.basename(os.path.abspath(root_path))
            f.write(f"{indent}{dirname}/\n")
            # ファイル一覧を書き込み
            for filename in sorted(filenames):
                f.write(f"{indent}    {filename}\n")

def main():
    parser = argparse.ArgumentParser(description="フォルダ構成をテキストファイルに書き出す")
    parser.add_argument("root", help="構成を取得したいルートフォルダのパス")
    parser.add_argument("-o", "--output", default="folder_structure.txt",
                        help="出力先テキストファイル名（デフォルト: folder_structure.txt）")
    args = parser.parse_args()

    write_folder_structure(args.root, args.output)
    print(f"フォルダ構成を '{args.output}' に書き出しました。")

if __name__ == "__main__":
    main()
