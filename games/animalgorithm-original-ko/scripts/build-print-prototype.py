#!/usr/bin/env python3
"""Build a printable Animal-gorithm Original KO paper prototype.

Requires:
  pip install reportlab pymupdf pillow

The PLIX animal deck PDF is intentionally supplied at build time and is not
bundled by this script. This keeps the repository source/data separate from
third-party source assets while license scope is being confirmed.
"""
from __future__ import annotations

import argparse
import io
import json
import os
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, A3, landscape, portrait
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

def _font_candidates(bold=False):
    env = os.environ.get("ANIMALGORITHM_KO_FONT_BOLD" if bold else "ANIMALGORITHM_KO_FONT_REGULAR")
    names = [env] if env else []
    if bold:
        names += [
            "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
            "C:/Windows/Fonts/malgunbd.ttf",
            "/Library/Fonts/NanumGothicBold.ttf",
        ]
    else:
        names += [
            "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
            "C:/Windows/Fonts/malgun.ttf",
            "/Library/Fonts/NanumGothic.ttf",
        ]
    return [Path(x) for x in names if x]

def _find_font(bold=False):
    for p in _font_candidates(bold):
        if p.exists(): return str(p)
    kind = "bold" if bold else "regular"
    raise FileNotFoundError(
        f"Korean {kind} TrueType font not found. Install NanumGothic or set "
        f"ANIMALGORITHM_KO_FONT_{'BOLD' if bold else 'REGULAR'}."
    )

FONT_REG = _find_font(False)
FONT_BOLD = _find_font(True)
ANIMALS = []
CATEGORIES = []

def load_project_data(data_dir: Path):
    global ANIMALS, CATEGORIES
    animals_doc = json.loads((data_dir / "animals.plix-ko.json").read_text(encoding="utf-8"))
    cats_doc = json.loads((data_dir / "category_pairs.plix-ko.json").read_text(encoding="utf-8"))
    ANIMALS = [(a["sourcePage"], a["sourceSlot"], a["nameEn"], a["nameKo"]) for a in animals_doc["animals"]]
    CATEGORIES = [(p["leftEn"], p["rightEn"], p["leftKo"], p["rightKo"]) for p in cats_doc["pairs"]]
    if len(ANIMALS) != 46:
        raise ValueError(f"Expected 46 named animals, got {len(ANIMALS)}")
    if len(CATEGORIES) != 8:
        raise ValueError(f"Expected 8 Category Idea pairs, got {len(CATEGORIES)}")

# Source slot order is column-major on each PLIX sheet:
# 1=col1/top, 2=col1/bottom, 3=col2/top, ...
def slot_to_col_row(slot: int) -> tuple[int, int]:
    return (slot - 1) // 2, (slot - 1) % 2


def fit_font(text: str, font_path: str, start: int, min_size: int, max_width: float) -> ImageFont.FreeTypeFont:
    size = start
    while size >= min_size:
        f = ImageFont.truetype(font_path, size=size)
        box = f.getbboxhtext)
        if box[2] - box[0] <= max_width:
            return f
        size -= 2
    return ImageFont.truetype(font_path, size=min_size)


def center_text(draw: ImageDraw.ImageDraw, xy: tuple[float, float], text: str, font: ImageFont.FreeTypeFont, fill="black"):
    box = draw.textbbox((0, 0), text, font=font)
    w = box[2] - box[0]
    h = box[3] - box[1]
    draw.text((xy[0] - w/2, xy[1] - h/2 - box[1]), text, font=font, fill=fill)


def card_crop(page_img: Image.Image, slot: int) -> Image.Image:
    col, row = slot_to_col_row(slot)
    cw = page_img.width / 4
    ch = page_img.height / 2
    inset = 4
    box = (int(col*cw)+inset, int(row*ch)+inset, int((col+1)*cw)-inset, int((row+1)*ch)-inset)
    return page_img.crop(box).convert("RGB")


def localize_animal_card(img: Image.Image, ko: str, en: str) -> Image.Image:
    out = img.copy()
    d = ImageDraw.Draw(out)
    w, h = out.size
    # Cover only the English animal-name band; preserve PLIX branding and URL.
    d.rectangle((0.06*w, 0.705*h, 0.94*w, 0.875*h), fill="white")
    ko_font = fit_font(ko, FONT_BOLD, int(h*0.070), int(h*0.045), 0.86*w)
    en_font = fit_font(en, FONT_REG, int(h*0.030), int(h*0.022), 0.78*w)
    center_text(d, (w/2, h*0.755), ko, ko_font)
    center_text(d, (w/2, h*0.835), en, en_font, fill="#555555")
    return out


