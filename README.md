# card-faces

Card-face artwork for [CardBal / TransitICReader](https://github.com/iebb/TransitICReader).
The app downloads `manifest.json` and the PNGs listed in it, so new faces ship
without an app update.

Faces are served from **https://faces.cardb.al/**, a Cloudflare Pages site
that rebuilds from `master` on every push. jsDelivr
(`https://cdn.jsdelivr.net/gh/iebb/card-faces@master/`, reachable from mainland
China) and raw GitHub are fallback mirrors with the same paths.

## Layout

```
catalog.json                        hand-edited metadata: names, matching keys
sources/<region>/<card>/<design>.*  full-resolution masters (WebP or PNG)
faces/<region>/<card>/<design>.png  optimized faces served to the app
manifest.json                       generated from catalog.json + faces/
public/_headers                     cache and CORS headers for Cloudflare Pages
tools/build.py                      optimizer and manifest generator
tools/validate.py                   budget and manifest checks (needs Pillow)
tools/publish.py                    stdlib-only Pages build: checks, then fills dist/
```

Every card folder has a `default.png`. Other designs sit next to it
(`faces/kr/tmoney/logo.png`, `faces/fr/la-carte/blue.png`) and the app offers
them in the face picker. Chinese cards are filed under their T-Union city code,
so `faces/cn/2900/default.png` is Shanghai.

### China: top 20 cities

The transit cards of mainland China's 20 largest cities by 2024 GDP. Each face
is a flat vector-style recreation of the city's real card front. Card numbers,
QR codes, serials and small print are removed.

| Folder | City | Card | Card prefix |
| --- | --- | --- | --- |
| `cn/2900` | 上海 Shanghai | 上海公共交通卡 (City Union 2000) | 31047700 |
| `cn/1000` | 北京 Beijing | 北京一卡通 | 31051700 |
| `cn/5840` | 深圳 Shenzhen | 深圳通 | 31048704 |
| `cn/6900` | 重庆 Chongqing | 宜居畅通卡 | 31049200, 31049201 |
| `cn/5810` | 广州 Guangzhou | 羊城通 | 31048703 |
| `cn/3050` | 苏州 Suzhou | 苏州市民卡 | 31048303 |
| `cn/6510` | 成都 Chengdu | 天府通 | 31047800 |
| `cn/3310` | 杭州 Hangzhou | 杭州通 | 31048801 |
| `cn/5210` | 武汉 Wuhan | 武汉通 | 31051400 |
| `cn/3010` | 南京 Nanjing | 南京市民卡 | 31048300 |
| `cn/3320` | 宁波 Ningbo | 宁波交通卡 | 31048802 |
| `cn/1121` | 天津 Tianjin | 天津城市卡 | 31049102 |
| `cn/4520` | 青岛 Qingdao | 琴岛通 | 31049304 |
| `cn/3020` | 无锡 Wuxi | 太湖交通卡 | 31048312 |
| `cn/5510` | 长沙 Changsha | 潇湘卡 | 31048200 |
| `cn/4910` | 郑州 Zhengzhou | 绿城通 | 31050702 |
| `cn/3910` | 福州 Fuzhou | 榕城通 | 31050600 |
| `cn/4510` | 济南 Jinan | 泉城通 | 31049308 |
| `cn/3610` | 合肥 Hefei | 合肥通 | 31049902 |
| `cn/5880` | 佛山 Foshan | 广佛通 | 31048707 |

### App default faces

The faces the app bundles, so they can be updated or extended without a
release. `bundledAsset` in the manifest names the app asset a design mirrors,
which lets the app skip a download it already has.

| Folder | Designs | Matched by |
| --- | --- | --- |
| `jp/suica`, `jp/pasmo`, `jp/icoca`, `jp/hayakaken`, `jp/sugoca`, `jp/manaca`, `jp/kitaca`, `jp/nimoca`, `jp/toica` | default | family name, serial prefix |
| `jp/okica`, `jp/edy`, `jp/waon`, `jp/nanaco` | default | family name |
| `kr/tmoney` | default, logo | family name |
| `kr/ezl`, `kr/climate-card` | default | family name |
| `fr/la-carte` | default, blue | family name |
| `mn/umoney` | default | family name |

## Budgets

Every published face must:

- be a PNG with a 30:19 aspect ratio (1200×760 when it fits);
- use at most **24 colours**;
- be smaller than **40,000 bytes**.

`tools/validate.py` enforces this in CI, together with the sha256, size and
colour count recorded in `manifest.json`.

## Adding or updating a design

1. Put the master in `sources/<region>/<card>/<design>.webp` (or `.png`). Use
   `default` for the card's main face. Chinese cards use the T-Union city code
   as `<card>`.
2. Add or edit the card in `catalog.json`. Designs other than `default` can
   get a display name under `designs`. Set `"denoise": false` for clean
   digital masters so their exact colours are kept.
3. Run `python3 tools/build.py <region>/<card>[/<design>]` (or no arguments to
   rebuild everything). It uses Pillow and numpy, plus `pngquant` and `optipng`
   when they are on `PATH`, which give noticeably smaller files.
4. Run `python3 -m unittest discover -s tests` and commit the face, master and
   regenerated manifest together. Pages publishes the push automatically.

The optimizer scales each master to the largest width (at most 1200 px, never
upscaled) that fits the budgets, trying 24, 20 and 16 colours without dithering.

## Manifest

```json
{
  "schemaVersion": 2,
  "cards": [
    {
      "id": "cn/2900",
      "region": "CN",
      "name": {"zh": "上海公共交通卡", "en": "Shanghai Public Transportation Card"},
      "city": {"zh": "上海", "en": "Shanghai"},
      "match": {
        "cityCodes": ["2900"],
        "cityUnionCodes": ["2000"],
        "cardPrefixes": ["31047700"],
        "families": [],
        "serialPrefixes": []
      },
      "designs": [
        {
          "id": "default",
          "file": "faces/cn/2900/default.png",
          "sha256": "…",
          "bytes": 26007,
          "width": 1200,
          "height": 760,
          "colors": 19
        }
      ]
    }
  ]
}
```

Clients match a card by T-Union city code, then City Union city code, then the
longest card-number prefix, then a lowercase substring of the card family name,
then the serial-number prefix. They should verify `sha256` before using a
download, and can append `?v=<sha256 prefix>` to bypass stale caches.
`manifest.json` is cached for 5 minutes and faces for a day.

## Notice

Card names, logos and the 交通联合 / China T-Union and City Union marks belong
to their respective issuers. The artwork here is a simplified recreation, used
only so a user can recognise their own card in the app. The tooling is MIT
licensed (see `LICENSE`).
