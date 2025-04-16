# クリニック予約システム

Fast APIとStreamlitを使用したクリニック予約システムです。Poetryを使用して依存関係を管理しています。

## システム概要

このシステムは以下の機能を提供します：

- クリニックの予約枠管理（平日17時〜19時、30分ごと、各枠2名までなど）
- 患者のオンライン予約
- QRコードによる予約確認
- 管理者向け予約管理機能

## 必要条件

- Python 3.8 以上
- Poetry

## セットアップ手順

### 1. Poetryのインストール

Poetryがインストールされていない場合は、以下のコマンドでインストールします：

```bash
# Windows (PowerShell)
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -

# macOS / Linux
curl -sSL https://install.python-poetry.org | python3 -
```

### 2. プロジェクトのセットアップ

```bash
# リポジトリをクローン
git clone https://github.com/yourusername/clinic-reservation.git
cd clinic-reservation

# 依存関係のインストール
poetry install
```

### 3. プロジェクトの実行

#### バックエンドの起動

```bash
# Poetry環境内でFast APIを起動
poetry run uvicorn api.main:app --reload
```

#### フロントエンドの起動

別々のターミナルで以下のコマンドを実行します：

**管理者用アプリ**
```bash
poetry run streamlit run streamlit/admin_app.py
```

**患者用アプリ**
```bash
poetry run streamlit run streamlit/patient_app.py
```

**クリニック用アプリ（QRコード読取用）**
```bash
poetry run streamlit run streamlit/clinic_app.py
```

## プロジェクト構造

```
clinic_reservation/
│
├── api/                      # Fast API バックエンド
│   ├── __init__.py
│   ├── main.py               # APIエントリーポイント
│   ├── models.py             # データモデル
│   ├── database.py           # DB接続設定
│   ├── schemas.py            # Pydanticスキーマ
│   └── routers/              # APIルーター
│       ├── __init__.py
│       ├── auth.py           # 認証関連
│       ├── slots.py          # 予約枠関連
│       └── reservations.py   # 予約関連
│
├── streamlit/                # Streamlitフロントエンド
│   ├── admin_app.py          # 管理者用アプリ
│   ├── patient_app.py        # 患者用アプリ
│   └── clinic_app.py         # クリニック用アプリ
│
├── pyproject.toml            # Poetry設定ファイル
└── README.md                 # プロジェクト説明
```

## 開発環境の拡張

### 新しい依存関係の追加

```bash
# パッケージ追加
poetry add パッケージ名

# 開発用パッケージ追加
poetry add --group dev パッケージ名
```

### 仮想環境でのシェル起動

```bash
poetry shell
```

## セキュリティに関する注意

- 実際の運用では、セキュリティ設定を強化してください
- 本番環境ではSQLiteではなく、PostgreSQLなどのデータベースを使用することをお勧めします
- シークレットキーは環境変数として設定してください