def draw_wrapped_center(draw, center_x, center_y, text, font_path, start_size, max_width, fill="black", max_lines=2):
    words = text.split()
    if len(words) <= 1:
        font = fit_font(text, font_path, start_size, int(start_size*0.7), max_width)
        center_text(draw, (center_x, center_y), text, font, fill)
        return
    # Try one line, then balanced 2 lines.
    font = fit_font(text, font_path, start_size, int(start_size*0.7), max_width)
    if font.getbbox(text)[2] - font.getbbox(text)[0] <= max_width:
        center_text(draw, (center_x, center_y), text, font, fill)
        return
    best = None
    for i in range(1, len(words)):
        a, b = " ".join(words[:i]), " ".join(words[i:])
        f = fit_font(max((a,b), key=len), font_path, start_size, int(start_size*0.65), max_width)
        widths = [(f.getbboxht)[2]-f.getbbox(t)[0]) for t in (a,b)]
        score = max(widths) + abs(widths[0]-widths[1])*0.2
        if best is None or score < best[0]: best = (score,a,b,f)
    _, a, b, f = best
    center_text(draw, (center_x, center_y - f.size*0.62), a, f, fill)
    center_text(draw, (center_x, center_y + f.size*0.62), b, f, fill)


def localize_category_card(img: Image.Image, idx: int, left_ko: str, right_ko: str) -> Image.Image:
    out = img.copy()
    d = ImageDraw.Draw(out)
    w, h = out.size
    # Replace the English title and central labels, retaining PLIX branding / URL / divider.
    d.rectangle((0.02*w, 0.060*h, 0.98*w, 0.205*h), fill="white")
    title_font = fit_font("카테고리 아이디어", FONT_BOLD, int(h*0.065), int(h*0.045), 0.92*w)
    center_text(d, (w/2, h*0.125), "카테고리 아이디어", title_font)
    d.rectangle((0.02*w, 0.43*h, 0.98*w, 0.73*h), fill="white")
    # redraw divider through covered band
    d.line((w*0.5, h*0.24, w*0.5, h*0.82), fill="black", width=max(4, int(w*0.006)))
    if idx < 7:
        draw_wrapped_center(d, w*0.25, h*0.585, left_ko, FONT_BOLD, int(h*0.055), 0.42*w)
        draw_wrapped_center(d, w*0.75, h*0.585, right_ko, FONT_BOLD, int(h*0.050), 0.42*w)
    else:
        small = ImageFont.truetype(FONT_REG, int(h*0.022))
        center_text(d, (w/2, h*0.215), "SOURCE 형식: X / X가 아님", small, fill="#555555")
        # large handwriting box on left
        pad = 0.08*w
        y1, y2 = 0.48*h, 0.68*h
        d.rounded_rectangle((pad, y1, 0.46*w, y2), radius=int(w*0.02), outline="black", width=max(3,int(w*0.005)))
        hint = ImageFont.truetype(FONT_REG, int(h*0.025))
        center_text(d, (0.27*w, 0.585*h), "기준을 적으세요", hint, fill="#777777")
        right_font = fit_font("왼쪽 기준이 아님", FONT_BOLD, int(h*0.045), int(h*0.034), 0.42*w)
        center_text(d, (0.75*w, 0.585*h), "왼쪽 기준이 아님", right_font)
    return out


def pil_to_reader(img: Image.Image) -> ImageReader:
    bio = io.BytesIO()
    img.save(bio, format="PNG", optimize=True)
    bio.seek(0)
    return ImageReader(bio)


def draw_cut_grid(c: canvas.Canvas, page_w, page_h, card_w, card_h, cols=4, rows=2):
    x0=(page_w-cols*card_w)/2
    y0=(page_h-rows*card_h)/2
    c.setStrokeColor(colors.HexColor("#777777")); c.setLineWidth(0.45); c.setDash(2,2)
    for col in range(cols+1):
        x=x0+col*card_w; c.line(x,y0,x,y0+rows*card_h)
    for row in range(rows+1):
        y=y0+row*card_h; c.line(x0,y,x0+cols*card_w,y)
    c.setDash()
    return x0,y0


