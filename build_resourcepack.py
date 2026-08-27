from __future__ import annotations

# OpenPVP country flag resource-pack builder.

import hashlib
import io
import json
import shutil
import urllib.request
import zipfile
from pathlib import Path

from PIL import Image

CODES = "AD,AE,AF,AG,AI,AL,AM,AO,AQ,AR,AS,AT,AU,AW,AX,AZ,BA,BB,BD,BE,BF,BG,BH,BI,BJ,BL,BM,BN,BO,BQ,BR,BS,BT,BV,BW,BY,BZ,CA,CC,CD,CF,CG,CH,CI,CK,CL,CM,CN,CO,CR,CU,CV,CW,CX,CY,CZ,DE,DJ,DK,DM,DO,DZ,EC,EE,EG,EH,ER,ES,ET,FI,FJ,FK,FM,FO,FR,GA,GB,GD,GE,GF,GG,GH,GI,GL,GM,GN,GP,GQ,GR,GS,GT,GU,GW,GY,HK,HM,HN,HR,HT,HU,ID,IE,IL,IM,IN,IO,IQ,IR,IS,IT,JE,JM,JO,JP,KE,KG,KH,KI,KM,KN,KP,KR,KW,KY,KZ,LA,LB,LC,LI,LK,LR,LS,LT,LU,LV,LY,MA,MC,MD,ME,MF,MG,MH,MK,ML,MM,MN,MO,MP,MQ,MR,MS,MT,MU,MV,MW,MX,MY,MZ,NA,NC,NE,NF,NG,NI,NL,NO,NP,NR,NU,NZ,OM,PA,PE,PF,PG,PH,PK,PL,PM,PN,PR,PS,PT,PW,PY,QA,RE,RO,RS,RU,RW,SA,SB,SC,SD,SE,SG,SH,SI,SJ,SK,SL,SM,SN,SO,SR,SS,ST,SV,SX,SY,SZ,TC,TD,TF,TG,TH,TJ,TK,TL,TM,TN,TO,TR,TT,TV,TW,TZ,UA,UG,UM,US,UY,UZ,VA,VC,VE,VG,VI,VN,VU,WF,WS,YE,YT,ZA,ZM,ZW".split(",")

PACK_NAME = "OpenPVPCountryFlags-resourcepack-1.21.11.zip"
BUILD = Path(".rp_build")
ROOT = BUILD / "pack"
ATLAS_PATH = ROOT / "assets" / "openpvp" / "textures" / "font" / "flags.png"
FONT_PATH = ROOT / "assets" / "minecraft" / "font" / "default.json"

CELL_W = 13
CELL_H = 8
COLS = 25
ROWS = 10
FIRST_GLYPH = 0xE100


def download_flag(code: str) -> Image.Image:
    url = f"https://flagcdn.com/w40/{code.lower()}.png"
    request = urllib.request.Request(url, headers={"User-Agent": "OpenPVP-ResourcePack-Builder/1.0"})
    with urllib.request.urlopen(request, timeout=20) as response:
        data = response.read()
    image = Image.open(io.BytesIO(data)).convert("RGBA")
    return image.resize((CELL_W, CELL_H), Image.Resampling.LANCZOS)


def build() -> None:
    if BUILD.exists():
        shutil.rmtree(BUILD)
    ATLAS_PATH.parent.mkdir(parents=True, exist_ok=True)
    FONT_PATH.parent.mkdir(parents=True, exist_ok=True)

    atlas = Image.new("RGBA", (COLS * CELL_W, ROWS * CELL_H), (0, 0, 0, 0))

    for i, code in enumerate(CODES):
        try:
            flag = download_flag(code)
        except Exception as exc:
            print(f"WARNING: {code}: {exc}; using transparent fallback")
            flag = Image.new("RGBA", (CELL_W, CELL_H), (0, 0, 0, 0))
        x = (i % COLS) * CELL_W
        y = (i // COLS) * CELL_H
        atlas.alpha_composite(flag, (x, y))

    atlas.save(ATLAS_PATH, optimize=True)

    chars = []
    for row in range(ROWS):
        row_chars = []
        for col in range(COLS):
            index = row * COLS + col
            row_chars.append(chr(FIRST_GLYPH + index))
        chars.append("".join(row_chars))

    font = {
        "providers": [
            {
                "type": "bitmap",
                "file": "openpvp:font/flags.png",
                "ascent": 7,
                "height": 8,
                "chars": chars,
            }
        ]
    }
    FONT_PATH.write_text(json.dumps(font, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    pack_meta = {
        "pack": {
            "pack_format": 75,
            "description": "OpenPVP Country Flags • Minecraft 1.21.11",
        }
    }
    (ROOT / "pack.mcmeta").write_text(json.dumps(pack_meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    mapping = "\n".join(f"{code}=E{0x100 + i:03X}" for i, code in enumerate(CODES)) + "\n"
    (ROOT / "flags.properties").write_text(mapping, encoding="utf-8")

    with zipfile.ZipFile(PACK_NAME, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in sorted(ROOT.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(ROOT).as_posix())

    data = Path(PACK_NAME).read_bytes()
    sha1 = hashlib.sha1(data).hexdigest()
    Path("SHA1.txt").write_text(sha1 + "\n", encoding="utf-8")
    print(f"Built {PACK_NAME}: {len(data)} bytes, SHA-1 {sha1}")


if __name__ == "__main__":
    build()
