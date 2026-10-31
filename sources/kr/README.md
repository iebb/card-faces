# Korean card references

Researched on 31 October 2026. The new PNG masters were recreated with the
built-in ImageGen tool from the actual card fronts shown by the issuer or its
authorized shop. They are simplified vector-style raster artwork, not original
issuer files or exact facsimiles. They preserve the principal composition,
colors and issuer marks; fine lettering and icon geometry may differ.
No claim of official endorsement or measured popularity is made.

This page describes the retained collection. Kakao Little Friends Ryan/Apeach
and K-PASS LINE FRIENDS variants have been retired; their current-tree sources,
published faces and character previews were removed. See the
[curation notes](../curation/README.md). Historical generation metadata remains.
The two shop-promotion designs now use original rectangle-only SVG masters and
generic color names. Their promotional text alternatives and original image
masters are removed.

## T-money

T-money Shop displays its authorization as an official Tmoney online seller.
Three non-character physical designs remain from its card catalog:

| Master | Real card | Reference |
| --- | --- | --- |
| `tmoney/go-green.png` | Eco-friendly Go Green | [Product 385](https://t-zone.co.kr/product/detail.html?product_no=385&cate_no=30&display_group=1) |
| `tmoney/kpass.png` | K-PASS BASIC | [Product 398](https://t-zone.co.kr/product/detail.html?product_no=398&cate_no=30&display_group=1) |
| `tmoney/safe.png` | Public Transport Safe Card | [Product 267](https://t-zone.co.kr/product/detail.html?product_no=267&cate_no=30&display_group=1) |

The pre-existing `default` and `logo` designs and their tokens remain available.
The three researched fronts remain additional choices. Retired character
selection tokens map to the abstract T-money default.

## EZL / Cashbee

Together with the existing yellow EZL K-PASS mascot default, the collection has
five designs. Cashbee is part of the same card family.

| Master | Real card | Issuer reference |
| --- | --- | --- |
| `ezl/default.png` | Yellow EZL K-PASS mascot | [EZL services](https://www.myezl.com/en/sub/service.do), `card2.png` |
| `ezl/duty-free.png` | Graphite and lime: original generic blocks | Historical palette reference: [EZL services](https://www.myezl.com/en/sub/service.do), middle card in `card3.png` |
| `ezl/myeongdong.png` | Navy and citron: original generic blocks | Historical palette reference: [EZL services](https://www.myezl.com/en/sub/service.do), right card in `card3.png` |
| `ezl/pop.png` | Orange POP Cashbee | [EZL services](https://www.myezl.com/en/sub/service.do), bottom-left card in `card7.png` |
| `ezl/tour.png` | Turquoise Jeonju 2 Days pass | [Cashbee partner cards](https://www.cashbee.co.kr/cb/service/cardAlliance.do), middle card in `card_regular_01.png` |

Issuer image paths are under `https://www.myezl.com/resource/images/service/`;
the Jeonju source is
`https://www.cashbee.co.kr/resource/img/front/cashbee/service_introduce/card_regular_01.png`.

The stable IDs `duty-free` and `myeongdong` now refer only to the generic blocks.
Their SVG masters contain only solid rectangles; `tools/generic_blocks.py`
exports them deterministically with the existing optimizer. Neither has a
promotional text alternative. POP Cashbee and Jeonju's ordinary two-day transit
pass were inspected and retained: neither active face has coupon redemption,
shop benefits or discount content.

## Generation and export

Each new design was generated separately with the matching source image as its
edit reference. The shared generation brief was:

> Recreate only the actual printed card rectangle in the reference, faithfully
> preserving its composition, colors, main lettering, characters and logos.
> Rotate portrait card artwork clockwise into a horizontal 30:19 card face.
> Render edge to edge with square corners, crisp flat vector-style shapes and
> restrained solid colors. Remove the product-photo surroundings, shadows, glare,
> serial numbers, QR codes and legal microprint. Do not invent graphic elements,
> redesign the layout, or add textures, gradients or dithering.

The native outputs have small aspect-ratio and tonal variations. The repository
build deterministically cover-crops them to 1200 x 760, median-filters generated
noise, merges nearby palette entries, removes isolated pixels and encodes indexed
PNGs without dithering. Current published PNGs are validated against the
24-color and fewer-than-40,000-byte limits. Retained sources remain here;
only current optimized `faces/` files are published by Cloudflare Pages.

Exact generation prompts retained for the three T-money non-character cards
are in [generation-prompts.json](generation-prompts.json).