def draw_card_sheet(c: canvas.Canvas, cards: list[Image.Image], footer: str):
    pw,ph=landscape(A4); c.setPageSize((pw,ph))
    card_h=99*mm; card_w=card_h*(198/306)
    x0,y0=draw_cut_grid(c,pw,ph,card_w,card_h)
    # cards list in visual row-major order.
    for i,img in enumerate(cards):
        row=i//4; col=i%4
        x=x0+col*card_w; y=y0+(1-row)*card_h
        c.drawImage(pil_to_reader(img),x,y,width=card_w,height=card_h,mask='auto')
    c.setFont("Nanum",6.5); c.setFillColor(colors.HexColor("#666666"))
    c.drawCentredString(pw/2,2.3*mm,footer)
    c.showPage()


def rounded_label(c, x, y, w, h, text, font="NanumBold", size=12):
    c.setStrokeColor(colors.black); c.setFillColor(colors.white); c.setLineWidth(1)
    c.roundRect(x,y,w,h,3*mm,stroke=1,fill=1)
    c.setFillColor(colors.black); c.setFont(font,size)
    c.drawCentredString(x+w/2, y+h/2-size*0.34, text)


def draw_custom_category_card(c, x,y,w,h, freeform=False, serial=1):
    c.setStrokeColor(colors.black); c.setFillColor(colors.white); c.rect(x,y,w,h,stroke=1,fill=1)
    c.setFont("Nanum",6.5); c.setFillColor(colors.HexColor("#555555")); c.drawString(x+4*mm,y+h-8*mm,"동물고리즘 Original KO")
    c.setFillColor(colors.black); c.setFont("NanumBold",13); c.drawCentredString(x+w/2,y+h-17*mm,"직접 작성 카테고리")
    c.setLineWidth(1.3); c.line(x+w/2,y+15*mm,x+w/2,y+h-24*mm)
    if freeform:
        c.setFont("NanumBold",9); c.drawCentredString(x+w/4,y+h-29*mm,"LEFT 기준")
        c.drawCentredString(x+3*w/4,y+h-29*mm,"RIGHT 기준")
        for xx in [x+4*mm,x+w/2+4*mm]:
            c.roundRect(xx,y+27*mm,w/2-8*mm,29*mm,2*mm,stroke=1,fill=0)
        c.setFont("Nanum",6.5); c.setFillColor(colors.HexColor("#666666")); c.drawCentredString(x+w/2,y+7*mm,"PROJECT DEFAULT - 두 범주가 겹치지 않게 작성")
    else:
        c.setFont("NanumBold",9); c.drawCentredString(x+w/4,y+h-29*mm,"기준 X")
        c.drawCentredString(x+3*w/4,y+h-29*mm,"X가 아님")
        c.roundRect(x+5*mm,y+29*mm,w/2-10*mm,28*mm,2*mm,stroke=1,fill=0)
        c.setFont("Nanum",7.2); c.setFillColor(colors.HexColor("#666666")); c.drawCentredString(x+3*w/4,y+44*mm,"왼쪽에 쓴 기준의 반대")
        c.drawCentredString(x+w/2,y+7*mm,"PROJECT DEFAULT - 원본형(X / X가 아님)")



