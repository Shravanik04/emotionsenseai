import io
import string
import datetime as dt
from collections import Counter
from typing import List, Dict, Any, Tuple
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas

from reportlab.graphics.shapes import Drawing, Rect, String as DString, Circle
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart

from app.models.social_analysis import SocialAnalysis, BatchAnalysisRun
from app.models.sentiment_model import SentimentRecord


# Stopwords for keyword extraction
STOP_WORDS = {
    'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', "you're", "you've", "you'll", "you'd",
    'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', "she's", 'her', 'hers',
    'herself', 'it', "it's", 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which',
    'who', 'whom', 'this', 'that', "that'll", 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been',
    'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if',
    'or', 'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between',
    'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out',
    'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why',
    'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not',
    'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', "don't",
    'should', "should've", 'now', 'd', 'll', 'm', 'o', 're', 've', 'y', 'ain', 'aren', "aren't", 'couldn',
    "couldn't", 'didn', "didn't", 'doesn', "doesn't", 'hadn', "hadn't", 'hasn', "hasn't", 'haven', "haven't",
    'isn', "isn't", 'ma', 'mightn', "mightn't", 'mustn', "mustn't", 'needn', "needn't", 'shan', "shan't",
    'shouldn', "shouldn't", 'wasn', "wasn't", 'weren', "weren't", 'won', "won't", 'wouldn', "wouldn't",
    'like', 'good', 'great', 'awesome', 'amazing', 'poor', 'bad', 'worst', 'excellent', 'would', 'could',
    'get', 'go', 'one', 'two', 'think', 'really', 'also', 'even'
}

EMOJI_MAP = {
    "joy": "😊", "happiness": "😀", "excitement": "🎉", "love": "❤️", "gratitude": "🙏", "pride": "🦁",
    "hope": "🌅", "optimism": "☀️", "relief": "😌", "confidence": "😎", "admiration": "👏",
    "inspiration": "💡", "curiosity": "🤔", "trust": "🤝", "satisfaction": "👍",
    "sadness": "😔", "anger": "😤", "fear": "😨", "anxiety": "😟", "stress": "😫", "frustration": "😒",
    "disappointment": "😞", "loneliness": "🏚️", "confusion": "🤷", "disgust": "🤢", "jealousy": "💚",
    "regret": "🤦", "guilt": "🥺", "embarrassment": "😳",
    "calm": "🧘", "neutral": "😐", "thoughtful": "💭", "analytical": "📊",
    "surprise": "😲", "nostalgia": "⏳", "determination": "✊", "sympathy": "💖", "compassion": "🤲",
    "awe": "🌌", "anticipation": "⏳", "skepticism": "🤨", "overwhelmed": "🤯", "shock": "💥"
}

PRONOUNS = {
    'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', "you're", "you've", "you'll", "you'd",
    'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', "she's", 'her', 'hers',
    'herself', 'it', "it's", 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves', 'who', 'whom',
    'whose', 'which', 'what', 'this', 'that', 'these', 'those', 'whoever', 'whomever'
}

COMMON_VERBS = {
    'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did',
    'doing', 'say', 'says', 'said', 'saying', 'go', 'goes', 'going', 'went', 'gone', 'make', 'makes', 'made',
    'making', 'get', 'gets', 'getting', 'got', 'gotten', 'know', 'knows', 'knew', 'knowing', 'think', 'thinks',
    'thought', 'thinking', 'take', 'takes', 'took', 'taken', 'taking', 'see', 'sees', 'saw', 'seen', 'seeing',
    'come', 'comes', 'coming', 'came', 'want', 'wants', 'wanted', 'wanting', 'look', 'looks', 'looked', 'looking',
    'use', 'uses', 'used', 'using', 'find', 'finds', 'found', 'finding', 'give', 'gives', 'gave', 'given',
    'giving', 'tell', 'tells', 'told', 'telling', 'work', 'works', 'worked', 'working', 'call', 'calls',
    'called', 'calling', 'try', 'tries', 'tried', 'trying', 'ask', 'asks', 'asked', 'asking', 'need', 'needs',
    'needed', 'needing', 'feel', 'feels', 'felt', 'feeling', 'become', 'becomes', 'became', 'becoming', 'leave',
    'leaves', 'left', 'leaving', 'put', 'puts', 'putting', 'keep', 'keeps', 'kept', 'keeping', 'let', 'lets',
    'letting', 'begin', 'begins', 'began', 'beginning', 'start', 'starts', 'started', 'starting', 'help',
    'helps', 'helped', 'helping', 'show', 'shows', 'showed', 'showing', 'play', 'plays', 'played', 'playing',
    'run', 'runs', 'ran', 'running', 'write', 'writes', 'wrote', 'written', 'writing', 'like', 'likes', 'liked',
    'liking', 'live', 'lives', 'lived', 'living', 'believe', 'believes', 'believed', 'believing', 'hold',
    'holds', 'held', 'holding', 'bring', 'brings', 'brought', 'bringing', 'happen', 'happens', 'happened',
    'happening', 'must', 'should', 'would', 'could', 'will', 'can', 'may', 'might', 'shall'
}

