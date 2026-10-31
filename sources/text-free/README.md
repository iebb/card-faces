# Text-free card artwork

The text-free collection derives from the real-card recreations already in this
repository. Native built-in ImageGen edits remove lettering, numerals and
wordmarks while preserving the original palette, background shapes,
illustrations and non-letter symbols. Each source is edited separately.

The original source and published PNG are copied without modification to
`text.*` / `text.png` for defaults, or `<design>-text.*` /
`<design>-text.png` for named designs. Designs that already have no lettering
remain unchanged: OKICA, the abstract T-money default and U-Money.

`edits.json` records each card, its stable design ID, the text alternative,
original source and PNG hashes, research references and the exact edit prompt.
The original PNG hashes refer to collection commit `44d5728`.

The text-free exports use the same optimizer as the rest of the collection:
30:19 PNGs, at most 24 colors and strictly less than 40,000 bytes. Only the
edited designs are rebuilt during this migration, preserving the original
published PNGs exactly.