def draw_source_category_card(c, x,y,w,h, left_ko, right_ko, custom=False):
    c.setStrokeColor(colors.black); c.setFillColor(colors.white); c.rect(x,y,w,h,stroke=1,fill=1)
    c.setFillColor(colors.HexColor("#555555")); c.setFont("Nanum",6.2)
    c.drawString(x+4*mm,y+h-7.5*mm,"PLIX Category Idea - 한국어판")
    c.setFillColor(colors.black); c.setFont("NanumBold",13); c.drawCentredString(x+w/2,y+h-17*mm,"카테고리 아이디어")
    c.setLineWidth(1.3); c.line(x+w/2,y+15*mm,x+w/2,y+h-24*mm)
    if custom:
        c.setFont("NanumBold",8.5); c.drawCentredString(x+w/4,y+h-29*mm,"기준 X")
        c.drawCentredString(x+3*w/4,y+h-29*mm,"X가 아님")
        c.roundRect(x+5*mm,y+31*mm,w/2-10*mm,27*mm,2*mm,stroke=1,fill=0)
        c.setFont("Nanum",6.8); c.setFillColor(colors.HexColor("#666666")); c.drawCentredString(x+w/4,y+43*mm,"기준을 크게 적으세요")
        c.setFillColor(colors.black); c.setFont("NanumBold",8); c.drawCentredString(x+3*w/4,y+44*mm,"왼쪽 기준이 아님")
    else:
        # Fit using ReportLab font size to each half.
        def fit_pdf(text, maxw, start=11.5, minimum=7.2):
            size=start
            while size>minimum and pdfmetrics.stringWidth(text,"NanumBold",size)>maxw:
                size-=0.4
            return size
        ls=fit_pdf(left_ko,w/2-8*mm); rs=fit_pdf(right_ko,w/2-8*mm)
        c.setFont("NanumBold",ls); c.drawCentredString(x+w/4,y+h*0.49,left_ko)
        c.setFont("NanumBold",rs); c.drawCentredString(x+3*w/4,y+h*0.49,right_ko)
    c.setFillColor(colors.HexColor("#666666")); c.setFont("Nanum",6.2); c.drawCentredString(x+w/2,y+6*mm,"SOURCE - PLIX 원본 Category Idea")


def draw_source_category_sheet(c):
    pw,ph=landscape(A4); c.setPageSize((pw,ph))
    card_h=99*mm; card_w=card_h*(198/306)
    x0,y0=draw_cut_grid(c,pw,ph,card_w,card_h)
    for i,(_,_,left_ko,right_ko) in enumerate(CATEGORIES):
        row=i//4; col=i%4; x=x0+col*card_w; y=y0+(1-row)*card_h
        draw_source_category_card(c,x,y,card_w,card_h,left_ko,right_ko,custom=(i==7))
    c.setFont("Nanum",6.5); c.setFillColor(colors.HexColor("#666666"))
    c.drawCentredString(pw/2,2.3*mm,"Category Idea 8장 - SOURCE 카테고리 한국어화 / 8번은 X / X가 아님 직접 작성형")
    c.showPage()

def draw_direct_category_sheet(c):
    pw,ph=landscape(A4); c.setPageSize((pw,ph))
    card_h=99*mm; card_w=card_h*(198/306)
    x0,y0=draw_cut_grid(c,pw,ph,card_w,card_h)
    for i in range(8):
        row=i//4; col=i%4; x=x0+col*card_w; y=y0+(1-row)*card_h
        draw_custom_category_card(c,x,y,card_w,card_h,freeform=(i>=4),serial=i+1)
    c.setFont("Nanum",6.5); c.setFillColor(colors.HexColor("#666666"))
    c.drawCentredString(pw/2,2.3*mm,"직접 작성 카드 8장: PROJECT DEFAULT 추가 - 원본형 4장 + 자유형 4장")
    c.showPage()


