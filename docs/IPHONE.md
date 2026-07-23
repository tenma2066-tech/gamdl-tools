# iPhone単体で使う(PC不要)

Apple Music を **iPhone だけ** でダウンロードする手順です。パソコンは一切いりません。

## しくみ

gamdl はもともとPC用ですが、バージョン **3.5.1** には次の特長があり、iPhone単体で動かせます。

- **Widevineデバイスを内蔵**しているので、Androidから取り出す `.wvd` ファイルが不要
- **曲の復号を純Python**で行うため、`mp4decrypt` などの外部ツールが不要
- ダウンロードは `yt-dlp`(純Python)で行う

必要なのは **Python + ffmpeg + gamdl + cookies.txt** だけです。これを **iSH** という無料アプリ(iPhone上で動くLinux環境)の中で動かします。

> **AAC 256kbps のみ**です。ALAC(ロスレス)/FLAC は「Wrapper」という復号サーバーが必要で、これはiPhoneでは動かせません。iPhone単体ではAACまでとなります。

---

## 手順

### 1. iSH をインストール

App Store で **「iSH Shell」**(無料)を入れて起動します。黒いターミナル画面が出ます。

### 2. cookies.txt を用意する(iPhoneだけで完結)

gamdl は Apple Music にログイン済みのCookieが必要です。iPhoneのSafariは拡張機能でCookieを書き出せないので、**拡張機能に対応した無料ブラウザ「Orion Browser」** を使います。

1. App Store で **「Orion Browser」** をインストール
2. Orion で拡張機能ストアから **「Get cookies.txt LOCALLY」**(Chrome拡張)を追加
3. Orion で https://music.apple.com を開き、Apple Musicに**ログイン**
4. ツールバーの拡張機能アイコン →「Export」で `cookies.txt` を書き出し、**「ファイル」アプリ**に保存

> Orionを使わない場合は、他のデバイス等で用意した `cookies.txt` を「ファイル」アプリに入れてもOKです。

### 3. cookies.txt を iSH に取り込む

iSH のファイルは iOS の「ファイル」アプリから見えます。

1. 「ファイル」アプリを開く →「ブラウズ」→ 場所に **「iSH」** が出ます
2. 手順2で保存した `cookies.txt` を **iSH の中の一番上のフォルダ**(ホーム `~`)にコピー

うまく見えない場合は、iSH内で次を実行するとホームの実体パスが分かります。
```sh
pwd        # 例: /root
```

### 4. gamdl をインストール(初回のみ)

iSH のターミナルで、次を1行ずつ実行します。

```sh
wget -O setup.sh https://raw.githubusercontent.com/tenma2066-tech/gamdl-tools/master/ios/setup.sh
wget -O amget.sh https://raw.githubusercontent.com/tenma2066-tech/gamdl-tools/master/ios/amget.sh
sh setup.sh
```

> iSHはx86エミュレーションで動くため**遅い**です。初回インストールは **10〜30分** かかることがあります。終わるまで **iSHを前面に表示したまま・画面をオンのまま** 待ってください(バックグラウンドに回すと止まります)。

画面下部の設定で「Disable screen dimming(画面を暗くしない)」をオンにしておくと安心です。

### 5. ダウンロードする

```sh
sh amget.sh
```

`[URL]` と出たら Apple Music の共有URL(アルバム/プレイリスト/曲)を貼り付けて Enter。
複数まとめて落としたいときは1つずつ貼って繰り返します。空Enter または `q` で終了。

URLを直接渡すこともできます:
```sh
sh amget.sh "https://music.apple.com/jp/album/xxxxx"
```

### 6. ダウンロードした曲の場所

保存先は iSH の `~/music` フォルダです。**「ファイル」アプリ →「iSH」→ music** から見え、そこから他アプリへ共有・コピーできます。

---

## うまくいかないとき

| 症状 | 対処 |
|---|---|
| `cookies.txt not found` | `cookies.txt` を iSH のホーム(`~`)に置く。`COOKIES=/path/to/cookies.txt sh amget.sh` で場所を指定してもよい |
| `403` / 認証エラー | Cookieの有効期限切れ。手順2をやり直して `cookies.txt` を入れ替える(数日で切れます) |
| インストールが途中で止まる | iSHをバックグラウンドに回すと停止します。前面・画面オンのまま再実行 |
| ディスク不足 | iSHは容量制限あり。落とした曲を「ファイル」アプリ経由で外に出してから `~/music` を空にする |
| 反応が非常に遅い | iSHのx86エミュレーションの仕様です。曲単位は数分で終わることが多いので待つ |

---

## 注意

- 有効な Apple Music サブスクリプションでの**個人利用**を前提とした自己責任の利用です。
- iPhone単体ではロスレス(ALAC/FLAC)は非対応です。ロスレスが必要な場合はPC + Wrapper が必要です(リポジトリ本体のREADME参照)。
