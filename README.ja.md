# Google Calendar API Direct Skill

[English](README.md)

Google Calendar の組み込みコネクタだけでは足りないときに、Google Calendar API を直接叩くための Codex スキルと、標準ライブラリだけで動く小さな Python CLI です。

主な用途:

- セカンダリカレンダーの作成
- カレンダー表示色の変更
- 場所、詳細、URL、通知、イベント色 ID 付きのサンプル予定作成
- 作成したカレンダーや予定の読み戻し確認

## なぜ作ったか

通常の予定確認や作成は Google Calendar コネクタで十分です。一方で、カレンダー単位の作成や色変更、API の実書き込み検証、再利用できるローカル自動化には直接 API が便利です。

## 構成

```text
.
├── SKILL.md
├── agents/openai.yaml
├── references/calendar-api.md
└── scripts/gcal_api.py
```

## 必要なもの

- Python 3.10 以降
- Google Calendar API を有効化した Google Cloud プロジェクト
- 種類が **デスクトップ アプリ** の OAuth クライアント

CLI は Python 標準ライブラリだけで動きます。追加パッケージのインストールは不要です。

## 認証情報の扱い

OAuth クライアント JSON やトークンはコミットしないでください。

CLI は標準でリポジトリ外に保存します:

```text
~/.codex/google-calendar-api-direct/client_secret.json
~/.codex/google-calendar-api-direct/token.json
```

テストや別プロファイルでは環境変数で変更できます:

```bash
export GCAL_CLIENT_SECRET=/path/to/client_secret.json
export GCAL_TOKEN_FILE=/path/to/token.json
```

## セットアップ

1. Google Cloud プロジェクトを作成または選択します。
2. **Google Calendar API** を有効化します。
3. Google Auth Platform / OAuth 同意画面を設定します。
4. 種類が **デスクトップ アプリ** の OAuth クライアントを作成します。
5. OAuth クライアント JSON をダウンロードします。
6. ローカルに保存します:

```bash
mkdir -p ~/.codex/google-calendar-api-direct
cp ~/Downloads/client_secret_*.json ~/.codex/google-calendar-api-direct/client_secret.json
chmod 600 ~/.codex/google-calendar-api-direct/client_secret.json
```

7. OAuth を実行します:

```bash
python3 scripts/gcal_api.py auth --scopes "https://www.googleapis.com/auth/calendar.app.created"
```

既存カレンダーを含む広い管理が必要なときだけ、より広い `https://www.googleapis.com/auth/calendar` スコープを使います。

## よく使うコマンド

カレンダー一覧:

```bash
python3 scripts/gcal_api.py calendars list
```

セカンダリカレンダー作成:

```bash
python3 scripts/gcal_api.py calendars create \
  --summary "Codex API Direct Demo" \
  --description "Created by the google-calendar-api-direct skill" \
  --time-zone Asia/Tokyo
```

カレンダー表示色の変更:

```bash
python3 scripts/gcal_api.py calendars color \
  --calendar-id "CALENDAR_ID" \
  --background "#16a765" \
  --foreground "#ffffff"
```

サンプル予定の作成:

```bash
python3 scripts/gcal_api.py events create \
  --calendar-id "CALENDAR_ID" \
  --summary "Codex API direct sample event" \
  --start "2026-05-19T10:00:00+09:00" \
  --end "2026-05-19T10:30:00+09:00" \
  --description "Created through the direct Google Calendar API" \
  --location "Online" \
  --url "https://example.com/codex-calendar-api-direct" \
  --color-id 5 \
  --reminder-minutes 10
```

作成予定の読み戻し:

```bash
python3 scripts/gcal_api.py events search \
  --calendar-id "CALENDAR_ID" \
  --time-min "2026-05-19T00:00:00+09:00" \
  --time-max "2026-05-20T00:00:00+09:00" \
  --query "Codex"
```

## 公開リポジトリ向けの注意

- OAuth 秘密情報はこのリポジトリに保存しません。
- `.gitignore` で認証情報、トークン、キャッシュ、ビルド成果物を除外しています。
- 破壊的なカレンダー削除操作は意図的に実装していません。
- 書き込み操作のあとには必ず読み戻し確認をしてから成功報告します。

## ライセンス

MIT