def draw_cover(c):
    pw,ph=portrait(A4); c.setPageSize((pw,ph)); m=18*mm
    c.setFillColor(colors.black); c.setFont("NanumBold",26); c.drawString(m,ph-35*mm,"동물고리즘")
    c.setFont("NanumBold",15); c.drawString(m,ph-47*mm,"Animal-gorithm Original KO - 인쇄 프로토타입")
    c.setFont("Nanum",10); c.setFillColor(colors.HexColor("#555555")); c.drawString(m,ph-57*mm,"PLIX 원작의 핵심 구조를 유지한 한국어 플레이테스트용 세트")
    c.setStrokeColor(colors.black); c.setLineWidth(1); c.line(m,ph-64*mm,pw-m,ph-64*mm)
    c.setFillColor(colors.black); c.setFont("NanumBold",12); c.drawString(m,ph-79*mm,"세트 구성")
    items=[
        "동물 카드 56장: 이름 있는 원본 46장 + 빈 동물 카드 10장",
        "Category Idea 8장: PLIX 원본 카테고리의 한국어판",
        "직접 작성 Category 8장: PROJECT DEFAULT 추가(원본형 4장 + 자유형 4장)",
        "LEFT / NEXT / RIGHT 플레이 영역: A3 기본 + A4 컴팩트 대체판",
        "상세 규칙 2쪽 + 플레이테스트 기록지 1쪽",
    ]
    y=ph-90*mm; c.setFont("Nanum",10)
    for t in items:
        c.drawString(m+4*mm,y,"• "+t); y-=8*mm
    c.setFont("NanumBold",12); c.drawString(m,y-4*mm,"인쇄")
    y-=14*mm; c.setFont("Nanum",9.5)
    lines=[
        "카드 시트: A4 가로 / 실제 크기 100% 권장. 점선에 맞춰 재단합니다.",
        "A3 플레이 영역: A3 가로 100% 권장. A3가 없으면 뒤의 A4 컴팩트판을 사용합니다.",
        "PROPOSAL: 반복 사용 시 두꺼운 용지 또는 슬리브를 사용하면 손글씨 카드 재사용이 쉽습니다.",
    ]
    for t in lines:
        c.drawString(m+4*mm,y,"• "+t); y-=7*mm
    c.setFont("NanumBold",12); c.drawString(m,y-3*mm,"표기")
    y-=13*mm; c.setFont("Nanum",9.3)
    for tag,desc in [("SOURCE","PLIX 원본에서 직접 확인"),("PROJECT DEFAULT","실제 플레이를 위해 프로젝트가 정한 운영값")]:
        c.setFont("NanumBold",9.3); c.drawString(m+4*mm,y,tag)
        c.setFont("Nanum",9.3); c.drawString(m+39*mm,y,desc); y-=7*mm
    c.setFont("Nanum",8); c.setFillColor(colors.HexColor("#666666"))
    note="원본 동물 이미지/레이아웃을 외부 배포 또는 판매에 쓰기 전에는 해당 PLIX 자료의 개별 라이선스 범위를 다시 확인합니다."
    c.drawString(m,18*mm,note)
    c.showPage()


def draw_playmat(c, compact=False):
    if compact:
        pw,ph=landscape(A4); title="A4 컴팩트 플레이 영역"
    else:
        pw,ph=landscape(A3); title="A3 기본 플레이 영역"
    c.setPageSize((pw,ph)); margin=12*mm
    c.setFont("NanumBold",15); c.drawString(margin,ph-11*mm,title)
    c.setFont("Nanum",7.5); c.setFillColor(colors.HexColor("#555555")); c.drawRightString(pw-margin,ph-10.5*mm,"PROJECT DEFAULT: NEXT 영역 포함")
    usable_w=pw-2*margin; top=ph-20*mm; bottom=12*mm; usable_h=top-bottom
    next_w=(72*mm if not compact else 63*mm)
    side_w=(usable_w-next_w)/2
    zones=[(margin,bottom,side_w,usable_h,"LEFT","왼쪽 그룹"),(margin+side_w,bottom,next_w,usable_h,"NEXT","다음에 시험할 카드"),(margin+side_w+next_w,bottom,side_w,usable_h,"RIGHT","오른쪽 그룹")]
    for x,y,w,h,en,ko in zones:
        c.setFillColor(colors.white); c.setStrokeColor(colors.black); c.setLineWidth(1.4); c.roundRect(x,y,w,h,4*mm,stroke=1,fill=1)
        c.setFillColor(colors.black); c.setFont("NanumBold",22 if not compact else 18); c.drawCentredString(x+w/2,y+h-16*mm,en)
        c.setFont("NanumBold",11 if not compact else 9); c.drawCentredString(x+w/2,y+h-25*mm,ko)
    # NEXT card footprint
    nx,ny,nw,nh=zones[1][0],zones[1][1],zones[1][2],zones[1][3]
    fpw=(64*mm if not compact else 48*mm); fph=99/64*fpw
    fx=nx+(nw-fpw)/2; fy=ny+(nh-fph)/2-5*mm
    c.setStrokeColor(colors.HexColor("#777777")); c.setDash(4,3); c.rect(fx,fy,fpw,fph,stroke=1,fill=0); c.setDash()
    c.setFont("Nanum",8); c.setFillColor(colors.HexColor("#777777")); c.drawCentredString(nx+nw/2,fy+fph/2,"선택한 새 동물 카드를 먼저 이곳에 둡니다")
    # arrows
    c.setStrokeColor(colors.black); c.setFillColor(colors.black); c.setLineWidth(2)
    cy=bottom+usable_h*0.46
    c.line(nx-8*mm,cy,nx-2*mm,cy); c.line(nx-8*mm,cy,nx-5*mm,cy+2*mm); c.line(nx-8*mm,cy,nx-5*mm,cy-2*mm)
    rx=nx+nw
    c.line(rx+2*mm,cy,rx+8*mm,cy); c.line(rx+8*mm,cy,rx+5*mm,cy+2*mm); c.line(rx+8*mm,cy,rx+5*mm,cy-2*mm)
    c.setFillColor(colors.HexColor("#555555")); c.setFont("Nanum",7)
    c.drawCentredString(pw/2,4*mm,"예측이 끝난 뒤 Decider가 NEXT 카드를 LEFT 또는 RIGHT로 이동합니다.")
    c.showPage()