GENERIC_WORDS = {
    'thing', 'things', 'something', 'anything', 'everything', 'nothing', 'one', 'two', 'three', 'first',
    'second', 'time', 'times', 'day', 'days', 'week', 'weeks', 'year', 'years', 'month', 'months', 'way', 'ways',
    'actual', 'actually', 'really', 'very', 'also', 'even', 'just', 'still', 'again', 'here', 'there',
    'when', 'where', 'why', 'how', 'who', 'about', 'some', 'any', 'other', 'others', 'such',
    'okay', 'people', 'person', 'lot', 'lots', 'much',
    'many', 'more', 'most', 'less', 'least', 'few', 'fewer', 'bit', 'little', 'almost', 'maybe', 'perhaps',
    'probably', 'definitely', 'clearly', 'simply', 'total', 'totally', 'complete', 'completely'
}


class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        # Suppress headers/footers on page 1 (cover page)
        if self._pageNumber == 1:
            return
            
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(HexColor("#1e1b4b")) # Dark Indigo
        
        # Header
        self.drawString(54, 755, "EmotionSense AI")
        self.setFont("Helvetica", 8)
        self.setFillColor(HexColor("#64748b")) # Slate
        self.drawRightString(558, 755, "Emotion Intelligence & Sentiment Report")
        
        self.setStrokeColor(HexColor("#cbd5e1")) # slate-300
        self.setLineWidth(0.5)
        self.line(54, 747, 558, 747)
        
        # Footer
        self.drawString(54, 38, "Generated by EmotionSense AI  |  Hugging Face Transformer Models")
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 38, page_text)
        self.line(54, 48, 558, 48)
        
        self.restoreState()

def extract_keywords_from_texts(texts: List[str]) -> Dict[str, List[Tuple[str, int]]]:
    """Helper to extract top keywords from a list of strings."""
    words_list = []
    for text in texts:
        clean = [
            w.strip(string.punctuation).lower()
            for w in text.split()
            if w.strip(string.punctuation)
        ]
        words_list.extend([w for w in clean if w not in STOP_WORDS and len(w) > 2])
        
    c = Counter(words_list)
    return c.most_common(8)


def draw_sentiment_pie_chart(pos_pct: float, neg_pct: float, neu_pct: float, mix_pct: float) -> Drawing:
    d = Drawing(400, 160)

    pc = Pie()
    pc.x = 120
    pc.y = 15
    pc.width = 130
    pc.height = 130
    pc.data = [pos_pct, neg_pct, neu_pct, mix_pct]
    pc.labels = [f"Pos ({pos_pct}%)", f"Neg ({neg_pct}%)", f"Neu ({neu_pct}%)", f"Mix ({mix_pct}%)"]
    pc.slices.strokeWidth = 0.5
    pc.slices.strokeColor = HexColor("#ffffff")
    pc.slices[0].fillColor = HexColor("#10b981") # Green
    pc.slices[1].fillColor = HexColor("#ef4444") # Red
    pc.slices[2].fillColor = HexColor("#f59e0b") # Amber
    pc.slices[3].fillColor = HexColor("#8b5cf6") # Purple (Mixed)
    d.add(pc)
    return d

