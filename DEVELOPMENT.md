# G9 Battle Sprites (Gen 3): developer guide

For contributors. Players only need the [README](README.md).

## Assets

Everything ships in `assets/atlas/`. No page is larger than 4096×4096, the texture limit on
many Android GPUs (a larger image fails to load there and the engine shows a red missing-pic
box).

- `battle_<variant>_<n>.png`: four variants (`front`, `front_shiny`, `back`, `back_shiny`),
  several pages each. A page holds blocks of uniform `fs × fs` cells; a species' frames sit in
  consecutive cells of one block, and the index records the block's corner (`ox`, `oy`).
- `party_icons_0.png`: two-frame 32×32 menu icons for #387–1025 and the forms, one page.
- `dex_fronts_0.png`: the cart-style 64×64 Ruby / Sapphire / Emerald Pokédex pics, from a
  pokeemerald-expansion checkout (`graphics/pokemon/<id>/anim_front_gba.png`, else
  `anim_front.png`, else `front.png`); a species with none uses its base species' pic.
- `data/atlas_index.lua`: each species (and form) to its engine `slot` (for Generations 1–3
  the game's own internal species id, read with the names from the engine's extracted data,
  `--gen3-data`), its cells, and for back pics where the Pokémon sits in its frame
  (`cx0, cy0, cx1, cy1`).

The atlases are built from the third-party DBK sprite pack and the "icones animados" icon
pack (not in this repo; credits in [CREDITS.md](CREDITS.md)). Rebuild them with:

```bash
python tools/build_atlas.py --sheets <DBK pack>/assets \
    --payload ../national_dex_gen3/data/species \
    --dbk <dbk_data.lua> --icons <icon_data.lua> --icon-atlas <party_icons.png>
```

Output is deterministic: the same inputs give identical bytes. Supporting tools:

- `tools/trim_loops.py` -> `tools/loop_trims.json`: long animations are trimmed to the median
  length of their kind (58 frames for fronts, 52 for backs), cut where the loop closes on a
  matching frame; a sheet with no clean loop keeps every frame.
- `tools/back_framing.py` -> `tools/back_framing.json`: back pics are framed like the cart's:
  the top of the body on the row the cart sprite's body starts, at the clean scale (1×, 1.5× or
  2×, never below 1×) nearest the cart sprite's height, measured on the first frame. A body
  starting so low that fewer than 28 rows show above the text box is raised
  (`MIN_BACK_SHOWN` in `tools/build_atlas.py`); a Pokémon with no reference is shown whole,
  feet on the bottom edge.
- `tools/back_fit.py` -> `tools/back_fit.json`: with Gen 3 HD Sprites, a Gen 1–3 back pic is
  zoomed and placed over the cart's own back sprite (best silhouette overlap, or bounding boxes
  when the poses differ too much).

Every file under `tools/` and `tests/` is listed by exact path in `.modkitignore` so none of
them ships; add a line for each new one.

## How it draws

`src/hooks.lua` wraps three functions of the gen3 engine's `Pokemon` module: `frontPic`,
`backPic` and `icon`. Each answers for the species the atlas has art for and calls the original
for everything else; the wrappers are reinstalled after each species reload and never wrapped
twice.

Pics are rendered from the current frame into a canvas (a bounded cache, least recently used
first). In battle, fronts and backs are drawn at full size in a canvas that may extend past the
64×64 pic box (up to 96 px, `BACK_WIDE_MAX` in `src/atlas.lua`), so wings and tails are never
cut by the canvas; a small wrap on `love.graphics.draw` points the engine's draw at that
canvas's centre. If the wrap can't be installed (or `BACK_WIDE = false`), a giant is reduced just
far enough to keep 70% of its width in view. Other screens (Pokédex, summary, PC) get the
fit-to-box pic. Animation runs at 8 frames per second; battlers of one species share one clock.

With Gen 3 HD Sprites, battle pics are drawn at window resolution and `data/sprite_scale.lua`
tunes each Pokémon's front and back size and offset by hand (edit and restart, no rebuild).
Each front tag also passes `top`: the cell's `uy0` in `data/atlas_index.lua`, which is the
first row of art over the whole animation, written by `tools/build_atlas.py`. With that,
Gen 3 HD Sprites' Battle Fit pulls the camera back to fit the art, not the frame's empty
margin.

## Tests

```sh
luajit tests/hooks_test.lua            # the gate test
luajit tests/forms_coverage_test.lua   # forms coverage
# plus the atlas layout, back framing, clean state, dex HD and gen3 coverage suites in tests/
```

Keep [README.md](README.md) describing the mod as it is now (players read it); what changed
goes in the release notes.