def draw_paragraph(c, text, x, y, width, font="Nanum", size=9.2, leading=13, bullet=None):
    # Simple Korean/space-aware line wrapping using string width.
    words=text.split(" ")
    lines=[]; cur=""
    for w in words:
        trial=(cur+" "+w).strip()
        if pdfmetrics.stringWidth(trial,font,size) <= width:
            cur=trial
        else:
            if cur: lines.append(cur)
            cur=w
    if cur: lines.append(cur)
    if bullet and lines:
        lines[0]=bullet+lines[0]
    c.setFont(font,size); c.setFillColor(colors.black)
    for line in lines:
        c.drawString(x,y,line); y-=leading
    return y


def draw_rules(c):
    pw,ph=portrait(A4); m=17*mm; colw=pw-2*m
    # Page 1
    c.setPageSize((pw,ph)); y=ph-20*mm
    c.setFont("NanumBold",20); c.drawString(m,y,"상세 규칙 1/2 - 준비와 한 차례")
    y-=12*mm
    c.setFont("NanumBold",11); c.drawString(m,y,"게임 목표  [SOURCE]"); y-=7*mm
    y=draw_paragraph(c,"LEFT의 공통점, RIGHT의 공통점, 두 그룹의 차이를 관찰해 Decider가 정한 비밀 카테고리 한 쌍을 알아냅니다.",m,y,colw)
    y-=4*mm; c.setFont("NanumBold",11); c.drawString(m,y,"준비"); y-=7*mm
    steps=[
        ("[PROJECT DEFAULT] LEFT / NEXT / RIGHT 플레이 영역을 중앙에 놓습니다.",),
        ("[PROJECT DEFAULT] 동물 카드를 모두 볼 수 있게 펼칩니다.",),
        ("한 명이 Decider가 됩니다. [SOURCE]",),
        ("Decider는 Category Idea 카드 1장을 고르거나 직접 카테고리를 작성합니다. 다른 플레이어에게는 비밀로 합니다. [SOURCE + PROJECT DEFAULT 보관 방식]",),
        ("[PROJECT DEFAULT] 시작 예시 동물 3장을 LEFT / RIGHT에 놓습니다. 양쪽에 최소 1장씩 둡니다.",),
    ]
    for i,(t,) in enumerate(steps,1):
        y=draw_paragraph(c,t,m+4*mm,y,colw-4*mm,size=9,leading=12,bullet=f"{i}. "); y-=2*mm
    y-=2*mm; c.setFont("NanumBold",11); c.drawString(m,y,"한 차례 - 둘 중 하나를 선택"); y-=8*mm
    c.setFont("NanumBold",10); c.drawString(m+4*mm,y,"A. 비밀 카테고리 추측"); y-=6*mm
    y=draw_paragraph(c,"LEFT와 RIGHT의 기준을 한 쌍으로 말합니다. 정확히 맞히면 라운드가 끝납니다. [SOURCE]",m+8*mm,y,colw-8*mm,size=9)
    y=draw_paragraph(c,"[PROJECT DEFAULT] 오답 페널티와 부분 힌트는 없습니다. Decider는 ‘정답’ 또는 ‘아직 정답이 아님’ 정도만 말합니다.",m+8*mm,y,colw-8*mm,size=9)
    y-=3*mm; c.setFont("NanumBold",10); c.drawString(m+4*mm,y,"B. 새 동물 시험"); y-=6*mm
    trial=["아직 분류되지 않은 동물 1장을 고릅니다.","[PROJECT DEFAULT] 그 카드를 먼저 NEXT에 둡니다.","Decider가 움직이기 전에 플레이어들이 LEFT / RIGHT를 예측합니다. [SOURCE]","예측 후 Decider가 실제 위치로 이동합니다.","새 결과를 보고 가설을 수정하고 다음 플레이어 차례로 넘어갑니다."]
    for i,t in enumerate(trial,1):
        y=draw_paragraph(c,t,m+8*mm,y,colw-8*mm,size=9,leading=12,bullet=f"{i}. "); y-=1.5*mm
    c.setFont("Nanum",7); c.setFillColor(colors.HexColor("#666666")); c.drawCentredString(pw/2,8*mm,"Original KO - SOURCE와 PROJECT DEFAULT를 구분해 표시")
    c.showPage()

    # Page 2
    c.setPageSize((pw,ph)); y=ph-20*mm
    c.setFont("NanumBold",20); c.drawString(m,y,"상세 규칙 2/2 - 정보 관리와 종료")
    y-=12*mm
    sections=[
        ("직접 질문", ["플레이어가 ‘포유류예요?’, ‘날개가 있으면 LEFT예요?’처럼 직접 예/아니오 질문을 해도 Decider는 답하지 않습니다. [PROJECT DEFAULT]", "대신 ‘확인하고 싶은 동물 카드를 골라 시험해 보세요.’라고 안내합니다."]),
        ("Decider 주의사항", ["비밀 카테고리를 보이지 않게 하고, 첫 동물 배치 전에 확정하며 라운드 중 바꾸지 않습니다. [PROJECT DEFAULT]", "특정 동물만 예외로 만들지 않습니다.", "예측이 끝난 뒤 카드를 이동합니다.", "표정, 시선, 손짓, 망설임, ‘거의 맞았어’ 같은 말이 힌트가 되지 않게 합니다. [PROJECT DEFAULT]"]),
        ("직접 작성 카테고리", ["원본형은 X / X가 아님 구조입니다. [SOURCE]", "추가 자유 작성형은 LEFT와 RIGHT를 각각 적습니다. [PROJECT DEFAULT]", "두 범주가 겹치지 않고, 사용할 동물이 어느 쪽에도 속하지 않는 일이 없도록 작성합니다. 게임 중 수정하지 않습니다. [PROJECT DEFAULT]"]),
        ("애매한 판정", ["Colorful, Eats bugs처럼 해석 차이가 생길 수 있습니다. 원작 카드이므로 Original KO에서는 삭제하지 않습니다. [SOURCE]", "Decider는 가능하면 라운드 전에 판정을 정하고, 논쟁이 생겨도 그 라운드에서는 기존 판정을 유지합니다. 라운드 후 기록합니다. [PROJECT DEFAULT]"]),
        ("라운드 종료", ["비밀 카테고리 한 쌍을 정확히 맞히면 끝납니다. [SOURCE]", "의미가 같으면 정답으로 인정하고 점수는 사용하지 않습니다. 다음 Decider는 시계 방향입니다. [PROJECT DEFAULT]"]),
    ]
    for title,bullets in sections:
        c.setFont("NanumBold",11); c.setFillColor(colors.black); c.drawString(m,y,title); y-=6.5*mm
        for t in bullets:
            y=draw_paragraph(c,t,m+4*mm,y,colw-4*mm,size=8.9,leading=12,bullet="• "); y-=1.5*mm
        y-=2.5*mm
    c.setFont("NanumBold",10); c.drawString(m,y,"핵심 사고 루프  [SOURCE의 학습 의도에 맞춘 정리]"); y-=7*mm
    c.setFont("Nanum",9); c.drawString(m+4*mm,y,"데이터 관찰 → 공통점/차이 발견 → 가설 생성 → 새 동물 선택 → 위치 예측 → 결과 확인 → 가설 수정")
    c.setFont("Nanum",7); c.setFillColor(colors.HexColor("#666666")); c.drawCentredString(pw/2,8*mm,"원작을 단순한 True/False 단일 규칙 게임으로 축소하지 않습니다.")
    c.showPage()