def draw_emotion_bar_chart(emotion_counts: Dict[str, int], total: int) -> Drawing:
    sorted_emotions = sorted(emotion_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    if not sorted_emotions:
        sorted_emotions = [("neutral", 1)]
        
    d = Drawing(400, 130)
    bc = VerticalBarChart()
    bc.x = 40
    bc.y = 20
    bc.height = 90
    bc.width = 320
    bc.data = [[round((val / total) * 100, 1) for name, val in sorted_emotions]]
    bc.categoryAxis.categoryNames = [f"{name.capitalize()} ({round((val/total)*100)}%)" for name, val in sorted_emotions]
    bc.categoryAxis.labels.fontSize = 8
    bc.categoryAxis.labels.dy = -10
    
    bc.valueAxis.valueMin = 0
    bc.valueAxis.valueMax = 100
    bc.valueAxis.valueStep = 25
    bc.bars[0].fillColor = HexColor("#6366f1") # Indigo-500
    bc.bars.strokeColor = None
    d.add(bc)
    return d

def draw_aspect_sentiment_chart(aspect_counts: Dict[str, Dict[str, int]]) -> Drawing:
    sorted_aspects = sorted(aspect_counts.items(), key=lambda x: sum(x[1].values()), reverse=True)[:5]
    
    d = Drawing(400, 140)
    y_offset = 110
    bar_width = 200
    bar_height = 8
    
    # Legend
    d.add(Rect(260, 125, 8, 8, fillColor=HexColor("#10b981"), strokeColor=None))
    d.add(DString(272, 126, "Positive", fontName="Helvetica", fontSize=8, fillColor=HexColor("#475569")))
    d.add(Rect(310, 125, 8, 8, fillColor=HexColor("#ef4444"), strokeColor=None))
    d.add(DString(322, 126, "Negative", fontName="Helvetica", fontSize=8, fillColor=HexColor("#475569")))
    d.add(Rect(355, 125, 8, 8, fillColor=HexColor("#f59e0b"), strokeColor=None))
    d.add(DString(367, 126, "Neutral", fontName="Helvetica", fontSize=8, fillColor=HexColor("#475569")))
    
    for aspect, counts in sorted_aspects:
        total = sum(counts.values()) or 1
        pos_p = counts.get("positive", 0) + counts.get("mixed", 0) * 0.5
        neg_p = counts.get("negative", 0) + counts.get("mixed", 0) * 0.5
        neu_p = counts.get("neutral", 0)
        
        pos_w = (pos_p / total) * bar_width
        neg_w = (neg_p / total) * bar_width
        neu_w = (neu_p / total) * bar_width
        
        # Aspect label
        d.add(DString(10, y_offset + 1, f"{aspect[:22]}", fontName="Helvetica-Bold", fontSize=8, fillColor=HexColor("#1e293b")))
        
        # Stacked Bar
        curr_x = 130
        if pos_w > 0:
            d.add(Rect(curr_x, y_offset, pos_w, bar_height, fillColor=HexColor("#10b981"), strokeColor=None))
            curr_x += pos_w
        if neg_w > 0:
            d.add(Rect(curr_x, y_offset, neg_w, bar_height, fillColor=HexColor("#ef4444"), strokeColor=None))
            curr_x += neg_w
        if neu_w > 0:
            d.add(Rect(curr_x, y_offset, neu_w, bar_height, fillColor=HexColor("#f59e0b"), strokeColor=None))
            
        y_offset -= 20
        
    return d

def draw_top_topics_chart(keywords: List[Tuple[str, int]]) -> Drawing:
    d = Drawing(400, 130)
    if not keywords:
        return d
        
    max_count = max([c for w, c in keywords]) or 1
    y_offset = 100
    max_bar_width = 200
    
    for word, count in keywords[:5]:
        w_width = (count / max_count) * max_bar_width
        # Label
        d.add(DString(10, y_offset + 2, word.capitalize(), fontName="Helvetica-Bold", fontSize=8, fillColor=HexColor("#1e293b")))
        # Bar
        d.add(Rect(130, y_offset, w_width, 8, fillColor=HexColor("#3b82f6"), strokeColor=None, rx=3, ry=3))
        # Count Label
        d.add(DString(135 + w_width, y_offset + 2, f"{count}", fontName="Helvetica", fontSize=8, fillColor=HexColor("#64748b")))
        
        y_offset -= 20
        
    return d

def draw_confidence_distribution_chart(confidences: List[float]) -> Drawing:
    bins = {"0-50%": 0, "50-70%": 0, "70-90%": 0, "90-100%": 0}
    for c in confidences:
        if c < 0.5:
            bins["0-50%"] += 1
        elif c < 0.7:
            bins["50-70%"] += 1
        elif c < 0.9:
            bins["70-90%"] += 1
        else:
            bins["90-100%"] += 1
            
    d = Drawing(400, 130)
    bc = VerticalBarChart()
    bc.x = 40
    bc.y = 20
    bc.height = 90
    bc.width = 300
    bc.data = [[v for v in bins.values()]]
    bc.categoryAxis.categoryNames = list(bins.keys())
    bc.categoryAxis.labels.fontSize = 8
    bc.categoryAxis.labels.dy = -10
    
    max_val = max(bins.values()) or 1
    bc.valueAxis.valueMin = 0
    bc.valueAxis.valueMax = max_val
    bc.valueAxis.valueStep = max(1, round(max_val / 3))
    bc.bars[0].fillColor = HexColor("#8b5cf6") # Purple-500
    bc.bars.strokeColor = None
    d.add(bc)
    return d

def draw_language_distribution_chart(lang_counts: Dict[str, int]) -> Drawing:
    sorted_langs = sorted(lang_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    if not sorted_langs:
        sorted_langs = [("English", 1)]
        
    d = Drawing(400, 130)
    max_count = max([c for l, c in sorted_langs]) or 1
    y_offset = 100
    max_bar_width = 200
    
    for lang, count in sorted_langs:
        w_width = (count / max_count) * max_bar_width
        # Label
        d.add(DString(10, y_offset + 2, lang, fontName="Helvetica-Bold", fontSize=8, fillColor=HexColor("#1e293b")))
        # Bar
        d.add(Rect(130, y_offset, w_width, 8, fillColor=HexColor("#10b981"), strokeColor=None, rx=3, ry=3))
        # Count
        d.add(DString(135 + w_width, y_offset + 2, f"{count}", fontName="Helvetica", fontSize=8, fillColor=HexColor("#64748b")))
        
        y_offset -= 20
        
    return d

def draw_confidence_bar(confidence: float) -> Drawing:
    d = Drawing(400, 25)
    # Background Track
    d.add(Rect(0, 5, 340, 12, fillColor=HexColor("#f1f5f9"), strokeColor=None, rx=6, ry=6))
    # Fill Track
    fill_width = max(8, 340 * confidence)
    color = "#10b981" if confidence >= 0.75 else ("#f59e0b" if confidence >= 0.4 else "#ef4444")
    d.add(Rect(0, 5, fill_width, 12, fillColor=HexColor(color), strokeColor=None, rx=6, ry=6))
    # Percent String
    d.add(DString(350, 7, f"{round(confidence * 100, 1)}%", fontName="Helvetica-Bold", fontSize=10, fillColor=HexColor("#1e293b")))
    return d

def get_record_aspect(r: Any) -> str:
    if hasattr(r, "aspect") and r.aspect:
        return r.aspect
    from app.utils.aspect_utils import detect_aspect_and_sentiment
    return detect_aspect_and_sentiment(r.original_text)


def generate_pdf_report(db: Session, analysis_id: int, current_user_id: int, user_email: str) -> io.BytesIO:
    # 1. Fetch analysis record
    batch_run = db.query(BatchAnalysisRun).filter(BatchAnalysisRun.id == analysis_id, BatchAnalysisRun.user_id == current_user_id).first()
    is_social = False
    is_batch = False
    batch_records = []
    social_record = None
    record = None
    
    if batch_run:
        is_social = True
        is_batch = True
        batch_records = db.query(SocialAnalysis).filter(
            SocialAnalysis.batch_run_id == batch_run.id,
            SocialAnalysis.user_id == current_user_id
        ).all()
        if not batch_records:
            # Fallback to date proximity query
            start_t = batch_run.created_at - dt.timedelta(seconds=5)
            end_t = batch_run.created_at + dt.timedelta(seconds=5)
            batch_records = db.query(SocialAnalysis).filter(
                SocialAnalysis.user_id == current_user_id,
                SocialAnalysis.platform == batch_run.platform,
                SocialAnalysis.created_at >= start_t,
                SocialAnalysis.created_at <= end_t
            ).all()
        if batch_records:
            social_record = batch_records[0]
        else:
            social_record = SocialAnalysis(
                platform=batch_run.platform,
                created_at=batch_run.created_at,
                original_text="Batch Run (No Linked Comments)"
            )
    else:
        # Fallback to single social comment lookup
        social_record = db.query(SocialAnalysis).filter(SocialAnalysis.id == analysis_id).first()
        if social_record:
            if social_record.user_id != current_user_id:
                raise HTTPException(status_code=403, detail="Unauthorized access to this report.")
            is_social = True
            
            # Load full batch if linked
            if social_record.batch_run_id:
                is_batch = True
                batch_records = db.query(SocialAnalysis).filter(
                    SocialAnalysis.batch_run_id == social_record.batch_run_id
                ).all()
            else:
                start_t = social_record.created_at - dt.timedelta(seconds=2)
                end_t = social_record.created_at + dt.timedelta(seconds=2)
                batch_records = db.query(SocialAnalysis).filter(
                    SocialAnalysis.user_id == current_user_id,
                    SocialAnalysis.platform == social_record.platform,
                    SocialAnalysis.created_at >= start_t,
                    SocialAnalysis.created_at <= end_t
                ).all()
                is_batch = len(batch_records) > 1
        else:
            # Check SentimentRecord
            sentiment_record = db.query(SentimentRecord).filter(SentimentRecord.id == analysis_id).first()
            if not sentiment_record:
                raise HTTPException(status_code=404, detail="Analysis record not found.")
                
            if hasattr(sentiment_record, "user_id") and sentiment_record.user_id is not None:
                if sentiment_record.user_id != current_user_id:
                    raise HTTPException(status_code=403, detail="Unauthorized access to this report.")
            record = sentiment_record

    
    # 2. Build Document Template
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=68,
        bottomMargin=68
    )

    # Styles
    raw_styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        "CoverTitle",
        parent=raw_styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=30,
        leading=36,
        textColor=HexColor("#4f46e5"),
        alignment=TA_CENTER,
        spaceAfter=12
    )
    
    subtitle_style = ParagraphStyle(
        "CoverSubtitle",
        parent=raw_styles["Normal"],
        fontName="Helvetica",
        fontSize=13,
        leading=16,
        textColor=HexColor("#475569"),
        alignment=TA_CENTER,
        spaceAfter=35
    )
    
    h1_style = ParagraphStyle(
        "SectionHeading",
        parent=raw_styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=HexColor("#1e1b4b"),
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )
    
    h2_style = ParagraphStyle(
        "SubSectionHeading",
        parent=raw_styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        textColor=HexColor("#312e81"),
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        "ReportBody",
        parent=raw_styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=HexColor("#334155")
    )
    
    bold_body_style = ParagraphStyle(
        "ReportBodyBold",
        parent=body_style,
        fontName="Helvetica-Bold"
    )

    quote_style = ParagraphStyle(
        "ReportQuote",
        parent=body_style,
        fontName="Helvetica-Oblique",
        leftIndent=15,
        rightIndent=15,
        textColor=HexColor("#475569")
    )

    # Compile data & story elements
    story = []

    # Get details
    created_at = social_record.created_at if is_social else record.created_at
    created_date = created_at.strftime("%B %d, %Y")
    created_time = created_at.strftime("%I:%M %p")
    
    # ------------------ COVER PAGE ------------------
    story.append(Spacer(1, 140))
    story.append(Paragraph("EmotionSense AI", title_style))
    story.append(Paragraph("AI-Powered Emotion Intelligence Report", subtitle_style))
    story.append(Spacer(1, 40))
    
    meta_data = [
        [Paragraph("Analysis Type:", bold_body_style), Paragraph("Social Media Batch Analysis" if is_batch else "Single Text Analysis", body_style)],
        [Paragraph("Analysis ID:", bold_body_style), Paragraph(f"SOC-B-{social_record.id}" if is_batch else (f"SOC-S-{social_record.id}" if is_social else f"TXT-{record.id}"), body_style)],
        [Paragraph("Platform Source:", bold_body_style), Paragraph(social_record.platform.upper() if is_social else "Direct Input", body_style)],
        [Paragraph("Generated Date:", bold_body_style), Paragraph(created_date, body_style)],
        [Paragraph("Generated Time:", bold_body_style), Paragraph(created_time, body_style)],
        [Paragraph("Generated For:", bold_body_style), Paragraph(user_email, body_style)],
    ]
    meta_table = Table(meta_data, colWidths=[120, 250])
    meta_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('LINEBELOW', (0,0), (-1,-1), 0.5, HexColor("#f1f5f9")),
    ]))
    story.append(meta_table)
    story.append(PageBreak())

    # Compile metrics
    records_list = batch_records if is_batch else [social_record if is_social else record]
    total_comments = len(records_list)
    
    text_length = sum([len(r.original_text) for r in records_list])
    word_count = sum([len(r.original_text.split()) for r in records_list])
    avg_processing_time = sum([r.processing_time_ms or 0.0 for r in records_list]) / total_comments
    
    # Sentiment calculation
    sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0, "mixed": 0}
    emotion_counts = {}
    lang_counts = {}
    sarcastic_count = 0
    total_confidence = 0.0
    aspect_counts = {}
    
    confidences = []
    
    for r in records_list:
        sent = r.sentiment.lower() if r.sentiment else "neutral"
        sentiment_counts[sent] = sentiment_counts.get(sent, 0) + 1
        
        emo = r.emotion.lower() if r.emotion else "neutral"
        emotion_counts[emo] = emotion_counts.get(emo, 0) + 1
        
        lang = r.detected_language or "English"
        lang_counts[lang] = lang_counts.get(lang, 0) + 1
        
        if getattr(r, "sarcasm_detected", False):
            sarcastic_count += 1
            
        conf = getattr(r, "confidence", 0.0) or getattr(r, "sentiment_confidence", 0.0) or 0.0
        total_confidence += conf
        confidences.append(conf)
        
        asp = get_record_aspect(r)
        if asp not in aspect_counts:
            aspect_counts[asp] = {"positive": 0, "negative": 0, "neutral": 0, "mixed": 0}
        aspect_counts[asp][sent] = aspect_counts[asp].get(sent, 0) + 1

    pos_pct = round((sentiment_counts["positive"] / total_comments) * 100, 1)
    neg_pct = round((sentiment_counts["negative"] / total_comments) * 100, 1)
    neu_pct = round((sentiment_counts["neutral"] / total_comments) * 100, 1)
    mix_pct = round((sentiment_counts["mixed"] / total_comments) * 100, 1)
    
    if pos_pct >= 70.0:
        overall_sentiment = "Positive"
    elif neg_pct >= 70.0:
        overall_sentiment = "Negative"
    else:
        overall_sentiment = "Mixed"
        
    avg_confidence = total_confidence / total_comments
    sarcasm_rate = (sarcastic_count / total_comments) * 100
    dominant_emotion = max(emotion_counts, key=emotion_counts.get) if emotion_counts else "neutral"
    dominant_emotion_emoji = EMOJI_MAP.get(dominant_emotion.lower(), "😐")
    dominant_lang = max(lang_counts, key=lang_counts.get) if lang_counts else "English"

    # ------------------ DETAILED COMMENT ANALYSIS TABLE ------------------
    story.append(Paragraph("Detailed Comment Analysis", h1_style))
    story.append(Spacer(1, 4))
    
    comment_cell_style = ParagraphStyle(
        "CommentCell",
        parent=body_style,
        fontSize=8,
        leading=10
    )
    
    table_headers = [
        Paragraph("Comment", bold_body_style),
        Paragraph("Sentiment", bold_body_style),
        Paragraph("Emotion", bold_body_style),
        Paragraph("Confidence", bold_body_style),
        Paragraph("Sarcasm", bold_body_style),
        Paragraph("Language", bold_body_style),
        Paragraph("Aspect", bold_body_style)
    ]
    table_rows = [table_headers]
    
    for r in records_list:
        text_val = r.original_text
        sent_val = r.sentiment.capitalize() if r.sentiment else "Neutral"
        emo_val = r.emotion.capitalize() if r.emotion else "Neutral"
        
        conf = getattr(r, "confidence", 0.0) or getattr(r, "sentiment_confidence", 0.0) or 0.0
        conf_val = f"{round(conf * 100)}%"
        
        sarc_val = "Yes" if getattr(r, "sarcasm_detected", False) else "No"
        lang_val = getattr(r, "detected_language", "Unknown") or "Unknown"
        aspect_val = get_record_aspect(r)
        
        table_rows.append([
            Paragraph(text_val, comment_cell_style),
            Paragraph(sent_val, body_style),
            Paragraph(emo_val, body_style),
            Paragraph(conf_val, body_style),
            Paragraph(sarc_val, body_style),
            Paragraph(lang_val, body_style),
            Paragraph(aspect_val, body_style)
        ])
        
    # Table column widths (total = 504 pt)
    col_widths = [164, 50, 60, 50, 40, 60, 80]
    
    detailed_table = Table(table_rows, colWidths=col_widths, repeatRows=1)
    detailed_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), HexColor("#f8fafc")),
        ('GRID', (0,0), (-1,-1), 0.5, HexColor("#cbd5e1")),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(detailed_table)
    story.append(Spacer(1, 15))
    story.append(PageBreak())

    # ------------------ SECTION 1: EXECUTIVE SUMMARY ------------------
    story.append(Paragraph("Executive Summary", h1_style))
    story.append(Spacer(1, 4))
    
    # Generate executive summary dynamically
    praised = [aspect for aspect, counts in aspect_counts.items() if counts["positive"] > counts["negative"]]
    if not praised:
        praised = [aspect for aspect, counts in aspect_counts.items() if counts["positive"] > 0]
    top_praises = sorted(praised, key=lambda a: aspect_counts[a]["positive"], reverse=True)[:3]
    
    complained = [aspect for aspect, counts in aspect_counts.items() if counts["negative"] > counts["positive"]]
    if not complained:
        complained = [aspect for aspect, counts in aspect_counts.items() if counts["negative"] > 0]
    top_complaints = sorted(complained, key=lambda a: aspect_counts[a]["negative"], reverse=True)[:3]
    
    sarcasm_text = "Sarcastic comments were detected." if sarcasm_rate > 20 else "No sarcasm was detected."
    trend_text = "with a slightly positive trend" if pos_pct > neg_pct else ("with a slightly negative trend" if neg_pct > pos_pct else "with a neutral trend")
    overall_text = f"Overall audience response is {overall_sentiment} {trend_text}."
    
    strength_details = f"Most customers appreciated the {', '.join([p.lower() for p in top_praises])}." if praised else ""
    weakness_details = f"Negative feedback focused on {', '.join([c.lower() for c in top_complaints if c != 'None Detected'])}." if [c for c in top_complaints if c != 'None Detected'] else ""
    
    exec_summary = (
        f"Out of {total_comments} analyzed comments, "
        f"{sentiment_counts['positive']} Positive, "
        f"{sentiment_counts['negative']} Negative, "
        f"{sentiment_counts['neutral']} Neutral, "
        f"{sentiment_counts['mixed']} Mixed. "
        f"{strength_details} "
        f"{weakness_details} "
        f"{sarcasm_text} "
        f"{overall_text}"
    )
    story.append(Paragraph(exec_summary, body_style))
    story.append(Spacer(1, 15))

    # ------------------ SECTION 2: METRICS & ANALYSIS SUMMARY ------------------
    story.append(Paragraph("Analysis Summary", h1_style))
    
    summary_data = [
        [Paragraph("Metadata Field", bold_body_style), Paragraph("Value / Detail", bold_body_style)],
        [Paragraph("Analysis Source", body_style), Paragraph("Social Media Feed" if is_social else "Manual Text Input", body_style)],
        [Paragraph("Language Detected", body_style), Paragraph(dominant_lang, body_style)],
        [Paragraph("Character Length", body_style), Paragraph(f"{text_length} characters", body_style)],
        [Paragraph("Word Count", body_style), Paragraph(f"{word_count} words", body_style)],
        [Paragraph("Execution Latency", body_style), Paragraph(f"{round(avg_processing_time, 2)} ms", body_style)],
    ]
    summary_table = Table(summary_data, colWidths=[180, 320])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), HexColor("#f8fafc")),
        ('GRID', (0,0), (-1,-1), 0.5, HexColor("#cbd5e1")),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 15))

    results_data = [
        [Paragraph("Classification Metric", bold_body_style), Paragraph("Detected Class / Score", bold_body_style)],
        [Paragraph("Overall Sentiment", body_style), Paragraph(overall_sentiment, bold_body_style)],
        [Paragraph("Overall Emotion", body_style), Paragraph(f"{dominant_emotion_emoji} {dominant_emotion.capitalize()}", body_style)],
        [Paragraph("Average Model Confidence", body_style), Paragraph(f"{round(avg_confidence * 100, 2)}%", body_style)],
        [Paragraph("Sarcasm Prevalence", body_style), Paragraph("Yes (Sarcasm Detected)" if sarcasm_rate > 20 else "No Sarcasm Detected", body_style)],
    ]
    results_table = Table(results_data, colWidths=[180, 320])
    results_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), HexColor("#f8fafc")),
        ('GRID', (0,0), (-1,-1), 0.5, HexColor("#cbd5e1")),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(results_table)
    story.append(PageBreak())

    # ------------------ SECTION 3: VISUALIZATIONS CHARTS GRID ------------------
    story.append(Paragraph("Visualizations & Distribution Charts", h1_style))
    story.append(Spacer(1, 5))
    
    story.append(Paragraph("Sentiment Distribution", h2_style))
    story.append(draw_sentiment_pie_chart(pos_pct, neg_pct, neu_pct, mix_pct))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("Emotion Distribution", h2_style))
    story.append(draw_emotion_bar_chart(emotion_counts, total_comments))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("Aspect Sentiment (Top Features)", h2_style))
    story.append(draw_aspect_sentiment_chart(aspect_counts))
    story.append(PageBreak())
    
    story.append(Paragraph("Top Topics / Key Terms", h2_style))
    all_texts = [r.original_text for r in records_list]
    words_list = []
    for text in all_texts:
        clean = [w.strip(string.punctuation).lower() for w in text.split() if w.strip(string.punctuation)]
        exclusions = STOP_WORDS | PRONOUNS | COMMON_VERBS | GENERIC_WORDS
        words_list.extend([w for w in clean if w not in exclusions and len(w) > 3])
    top_keywords = Counter(words_list).most_common(5)
    story.append(draw_top_topics_chart(top_keywords))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("Confidence Level Distribution", h2_style))
    story.append(draw_confidence_distribution_chart(confidences))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("Language Distribution", h2_style))
    story.append(draw_language_distribution_chart(lang_counts))
    story.append(PageBreak())

    # ------------------ SECTION 4: BUSINESS INSIGHTS (BATCH ONLY) ------------------
    if is_batch:
        story.append(Paragraph("Business & Actionable Insights", h1_style))
        story.append(Spacer(1, 4))
        
        recs = []
        if complained and [c for c in top_complaints if c != 'None Detected']:
            weakness_str = " and ".join(top_complaints)
            strength_str = f" while maintaining the excellent {' and '.join(top_praises)}" if praised else ""
            recs.append(f"Improve {weakness_str.lower()}{strength_str.lower()} to enhance overall user satisfaction.")
        elif praised:
            recs.append(f"Continue leveraging your key strengths in {', '.join(top_praises).lower()} to sustain positive momentum.")
            
        if sarcasm_rate > 20 and [c for c in top_complaints if c != 'None Detected']:
            recs.append(f"High sarcasm rate detected ({round(sarcasm_rate, 1)}%). Monitor underlying feedback on {', '.join(top_complaints).lower()} for subtle critique.")
            
        if not recs:
            recs.append("Maintain quality of services and continue monitoring customer sentiments.")
            
        story.append(Paragraph("Strategic Actions Recommended:", h2_style))
        for r in recs:
            story.append(Paragraph(f"• {r}", body_style))
            story.append(Spacer(1, 4))
            
    doc.build(story, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer

