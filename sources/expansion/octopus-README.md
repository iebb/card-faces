# Hong Kong Standard Octopus

Six exports cover the real Standard Adult (dark gray), Child (pale blue) and
Elder (green) On-Loan Octopus fronts. Adult is the default. The colorful
asymmetric infinity ribbon remains decorative artwork in all six exports.
Ordinary lettering appears only in `text`, `child-text` and `elder-text`.

The supplied issuer category images are only 54 x 34 pixels. The larger official
product composite supplies secondary evidence for the visible Adult ribbon,
but occludes the lower half. Further research found three clearer 238 x 150
standalone fronts linked by the issuer's October 17, 2017 card-replacement press
release. These independently confirm all three categories, the common ribbon,
the top-left `八達通 Octopus` branding, and the lower-right `小童 Child` and
`長者 Elder` labels. The Adult front has no category label. The issuer originals
and relevant HTML are preserved byte for byte in `octopus-references/`.

Built-in native ImageGen generated the three decorative bases sequentially.
No extra generation agents or API/CLI image fallback were used. Exact verified
lettering was added deterministically with `octopus-export.py`; its font and
layout inputs are recorded in `octopus-report.json`. Typography approximates
the visible issuer lettering, rather than claiming access to production fonts.
Curves and shades are simplified recreations; no unreadable fine copy was
invented. The 2017 reference does not prove every outlet's current card revision.

The report includes the exact native prompts, original research, provenance,
reference and external-master hashes, preservation inventory, limits and final
export metadata. Large native masters remain outside the current Git tree.
The compact inputs in `sources/hk/octopus/` are byte-identical to the final
PNGs in `faces/hk/octopus/`. Denoising is disabled. The existing optimizer
preserves their pixels and bytes on scoped rebuilds:

```
python3 tools/build.py hk/octopus
python3 tools/validate.py
python3 -m unittest discover -s tests
python3 tools/publish.py
```

`previews/octopus-standard.png` is a contact sheet of the actual final PNGs.
At the Octopus addition, all 130 previous faces and their sources were preserved,
bringing the collection to 40 card types and 136 faces. Subsequent character
and shop-promotion curation removes 15 other faces; the current collection has
40 card types and 121 faces. All six Octopus faces and sources remain unchanged. The original
`octopus-report.json` records the historical addition and its validation.
Local publication builds `dist/`;
Cloudflare Pages rebuilds the live collection from `master` on push.
