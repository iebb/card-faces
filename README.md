# card-faces

Card-face artwork for [CardBal / TransitICReader](https://github.com/iebb/TransitICReader).
The app downloads `manifest.json` and the PNGs listed in it, so new faces ship
without an app update.

The first collection covers the transit cards of mainland China's 20 largest
cities by 2024 GDP. Each face is a flat vector-style recreation of the city's
real card front. Card numbers, QR codes, serials and small print are removed.

| City | Card | T-Union city code | Card prefix |
| --- | --- | --- | --- |
| 上海 Shanghai | 上海公共交通卡 | 2900 (City Union 2000) | 31047700 |
| 北京 Beijing | 北京一卡通 | 1000 | 31051700 |
| 深圳 Shenzhen | 深圳通 | 5840 | 31048704 |
| 重庆 Chongqing | 宜居畅通卡 | 6900 | 31049200, 31049201 |
| 广州 Guangzhou | 羊城通 | 5810 | 31048703 |
| 苏州 Suzhou | 苏州市民卡 | 3050 | 31048303 |
| 成都 Chengdu | 天府通 | 6510 | 31047800 |
| 杭州 Hangzhou | 杭州通 | 3310 | 31048801 |
| 武汉 Wuhan | 武汉通 | 5210 | 31051400 |
| 南京 Nanjing | 南京市民卡 | 3010 | 31048300 |
| 宁波 Ningbo | 宁波交通卡 | 3320 | 31048802 |
| 天津 Tianjin | 天津城市卡 | 1121 | 31049102 |
| 青岛 Qingdao | 琴岛通 | 4520 | 31049304 |
| 无锡 Wuxi | 太湖交通卡 | 3020 | 31048312 |
| 长沙 Changsha | 潇湘卡 | 5510 | 31048200 |
| 郑州 Zhengzhou | 绿城通 | 4910 | 31050702 |
| 福州 Fuzhou | 榕城通 | 3910 | 31050600 |
| 济南 Jinan | 泉城通 | 4510 | 31049308 |
| 合肥 Hefei | 合肥通 | 3610 | 31049902 |
| 佛山 Foshan | 广佛通 | 5880 | 31048707 |

## Budgets

Every published face must:

- be a PNG with a 30:19 aspect ratio (1200×760 when it fits);
- use at most **24 colours**;
- be smaller than **40,000 bytes**.

`tools/validate.py` enforces this in CI, together with the sha256, size and
colour count recorded in `manifest.json`.

## Layout

```
catalog.json        hand-edited metadata: names, city codes, card prefixes
sources/<region>/   full-resolution masters (WebP)
faces/<region>/     optimized faces served to the app
manifest.json       generated from catalog.json + faces/
tools/build.py      optimizer and manifest generator
tools/validate.py   budget and manifest checks
```

## Adding or updating a face

1. Put the master image in `sources/<region>/<slug>.webp` (or `.png`).
2. Add or edit the entry in `catalog.json`.
3. Run `python3 tools/build.py <slug>` (or no arguments to rebuild everything).
   The script installs nothing; it uses Pillow and numpy, plus `pngquant` and
   `optipng` when they are on `PATH`, which give noticeably smaller files.
4. Run `python3 -m unittest discover -s tests` and commit the face, master and
   regenerated manifest together.

The optimizer scales each master to the largest width from 1200 px down that
fits the budgets. It tries 24, 20 and 16 colours at each width, without dithering.

## Manifest

```json
{
  "schemaVersion": 1,
  "faces": [
    {
      "id": "cn-shanghai",
      "region": "CN",
      "city": {"zh": "上海", "en": "Shanghai"},
      "name": {"zh": "上海公共交通卡", "en": "Shanghai Public Transportation Card"},
      "cityCodes": ["2900"],
      "cityUnionCodes": ["2000"],
      "cardPrefixes": ["31047700"],
      "file": "faces/cn/shanghai.png",
      "sha256": "…",
      "bytes": 26007,
      "width": 1200,
      "height": 760,
      "colors": 24
    }
  ]
}
```

Clients match a card by T-Union city code, then legacy City Union city code,
then the longest card-number prefix. They should verify `sha256` before using a
download. Files are served from
`https://raw.githubusercontent.com/iebb/card-faces/master/`, with
`https://cdn.jsdelivr.net/gh/iebb/card-faces@master/` as a mirror that is
reachable from mainland China.

## Notice

Card names, logos and the 交通联合 / China T-Union and City Union marks belong
to their respective issuers. The artwork here is a simplified recreation, used
only so a user can recognise their own card in the app. The tooling is MIT
licensed (see `LICENSE`).
