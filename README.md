# card-faces

Card-face artwork for [CardBal / TransitICReader](https://github.com/iebb/TransitICReader).
The app downloads `manifest.json` and the PNGs listed in it, so new faces ship
without an app update.

The collection contains **40 card types and 136 faces**, including six Standard
Octopus exports for Hong Kong.

Faces are served from **https://faces.cardb.al/**, a Cloudflare Pages site
that rebuilds from `master` on every push. jsDelivr
(`https://cdn.jsdelivr.net/gh/iebb/card-faces@master/`, reachable from mainland
China) and raw GitHub are fallback mirrors with the same paths.

## Layout

```
catalog.json                        hand-edited metadata: names, matching keys
sources/<region>/<card>/<design>.*  build inputs (WebP or PNG)
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

### Text-free faces

The main faces keep the real card's colors, background artwork and illustrations,
with ordinary lettering, numbers and wordmarks removed. Lettering that functions
as decorative artwork is kept: PASMO's letters complete its train and bus motif.
Other exceptions are Edy's background R, the Climate Card GO ribbon, Changsha's
background brushwork and the geometric JS emblems on Suzhou and Nanjing cards.
Each exception also offers a fully text-free `no-text.png`. Informational labels,
city names, service details and small print stay in the **with text** alternatives:

- `default.png` pairs with `text.png`;
- named designs such as `ryan.png` pair with `ryan-text.png`.

Existing design IDs keep working, including PASMO's original `text.png` choice.
Faces that already had no lettering are unchanged. The original masters and
published PNGs are preserved byte for byte in the text alternatives.
Research references, edit prompts and preservation
hashes are recorded in [the text-removal notes](sources/text-free/README.md).
See the [before/after comparison](previews/text-free-comparison.png) or
[all text-free choices](previews/text-free-all.png). The
[decorative exceptions](previews/decorative-exceptions.png) compare each default
with its fully text-free and original text alternatives.

The current text-free inputs are the optimized PNG exports, with denoising
disabled so rebuilding preserves their pixels. Full-resolution generated masters
remain in commit `8b9168c`; original text masters remain in the current tree.

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

All app defaults are available here and download on demand. `bundledAsset`
identifies the legacy app asset name, so existing cards and backups keep their
selected artwork after a bundle is removed. The apps prefer the downloaded
face; Suica, PASMO, ICOCA, T-money and EZL remain as small offline fallbacks.

| Folder | Designs | Matched by |
| --- | --- | --- |
| `jp/suica`, `jp/icoca`, `jp/hayakaken`, `jp/sugoca`, `jp/manaca`, `jp/kitaca`, `jp/nimoca`, `jp/toica` | default, text | family name, serial prefix |
| `jp/pasmo` | default, no-text, text | family name, serial prefix |
| `jp/edy` | default, no-text, text | family name |
| `jp/waon`, `jp/nanaco` | default, text | family name |
| `jp/okica` | default | family name |
| `kr/tmoney` | default, logo, apeach, go-green, kpass, ryan, safe, text alternatives | family name |
| `kr/ezl` | default, duty-free, myeongdong, pop, tour, text alternatives | family name |
| `kr/climate-card` | default, no-text, text | family name |
| `fr/la-carte` | default, blue, text, blue-text | family name |
| `mn/umoney` | default | family name |
| `sg/ezlink` | default, text | family name |

The Korean additions recreate real issuer and authorized-shop references in a
flat vector style. See [the designs](previews/korean-designs.png) and
[their sources and generation brief](sources/kr/README.md). These are familiar
standard, character, convenience-store and tourist designs, not a sales ranking.

### Additional designs

The expanded collection adds twelve researched physical designs across the six
covered countries: four Chinese city cards, three Japanese visitor designs, two
Singapore EZ-Link designs, K-PASS LINE FRIENDS T-money, Nice's Tour de
France yellow-jersey La Carte, and the TDB/U-Money Britto Einstein card.
Existing defaults stay unchanged. Each addition has a normal cleaned choice and
a selectable text version. Three decorative-lettering designs also offer a fully
text-free alternative.

See the [new designs](previews/expansion-designs.png) and
[research and generation notes](sources/expansion/README.md).
The apps rank designs for the physical card's type first, then designs for its
city in the same country, regardless of the artwork currently selected.

## Budgets

Every published face must:

- be a PNG with a 30:19 aspect ratio (1200×760 when it fits);
- use at most **24 colours**;
- be smaller than **40,000 bytes**.

`tools/validate.py` enforces this in CI, together with the sha256, size and
colour count recorded in `manifest.json`.

The Git package must also stay below **50,000,000 bytes** for compatibility
with jsDelivr edges that enforce that limit. Validation counts tracked and new
files while excluding ignored build outputs. Keep large generated masters in
Git history and use optimized inputs in the current tree.

## Adding or updating a design

1. Put the master in `sources/<region>/<card>/<design>.webp` (or `.png`). Use
   `default` for the card's main face. Chinese cards use the T-Union city code
   as `<card>`.
2. Add or edit the card in `catalog.json`. Designs other than `default` can
   get a display name under `designs`. Set `"denoise": false` for clean
   digital masters so their exact colours are kept. A design can override this
   setting with its own `denoise` value under `designs`.
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
