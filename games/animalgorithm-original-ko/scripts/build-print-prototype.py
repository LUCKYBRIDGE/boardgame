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
        raise ValueError(f"Expected 8 분류 기준 카드 pairs, got {len(CATEGORIES)}")

# Source slot order is column-major on each PLIX sheet:
# 1=col1/top, 2=col1/bottom, 3=col2/top, ...
def slot_to_col_row(slot: int) -> tuple[int, int]:
    return (slot - 1) // 2, (slot - 1) % 2


def fit_font(text: str, font_path: str, start: int, min_size: int, max_width: float) -> ImageFont.FreeTypeFont:
    size = start
    while size >= min_size:
        f = ImageFont.truetype(font_path, size=size)
        box = f.getbbox(text)
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
        widths = [(f.getbbox(t)[2]-f.getbbox(t)[0]) for t in (a,b)]
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
        c.setFont("NanumBold",9); c.drawCentredString(x+w/4,y+h-29*mm,"왼쪽 기준")
        c.drawCentredString(x+3*w/4,y+h-29*mm,"오른쪽 기준")
        for xx in [x+4*mm,x+w/2+4*mm]:
            c.roundRect(xx,y+27*mm,w/2-8*mm,29*mm,2*mm,stroke=1,fill=0)
        c.setFont("Nanum",6.5); c.setFillColor(colors.HexColor("#666666")); c.drawCentredString(x+w/2,y+7*mm,"프로젝트 기본 - 자유 작성형")
    else:
        c.setFont("NanumBold",9); c.drawCentredString(x+w/4,y+h-29*mm,"기준 X")
        c.drawCentredString(x+3*w/4,y+h-29*mm,"X가 아님")
        c.roundRect(x+5*mm,y+29*mm,w/2-10*mm,28*mm,2*mm,stroke=1,fill=0)
        c.setFont("Nanum",7.2); c.setFillColor(colors.HexColor("#666666")); c.drawCentredString(x+3*w/4,y+44*mm,"왼쪽에 쓴 기준의 반대")
        c.drawCentredString(x+w/2,y+7*mm,"프로젝트 기본 - 원본형 추가 사본")



def draw_source_category_card(c, x,y,w,h, left_ko, right_ko, custom=False):
    c.setStrokeColor(colors.black); c.setFillColor(colors.white); c.rect(x,y,w,h,stroke=1,fill=1)
    c.setFillColor(colors.HexColor("#555555")); c.setFont("Nanum",6.2)
    c.drawString(x+4*mm,y+h-7.5*mm,"PLIX 분류 기준 카드 - 한국어판")
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
    c.setFillColor(colors.HexColor("#666666")); c.setFont("Nanum",6.2); c.drawCentredString(x+w/2,y+6*mm,"SOURCE - PLIX 원본 분류 기준 카드")