def draw_checklist(c):
    pw,ph=portrait(A4); m=15*mm; c.setPageSize((pw,ph)); y=ph-18*mm
    c.setFont("NanumBold",18); c.drawString(m,y,"Original KO 플레이테스트 기록지"); y-=10*mm
    c.setFont("Nanum",8.5)
    meta=["날짜: ____________________   학년: ______   인원: ______   라운드: ______", "Decider: __________________________   사용 카테고리: ______________________________"]
    for t in meta: c.drawString(m,y,t); y-=7*mm
    blocks=[
        ("비밀정보 관리",["Decider 외에는 비밀 카테고리를 보지 못했음","카테고리를 시작 전에 확정했고 라운드 중 바꾸지 않았음","표정/말/손짓/망설임이 힌트가 되지 않았음"]),
        ("규칙 이해",["LEFT / RIGHT 두 그룹을 이해함","새 카드가 분류되기 전에 먼저 예측함","카테고리 추측과 새 카드 시험을 구분함","직접 예/아니오 질문 대신 카드를 통해 확인함"]),
        ("추론 행동",["양쪽의 공통점과 차이를 비교함","새 데이터 후 가설을 수정함","정보 가치가 큰 동물을 선택하려고 함","비슷한 카드만 반복해서 고르지 않음"]),
        ("카테고리 문제",["양쪽에 동시에 들어가는 동물이 없었음","어느 쪽에도 들어가지 않는 동물이 없었음","주관성 때문에 진행이 막히지 않았음"]),
    ]
    for title,items in blocks:
        c.setFont("NanumBold",10.5); c.drawString(m,y,title); y-=6*mm
        c.setFont("Nanum",8.5)
        for t in items: c.drawString(m+4*mm,y,"□ "+t); y-=5.5*mm
        y-=2*mm
    c.setFont("NanumBold",10); c.drawString(m,y,"기록"); y-=6*mm
    fields=["애매했던 동물/판정","가장 유용했던 추가 카드","최초 가설","가설을 바꾸게 한 카드","최종 정답까지 추가된 카드 수","라운드 시간"]
    for f in fields:
        c.setFont("Nanum",8.5); c.drawString(m,y,f+":"); c.line(m+42*mm,y-1,pw-m,y-1); y-=7.5*mm
    c.setFont("NanumBold",9.5); c.drawString(m,y,"수정 우선순위"); y-=6*mm
    for t in ["P0 진행 불가:","P1 원작 구조/학습 문제:","P2 한국어 표현/운영 문제:","P3 개선판 후보 아이디어:"]:
        c.setFont("Nanum",8.5); c.drawString(m,y,t); c.line(m+37*mm,y-1,pw-m,y-1); y-=7*mm
    c.showPage()


