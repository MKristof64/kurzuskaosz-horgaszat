# KurzusKáosz — Kifogjuk az okokat

Görgethető, magyar nyelvű 3D horgásztörténet és térbeli Ishikawa-diagram. A hal a szájánál kapcsolódó zsinóron emelkedik ki a vízből, majd fejjel felfelé lóg. Az öt okcsoport vastag, háttér nélküli térbeli betűi fokozatosan jelennek meg körülötte.

[Weboldal](https://kurzuskaosz-hal-3d.kristof-madarasz159.chatgpt.site) · [Modellfájlok](https://github.com/MKristof64/kurzuskaosz-horgaszat/releases/tag/model-v1)

- Természetes olíva, nád, homok és bronz színek; animált vízfelszín, horgászbot, zsinór, úszó és vízcseppek.
- Öt kategória és az eredeti húsz ok; összesen 32 eredeti magyar szövegblokk.
- Szabadon forgatható teljes diagram, OBJ- és PNG-letöltések; külön modellnézegető a `/modell` útvonalon.
- A hal 3 676 000 háromszögből áll. A háttér nélküli webes modell 4 717 710 háromszög, a betűk mélysége körülbelül 3,6 mm a modell léptékében.
- Mobilos elrendezés, csökkentett mozgás támogatása, látható fókuszjelölések és 3D-betöltési hibára PNG-tartalék.

## Helyi indítás

Node.js 22.13 vagy újabb és pnpm szükséges.

```sh
pnpm install
pnpm assets
pnpm dev
```

A nagy, Blenderrel előállított modellek és képek GitHub Release-fájlok. A `pnpm assets` a nyilvános kiadásból tölti le és SHA-256 alapján ellenőrzi őket. A Git a weboldal és a modellgenerátorok forrását tartalmazza; a generált állományok jegyzéke a `generated-assets.json`.

```sh
pnpm lint
pnpm exec tsc --noEmit
pnpm build
```

A build a generált állományok ellenőrzése után készít Vinext/Cloudflare Worker-kimenetet. A Sites-feltöltés archívuma ezeket a pontos modelleket, képeket és OBJ-letöltési részeket tartalmazza.

## Modellforrás és tartalom

A Blender 4.5-generátorok, az eredeti magyar szövegek és a Patrick Hand betűkészlet a `model-source/` mappában találhatók; az ottani README leírja az előállítás lépéseit. A betűkészlethez mellékelt SIL Open Font License érvényes.

A modell csapósügérre épülő művészi rekonstrukció, nem egy valódi példány szkennelése. A kiinduló halszálkadiagram nem tartalmazott halanatómiát. Az eredeti OBJ és PNG a korábbi, táblás változatot őrzi; a történethez külön háttér nélküli GLB készült.

Anatómiai támpontok: [Fishes of Australia](https://fishesofaustralia.net.au/home/species/3690), [Australian Museum](https://australian.museum/learn/animals/fishes/redfin-perca-fluviatilis/).