def draw_source_category_sheet(c):
    pw,ph=landscape(A4); c.setPageSize((pw,ph))
    card_h=99*mm; card_w=card_h*(198/306)
    x0,y0=draw_cut_grid(c,pw,ph,card_w,card_h)
    for i,(_,_,left_ko,right_ko) in enumerate(CATEGORIES):
        row=i//4; col=i%4; x=x0+col*card_w; y=y0+(1-row)*card_h
        draw_source_category_card(c,x,y,card_w,card_h,left_ko,right_ko,custom=(i==7))
    c.setFont("Nanum",6.5); c.setFillColor(colors.HexColor("#666666"))
    c.drawCentredString(pw/2,2.3*mm,"분류 기준 카드 8장 - SOURCE 카테고리 한국어화 / 8번은 X / X가 아님 직접 작성형")
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
    c.setFont("NanumBold",15); c.drawString(m,ph-47*mm,"Animal-gorithm Original KO - 한국어 인쇄 프로토타입")
    c.setFont("Nanum",10); c.setFillColor(colors.HexColor("#555555")); c.drawString(m,ph-57*mm,"PLIX 원작의 핵심 플레이 구조를 유지한 한국어 플레이테스트용 세트")
    c.setStrokeColor(colors.black); c.setLineWidth(1); c.line(m,ph-64*mm,pw-m,ph-64*mm)
    c.setFillColor(colors.black); c.setFont("NanumBold",12); c.drawString(m,ph-79*mm,"세트 구성")
    items=[
        "동물 카드 56장: 이름 있는 원본 46장 + 빈 동물 카드 10장",
        "분류 기준 카드 8장: PLIX 원본 분류 기준의 한국어판",
        "직접 작성 분류 기준 카드 8장: 프로젝트 기본 추가(원본형 4장 + 자유형 4장)",
        "왼쪽 / 다음 카드 / 오른쪽 플레이 영역: A4 가로 1장",
        "상세 규칙 3쪽 + 플레이테스트 기록지 1쪽",
    ]
    y=ph-90*mm; c.setFont("Nanum",10)
    for t in items:
        c.drawString(m+4*mm,y,"• "+t); y-=8*mm
    c.setFont("NanumBold",12); c.drawString(m,y-4*mm,"인쇄")
    y-=14*mm
    for t in [
        "전체 프로토타입은 A4를 기준으로 제작합니다. 카드 시트와 플레이 영역은 A4 가로, 규칙/기록지는 A4 세로입니다.",
        "카드 시트는 실제 크기 100%로 인쇄하고 카드 경계에 맞춰 재단합니다.",
        "더 큰 플레이 영역이 필요하면 A4 플레이 영역만 A3로 확대 복사합니다(약 141%).",
    ]:
        y=draw_paragraph(c,t,m+4*mm,y,pw-2*m-4*mm,size=9.2,leading=13,bullet="• "); y-=2*mm
    c.setFont("NanumBold",12); c.drawString(m,y-2*mm,"4명이 할 때 핵심")
    y-=12*mm
    for t in [
        "1명은 결정자, 나머지 3명은 추리 플레이어가 됩니다.",
        "추리 플레이어의 개인 차례는 시계 방향으로 돌지만 새 동물 위치 예측은 3명 모두 동시에 참여합니다.",
        "결정자는 개인 행동 차례 없이 비밀 기준을 관리하고 결과를 판정합니다.",
    ]:
        y=draw_paragraph(c,t,m+4*mm,y,pw-2*m-4*mm,size=9,leading=12,bullet="• "); y-=1.5*mm
    c.setFont("NanumBold",12); c.drawString(m,y-2*mm,"표기")
    y-=12*mm
    for tag,desc in [("원작(SOURCE)","PLIX 원본에서 직접 확인"),("프로젝트 기본(PROJECT DEFAULT)","원작이 정하지 않은 실제 운영 보완")]:
        c.setFont("NanumBold",8.8); c.drawString(m+4*mm,y,tag)
        c.setFont("Nanum",8.8); c.drawString(m+62*mm,y,desc); y-=7*mm
    c.setFont("Nanum",7); c.setFillColor(colors.HexColor("#666666"))
    c.drawString(m,18*mm,"원본 동물 이미지/카드 디자인을 외부 배포 또는 판매에 쓰기 전에는 PLIX 자료의 개별 라이선스를 다시 확인합니다.")
    c.showPage()