def build(deck_pdf: Path, out_pdf: Path):
    pdfmetrics.registerFont(TTFont("Nanum", FONT_REG))
    pdfmetrics.registerFont(TTFont("NanumBold", FONT_BOLD))

    doc=fitz.open(deck_pdf)
    page_imgs=[]
    scale=300/72
    for pno in range(8):
        pix=doc[pno].get_pixmap(matrix=fitz.Matrix(scale,scale), alpha=False)
        page_imgs.append(Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB"))

    animal_by_pos={(p,s):(en,ko) for p,s,en,ko in ANIMALS}
    localized_pages=[]
    for p in range(1,8):
        cards=[]
        # visual row-major positions = slots 1,3,5,7 / 2,4,6,8
        slots=[1,3,5,7,2,4,6,8]
        for s in slots:
            crop=card_crop(page_imgs[p-1],s)
            if (p,s) in animal_by_pos:
                en,ko=animal_by_pos[(p,s)]
                crop=localize_animal_card(crop,ko,en)
            cards.append(crop)
        localized_pages.append(cards)

    out_pdf.parent.mkdir(parents=True,exist_ok=True)
    c=canvas.Canvas(str(out_pdf), pagesize=A4)
    c.setTitle("Animal-gorithm Original KO Printable Prototype")
    c.setAuthor("Animal-gorithm Original KO project / based on PLIX source materials")

    draw_cover(c)
    for n,cards in enumerate(localized_pages,1):
        draw_card_sheet(c,cards,f"동물 카드 시트 {n}/7 - PLIX 원본 그림 유지 / 한국어 이름 우선 + 영문 소형 병기")
    draw_source_category_sheet(c)
    draw_direct_category_sheet(c)
    draw_playmat(c,compact=False)
    draw_playmat(c,compact=True)
    draw_rules(c)
    draw_checklist(c)
    c.save()


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--deck-pdf",required=True,type=Path)
    ap.add_argument("--out",required=True,type=Path)
    ap.add_argument("--data-dir",type=Path,default=Path(__file__).resolve().parent.parent / "data")
    args=ap.parse_args()
    load_project_data(args.data_dir)
    build(args.deck_pdf,args.out)

if __name__=="__main__":
    main()