def draw_playmat(c):
    pw,ph=landscape(A4); c.setPageSize((pw,ph)); margin=10*mm
    c.setFont("NanumBold",15); c.setFillColor(colors.black); c.drawString(margin,ph-10*mm,"A4 플레이 영역")
    c.setFont("Nanum",7.3); c.setFillColor(colors.HexColor("#555555")); c.drawRightString(pw-margin,ph-9.5*mm,"프로젝트 기본(PROJECT DEFAULT): 다음 카드 영역 포함")
    top=ph-18*mm; bottom=11*mm; usable_h=top-bottom; usable_w=pw-2*margin
    next_w=72*mm; side_w=(usable_w-next_w)/2
    zones=[
        (margin,bottom,side_w,usable_h,"왼쪽","분류된 왼쪽 그룹"),
        (margin+side_w,bottom,next_w,usable_h,"다음 카드","지금 시험할 카드"),
        (margin+side_w+next_w,bottom,side_w,usable_h,"오른쪽","분류된 오른쪽 그룹"),
    ]
    for x,y,w,h,title,sub in zones:
        c.setFillColor(colors.white); c.setStrokeColor(colors.black); c.setLineWidth(1.35); c.roundRect(x,y,w,h,4*mm,stroke=1,fill=1)
        c.setFillColor(colors.black); c.setFont("NanumBold",18); c.drawCentredString(x+w/2,y+h-15*mm,title)
        c.setFont("NanumBold",8.7); c.drawCentredString(x+w/2,y+h-23*mm,sub)
    nx,ny,nw,nh=zones[1][0],zones[1][1],zones[1][2],zones[1][3]
    fpw=64*mm; fph=99*mm; fx=nx+(nw-fpw)/2; fy=ny+(nh-fph)/2-3*mm
    c.setStrokeColor(colors.HexColor("#777777")); c.setDash(4,3); c.rect(fx,fy,fpw,fph,stroke=1,fill=0); c.setDash()
    c.setFont("Nanum",7.4); c.setFillColor(colors.HexColor("#777777")); c.drawCentredString(nx+nw/2,fy+fph/2,"선택한 새 동물 카드를 먼저 이곳에 둡니다")
    c.setStrokeColor(colors.black); c.setLineWidth(1.8); cy=bottom+usable_h*0.43
    c.line(nx-7*mm,cy,nx-2*mm,cy); c.line(nx-7*mm,cy,nx-4.5*mm,cy+2*mm); c.line(nx-7*mm,cy,nx-4.5*mm,cy-2*mm)
    rx=nx+nw
    c.line(rx+2*mm,cy,rx+7*mm,cy); c.line(rx+7*mm,cy,rx+4.5*mm,cy+2*mm); c.line(rx+7*mm,cy,rx+4.5*mm,cy-2*mm)
    c.setFont("Nanum",7); c.setFillColor(colors.HexColor("#555555"))
    c.drawCentredString(pw/2,3.5*mm,"모두가 위치를 예측한 뒤 결정자가 다음 카드를 왼쪽 또는 오른쪽으로 이동합니다. 필요하면 이 페이지를 A3로 약 141% 확대 복사하세요.")
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
    pw,ph=portrait(A4); m=16*mm; colw=pw-2*m

    c.setPageSize((pw,ph)); y=ph-18*mm
    c.setFont("NanumBold",19); c.drawString(m,y,"상세 규칙 1/3 - 역할과 차례"); y-=11*mm
    c.setFont("NanumBold",11); c.drawString(m,y,"4명이 할 때  [프로젝트 기본(PROJECT DEFAULT)]"); y-=7*mm
    y=draw_paragraph(c,"원작은 1명의 결정자와 나머지 플레이어가 추리하는 구조를 제시하지만, 개인 차례 순서와 동시 행동 범위는 세부적으로 정하지 않습니다. 아래 방식은 실제 수업과 플레이를 위한 프로젝트 기본 운영입니다.",m,y,colw,size=8.9,leading=12); y-=4*mm
    c.setFont("NanumBold",10.5); c.drawString(m,y,"역할 분배"); y-=7*mm
    for t in [
        "결정자 1명: 비밀 분류 기준을 정하고 시작 동물 3장을 배치하며 각 시험의 실제 위치와 정답 여부를 판정합니다. 결정자에게는 별도의 개인 행동 차례가 없습니다.",
        "추리 플레이어 3명: 결정자의 왼쪽에 앉은 사람부터 시계 방향으로 A → B → C → A 순서로 개인 차례를 반복합니다.",
    ]:
        y=draw_paragraph(c,t,m+4*mm,y,colw-4*mm,size=8.9,leading=12,bullet="• "); y-=2.5*mm
    c.setFont("NanumBold",10.5); c.drawString(m,y,"개인 차례와 함께 하는 활동"); y-=7*mm
    turns=[
        "개인 차례: 현재 차례의 추리 플레이어 1명이 비밀 분류 기준 추측 또는 새 동물 시험 중 하나를 선택합니다.",
        "비밀 분류 기준 추측: 현재 차례 플레이어만 공식 추측을 말합니다. 틀리면 결정자가 아직 정답이 아님 정도만 알려 주고 다음 추리 플레이어 차례로 넘어갑니다.",
        "새 동물 시험: 현재 차례 플레이어가 시험할 동물 1장을 골라 다음 카드에 놓습니다.",
        "동시 예측: 새 동물이 선택되면 추리 플레이어 3명 모두가 결과를 보기 전에 각자 왼쪽/오른쪽을 동시에 예측합니다.",
        "결과 공개: 3명의 예측이 끝나면 결정자가 카드를 실제 위치로 옮깁니다. 모두가 결과를 보고 가설을 고친 뒤 다음 사람 차례로 넘어갑니다.",
    ]
    for i,t in enumerate(turns,1):
        y=draw_paragraph(c,t,m+4*mm,y,colw-4*mm,size=8.7,leading=11.6,bullet=f"{i}. "); y-=2*mm
    c.setFont("NanumBold",10.5); c.drawString(m,y,"4인 진행 예시"); y-=7*mm
    ex=[
        "결정자 D가 비밀 기준과 시작 카드 3장을 준비합니다.",
        "A 차례: A가 새 동물 박쥐를 선택 → A·B·C가 동시에 왼쪽/오른쪽 예측 → D가 실제 위치 공개.",
        "B 차례: B가 비밀 기준을 한 쌍으로 추측 → 오답이면 D는 정답 여부만 말함.",
        "C 차례: C가 새 동물을 선택 → A·B·C 모두 동시에 위치 예측 → D가 공개.",
        "그 다음 다시 A 차례. 누군가 정확한 비밀 기준을 맞히면 즉시 라운드 종료.",
    ]
    for i,t in enumerate(ex,1):
        y=draw_paragraph(c,t,m+4*mm,y,colw-4*mm,size=8.6,leading=11.2,bullet=f"{i}. "); y-=1.4*mm
    c.setFont("Nanum",7); c.setFillColor(colors.HexColor("#666666")); c.drawCentredString(pw/2,8*mm,"핵심: 행동 선택은 개인 차례, 새 카드 위치 예측은 추리 플레이어 모두가 동시에 참여")
    c.showPage()

    c.setPageSize((pw,ph)); y=ph-18*mm
    c.setFont("NanumBold",19); c.drawString(m,y,"상세 규칙 2/3 - 준비와 한 차례"); y-=11*mm
    c.setFont("NanumBold",11); c.drawString(m,y,"게임 목표  [원작(SOURCE)]"); y-=7*mm
    y=draw_paragraph(c,"왼쪽의 공통점, 오른쪽의 공통점, 두 그룹의 차이를 관찰해 결정자가 정한 비밀 분류 기준 한 쌍을 알아냅니다.",m,y,colw,size=9,leading=12); y-=4*mm
    c.setFont("NanumBold",11); c.drawString(m,y,"준비"); y-=7*mm
    steps=[
        "[프로젝트 기본(PROJECT DEFAULT)] A4 왼쪽 / 다음 카드 / 오른쪽 플레이 영역을 중앙에 놓습니다.",
        "[프로젝트 기본(PROJECT DEFAULT)] 동물 카드를 모두 볼 수 있게 펼칩니다.",
        "한 명이 결정자가 됩니다. [원작(SOURCE)]",
        "결정자는 분류 기준 카드 1장을 고르거나 직접 분류 기준을 작성합니다. 다른 플레이어에게는 비밀로 합니다.",
        "[프로젝트 기본(PROJECT DEFAULT)] 시작 예시 동물 3장을 왼쪽 / 오른쪽에 놓습니다. 양쪽에 최소 1장씩 둡니다.",
        "[프로젝트 기본(PROJECT DEFAULT)] 결정자의 왼쪽 추리 플레이어부터 첫 개인 차례를 시작합니다.",
    ]
    for i,t in enumerate(steps,1):
        y=draw_paragraph(c,t,m+4*mm,y,colw-4*mm,size=8.7,leading=11.5,bullet=f"{i}. "); y-=1.7*mm
    c.setFont("NanumBold",11); c.drawString(m,y,"현재 차례 플레이어는 둘 중 하나를 선택"); y-=8*mm
    c.setFont("NanumBold",10); c.drawString(m+4*mm,y,"A. 비밀 분류 기준 추측"); y-=6*mm
    y=draw_paragraph(c,"현재 차례 플레이어가 왼쪽과 오른쪽의 기준을 한 쌍으로 말합니다. 정확히 맞히면 라운드가 끝납니다.",m+8*mm,y,colw-8*mm,size=8.8,leading=11.5); y-=2*mm
    y=draw_paragraph(c,"오답 페널티와 부분 힌트는 없습니다. 결정자는 정답 또는 아직 정답이 아님 정도만 말합니다. [프로젝트 기본]",m+8*mm,y,colw-8*mm,size=8.8,leading=11.5); y-=4*mm
    c.setFont("NanumBold",10); c.drawString(m+4*mm,y,"B. 새 동물 시험"); y-=6*mm
    trial=[
        "현재 차례 플레이어가 아직 분류되지 않은 동물 1장을 고릅니다.",
        "그 카드를 먼저 다음 카드 영역에 둡니다. [프로젝트 기본]",
        "추리 플레이어 모두가 결과를 보기 전에 왼쪽 / 오른쪽을 동시에 예측합니다. [동시 공개 방식은 프로젝트 기본]",
        "모든 예측이 끝난 뒤 결정자가 실제 위치로 이동합니다.",
        "모두가 새 결과를 보고 가설을 수정한 뒤 다음 추리 플레이어 차례로 넘어갑니다.",
    ]
    for i,t in enumerate(trial,1):
        y=draw_paragraph(c,t,m+8*mm,y,colw-8*mm,size=8.8,leading=11.5,bullet=f"{i}. "); y-=1.5*mm
    c.setFont("Nanum",7); c.setFillColor(colors.HexColor("#666666")); c.drawCentredString(pw/2,8*mm,"관찰과 추론은 모두가 계속하지만 공식 행동 선택은 현재 차례 플레이어가 합니다.")
    c.showPage()

    c.setPageSize((pw,ph)); y=ph-18*mm
    c.setFont("NanumBold",19); c.drawString(m,y,"상세 규칙 3/3 - 정보 관리와 라운드 종료"); y-=11*mm
    sections=[
        ("직접 질문",["플레이어가 포유류예요?, 날개가 있으면 왼쪽이에요?처럼 직접 예/아니오 질문을 해도 결정자는 답하지 않습니다. [프로젝트 기본]","대신 확인하고 싶은 동물 카드를 골라 시험해 보세요.라고 안내합니다."]),
        ("결정자 주의사항",["비밀 분류 기준을 보이지 않게 하고 첫 동물 배치 전에 확정하며 라운드 중 바꾸지 않습니다. [프로젝트 기본]","특정 동물만 예외로 만들지 않습니다.","새 카드 위치를 공개하기 전에 추리 플레이어 모두의 예측이 끝났는지 확인합니다.","표정, 시선, 손짓, 망설임 같은 말과 행동이 힌트가 되지 않게 합니다. [프로젝트 기본]"]),
        ("직접 작성 분류 기준",["원본형은 X / X가 아님 구조입니다. [원작(SOURCE)]","추가 자유 작성형은 왼쪽과 오른쪽 기준을 각각 적습니다. [프로젝트 기본]","두 범주가 겹치지 않고 사용할 동물이 어느 쪽에도 속하지 않는 일이 없도록 작성하며 게임 중 수정하지 않습니다."]),
        ("애매한 판정",["색이 화려함, 곤충을 먹음처럼 해석 차이가 생길 수 있습니다. 원작 카드이므로 Original KO에서는 삭제하지 않습니다. [원작(SOURCE)]","결정자는 가능하면 라운드 전에 판정을 정하고 그 라운드에서는 기존 판정을 유지합니다. 라운드 후 기록합니다. [프로젝트 기본]"]),
        ("라운드 종료와 다음 라운드",["비밀 분류 기준 한 쌍을 정확히 맞히면 즉시 끝납니다. [원작(SOURCE)]","의미가 같으면 정답으로 인정하고 점수는 사용하지 않습니다. [프로젝트 기본]","다음 결정자는 현재 결정자의 왼쪽 사람이 맡고 새 결정자의 왼쪽 추리 플레이어부터 다시 개인 차례를 시작합니다. [프로젝트 기본]"]),
    ]
    for title,bullets in sections:
        c.setFont("NanumBold",10.7); c.setFillColor(colors.black); c.drawString(m,y,title); y-=6.2*mm
        for t in bullets:
            y=draw_paragraph(c,t,m+4*mm,y,colw-4*mm,size=8.6,leading=11.3,bullet="• "); y-=1.2*mm
        y-=2*mm
    c.setFont("NanumBold",10); c.drawString(m,y,"핵심 사고 루프  [원작(SOURCE)의 학습 의도에 맞춘 정리]"); y-=7*mm
    c.setFont("Nanum",8.8); c.drawString(m+4*mm,y,"데이터 관찰 → 공통점/차이 발견 → 가설 생성 → 새 동물 선택 → 위치 예측 → 결과 확인 → 가설 수정")
    c.setFont("Nanum",7); c.setFillColor(colors.HexColor("#666666")); c.drawCentredString(pw/2,8*mm,"원작을 단순 참/거짓 단일 규칙 게임으로 축소하지 않습니다.")
    c.showPage()

def draw_checklist(c):
    pw,ph=portrait(A4); m=15*mm; c.setPageSize((pw,ph)); y=ph-18*mm
    c.setFont("NanumBold",18); c.drawString(m,y,"Original KO 플레이테스트 기록지"); y-=10*mm
    c.setFont("Nanum",8.5); c.drawString(m,y,"날짜: __________________  학년: ______  인원: ______  라운드: ______"); y-=7*mm
    c.drawString(m,y,"결정자: __________________________  사용 분류 기준: ______________________________"); y-=9*mm
    blocks=[
        ("역할과 차례",["결정자와 추리 플레이어 역할을 구분했음","개인 차례가 시계 방향으로 자연스럽게 이어졌음","현재 차례 플레이어가 공식 행동 하나를 선택했음","새 동물 시험 때 모든 추리 플레이어가 결과 공개 전에 동시에 위치를 예측했음"]),
        ("비밀정보 관리",["결정자 외에는 비밀 분류 기준을 보지 못했음","분류 기준을 시작 전에 확정했고 라운드 중 바꾸지 않았음","결정자의 표정/말/손동작/망설임이 힌트가 되지 않았음"]),
        ("규칙 이해",["왼쪽 / 오른쪽 두 그룹을 이해함","분류 기준 추측과 새 카드 시험을 구분함","직접 예/아니오 질문 대신 카드를 통해 확인함"]),
        ("추론 행동",["양쪽의 공통점과 차이를 비교함","새 데이터 후 가설을 수정함","정보가 클 것 같은 동물을 선택하려고 함"]),
        ("실물/인쇄",["A4 플레이 영역에서 카드 이동에 문제가 없었음","한국어 동물명과 분류 기준을 쉽게 읽었음","필요한 테이블 공간에 전체 공개 카드와 플레이 영역을 배치할 수 있었음"]),
    ]
    for title,items in blocks:
        c.setFont("NanumBold",10.2); c.drawString(m,y,title); y-=5.7*mm
        c.setFont("Nanum",8.2)
        for t in items:
            c.drawString(m+4*mm,y,"□ "+t); y-=5.1*mm
        y-=1.6*mm
    c.setFont("NanumBold",9.7); c.drawString(m,y,"기록"); y-=5.8*mm
    for f in ["차례가 헷갈렸던 순간","가장 유용했던 추가 카드","가설을 바꾸게 한 카드","최종 정답까지 추가된 카드 수","라운드 시간"]:
        c.setFont("Nanum",8.2); c.drawString(m,y,f+":"); c.line(m+42*mm,y-1,pw-m,y-1); y-=7*mm
    c.setFont("NanumBold",9.2); c.drawString(m,y,"수정 우선순위"); y-=5.7*mm
    for t in ["P0 진행 불가:","P1 원작 구조/학습 문제:","P2 한국어 표현/운영/인쇄 문제:","P3 개선판 후보 아이디어:"]:
        c.setFont("Nanum",8.1); c.drawString(m,y,t); c.line(m+37*mm,y-1,pw-m,y-1); y-=6.6*mm
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
    draw_playmat(c)
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
