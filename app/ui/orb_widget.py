"""
app/ui/orb_widget.py
 
Free-flowing AI Assistant Orb — liquid plasma energy, not a solid sphere.
 
Design Philosophy:
  The orb is NOT a ball. It is a contained energy field.
  It breathes, warps, pulses, and bleeds light into the space around it.
  No hard edges. No solid fills. Only layered translucent gradients,
  morphing blob paths, and light that spills outward.
 
Architecture:
  - Driven entirely by StateManager.state property + state_changed signal
  - No hardcoded test states, no auto-cycling timers
  - 60 FPS QPainter rendering
  - Organic blob shape via sine-perturbed path (not a circle)
  - All compositing uses additive-style alpha layering
 
States:
  IDLE      → deep blue,  slow drift, barely-there presence
  LISTENING → cyan,       sonar rings, attentive pulse
  THINKING  → violet,     spinning plasma arc, comet head
  SPEAKING  → gold,       radial waveform bars, ripples
  ERROR     → crimson,    flicker, shake, warning rings
 
Controls (dev):
  Drag         → move orb
  Double-click → cycle state (remove in production)
"""
 
from __future__ import annotations
 
import math
import random
from typing import TYPE_CHECKING
 
from PyQt6.QtCore import Qt, QTimer, QPoint, QPointF, QRectF
from PyQt6.QtGui import (
    QPainter, QColor, QRadialGradient,
    QPen, QBrush, QPainterPath,
)
from PyQt6.QtWidgets import QWidget
 
from app.core.state import AssistantState
 
if TYPE_CHECKING:
    from app.core.state_manager import StateManager
 
 
# ── Canvas ────────────────────────────────────────────────────────────────────
W        = 240          # widget width == height (px)
CX       = W / 2
CY       = W / 2
R_CORE   = 38           # nominal core radius before animation
 
# ── Per-state palettes  (pr,pg,pb,  gr,gg,gb) ─────────────────────────────────
_PAL: dict[AssistantState, tuple] = {
    AssistantState.IDLE:      ( 35, 110, 255,  10,  45, 160),
    AssistantState.LISTENING: (  0, 215, 210,   0, 110, 175),
    AssistantState.THINKING:  (155,  50, 255,  75,  12, 185),
    AssistantState.SPEAKING:  (255, 180,  25, 195, 105,   0),
    AssistantState.ERROR:     (255,  38,  50, 175,   0,  18),
}
 
# ── Blob shape: how many sine lobes per state ─────────────────────────────────
_BLOB_LOBES: dict[AssistantState, int] = {
    AssistantState.IDLE:      3,
    AssistantState.LISTENING: 4,
    AssistantState.THINKING:  5,
    AssistantState.SPEAKING:  6,
    AssistantState.ERROR:     4,
}
 
_BLOB_AMP: dict[AssistantState, float] = {
    AssistantState.IDLE:       4.0,
    AssistantState.LISTENING:  7.0,
    AssistantState.THINKING:   5.0,
    AssistantState.SPEAKING:  10.0,
    AssistantState.ERROR:      8.0,
}
 
_BAR_COUNT  = 24
_BAR_FREQS  = [0.038 + i * 0.014 for i in range(_BAR_COUNT)]
_BAR_PHASES = [random.uniform(0, math.tau) for _ in range(_BAR_COUNT)]
 
 
# ── Pure helpers ──────────────────────────────────────────────────────────────
 
def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t
 
def _clamp_f(v: float, lo: float = 0.0, hi: float = 255.0) -> float:
    """Always returns a real float — never goes negative (avoids complex pow)."""
    return max(lo, min(hi, float(v)))
 
def _ci(v) -> int:
    return int(_clamp_f(float(v)))
 
def _c(r, g, b, a=255) -> QColor:
    return QColor(_ci(r), _ci(g), _ci(b), _ci(a))
 
 
# ── Blob path builder ─────────────────────────────────────────────────────────
 
def _blob_path(cx: float, cy: float, base_r: float,
               lobes: int, amp: float, tick: float,
               speed: float = 1.0, pts: int = 72) -> QPainterPath:
    """
    Returns a smooth closed QPainterPath that looks like a morphing liquid blob.
    The radius is perturbed by overlapping sine waves so it breathes organically.
    Uses cubicTo for smooth curves — no jagged polygon look.
    """
    coords = []
    for i in range(pts):
        angle = (i / pts) * math.tau
        # Primary lobe warp
        warp  = amp * math.sin(lobes * angle + tick * speed * 0.018)
        # Secondary slower warp at different frequency for extra organicism
        warp += (amp * 0.4) * math.sin((lobes + 1) * angle - tick * speed * 0.011)
        r = base_r + warp
        coords.append((cx + math.cos(angle) * r, cy + math.sin(angle) * r))
 
    path = QPainterPath()
    n = len(coords)
 
    # Catmull-Rom → cubic Bezier conversion for smooth interpolation
    def _cp(i):
        return coords[i % n]
 
    x0, y0 = _cp(0)
    path.moveTo(x0, y0)
    for i in range(n):
        p0 = _cp(i - 1)
        p1 = _cp(i)
        p2 = _cp(i + 1)
        p3 = _cp(i + 2)
        cp1x = p1[0] + (p2[0] - p0[0]) / 6
        cp1y = p1[1] + (p2[1] - p0[1]) / 6
        cp2x = p2[0] - (p3[0] - p1[0]) / 6
        cp2y = p2[1] - (p3[1] - p1[1]) / 6
        path.cubicTo(cp1x, cp1y, cp2x, cp2y, p2[0], p2[1])
 
    path.closeSubpath()
    return path
 
 
# ── Orbiting mote ─────────────────────────────────────────────────────────────
 
class _Mote:
    def __init__(self, slot: int, total: int, orbit: float, speed: float):
        self.orbit = orbit
        self.speed = speed
        self.base_angle = (slot / total) * math.tau
        self.dot_r = random.uniform(1.8, 3.2)
        self.phase = random.uniform(0, math.tau)
 
    def pos(self, tick: float) -> QPointF:
        a = self.base_angle + tick * self.speed
        return QPointF(CX + math.cos(a) * self.orbit,
                       CY + math.sin(a) * self.orbit)
 
    def alpha(self, tick: float) -> int:
        return _ci(120 + 80 * math.sin(tick * 0.021 + self.phase))
 
 
# ══════════════════════════════════════════════════════════════════════════════
class OrbWidget(QWidget):
    """
    Free-flowing living orb widget.
    Drop into any layout or use as frameless overlay.
    Controlled entirely via StateManager.
    """
 
    def __init__(self, state_manager: "StateManager", parent=None):
        super().__init__(parent)
        self.sm = state_manager
        self._state = state_manager.state
 
        # ── Window ────────────────────────────────────────────────────────────
        self.setFixedSize(W, W)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool,
        )
 
        # ── Colour channels (interpolated) ────────────────────────────────────
        p = _PAL[self._state]
        self._pr, self._pg, self._pb = float(p[0]), float(p[1]), float(p[2])
        self._gr, self._gg, self._gb = float(p[3]), float(p[4]), float(p[5])
 
        # ── Blob shape channels (interpolated) ────────────────────────────────
        self._lobes_f: float = float(_BLOB_LOBES[self._state])
        self._amp_f:   float = _BLOB_AMP[self._state]
 
        # ── Master tick ───────────────────────────────────────────────────────
        self._tick: float = 0.0
 
        # ── Core radius (interpolated) ─────────────────────────────────────────
        self._radius: float = float(R_CORE)
 
        # ── Drag ──────────────────────────────────────────────────────────────
        self._drag_anchor = QPoint()
 
        # ── IDLE motes ────────────────────────────────────────────────────────
        self._idle_motes = [
            _Mote(i, 5, orbit=58 + i * 3, speed=0.006 + i * 0.0007)
            for i in range(5)
        ]
 
        # ── THINKING ──────────────────────────────────────────────────────────
        self._think_motes = [
            _Mote(i, 4, orbit=62 + i * 4, speed=0.017 + i * 0.003)
            for i in range(4)
        ]
        self._think_angle: float = 0.0
 
        # ── LISTENING ─────────────────────────────────────────────────────────
        self._ring_phase: float = 0.0
 
        # ── SPEAKING ripples ──────────────────────────────────────────────────
        self._ripples: list[float] = []
 
        # ── ERROR ─────────────────────────────────────────────────────────────
        self._shake_x: float = 0.0
        self._shake_y: float = 0.0
        self._flicker: float = 1.0
 
        # ── State signal ──────────────────────────────────────────────────────
        state_manager.state_changed.connect(self._on_state_changed)
 
        # ── 60 FPS ────────────────────────────────────────────────────────────
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick_frame)
        self._timer.start(16)
 
    # ── State change ──────────────────────────────────────────────────────────
 
    def _on_state_changed(self, new_state: AssistantState):
        self._state = new_state
        if new_state == AssistantState.SPEAKING:
            self._ripples.clear()
        if new_state == AssistantState.ERROR:
            self._flicker = 1.0
 
    # ── Per-frame ─────────────────────────────────────────────────────────────
 
    def _tick_frame(self):
        self._tick += 1.0
        t  = self._tick
        st = self._state
        f  = 0.05   # lerp factor → ~20-frame transitions
 
        # Colour lerp
        tgt = _PAL[st]
        self._pr = _lerp(self._pr, tgt[0], f)
        self._pg = _lerp(self._pg, tgt[1], f)
        self._pb = _lerp(self._pb, tgt[2], f)
        self._gr = _lerp(self._gr, tgt[3], f)
        self._gg = _lerp(self._gg, tgt[4], f)
        self._gb = _lerp(self._gb, tgt[5], f)
 
        # Blob shape lerp
        self._lobes_f = _lerp(self._lobes_f, float(_BLOB_LOBES[st]), f * 0.5)
        self._amp_f   = _lerp(self._amp_f,   _BLOB_AMP[st],          f * 0.5)
 
        # State-specific updates
        if st == AssistantState.THINKING:
            self._think_angle = (self._think_angle + 2.6) % 360.0
 
        elif st == AssistantState.LISTENING:
            self._ring_phase += 0.062
 
        elif st == AssistantState.SPEAKING:
            self._ring_phase += 0.09
            amp = self._speak_amp()
            if int(t) % 20 == 0 and amp > 0.50:
                self._ripples.append(float(R_CORE + 6))
            # advance + prune — clamp progress to [0,1] before any pow()
            self._ripples = [r + 2.0 for r in self._ripples if r < 92.0]
 
        elif st == AssistantState.ERROR:
            self._shake_x = random.uniform(-5.0, 5.0)
            self._shake_y = random.uniform(-5.0, 5.0)
            self._flicker = 0.70 + 0.30 * math.sin(t * 0.37)
        else:
            self._shake_x *= 0.75
            self._shake_y *= 0.75
 
        self.update()
 
    # ── Amplitude model (swap for real mic RMS later) ─────────────────────────
 
    def _speak_amp(self) -> float:
        """
        Simulated speech amplitude in [0, 1].
        To connect a real microphone:
            return self.audio_source.get_rms()   # float 0.0–1.0
        """
        v = sum(math.sin(self._tick * f + p)
                for f, p in zip(_BAR_FREQS[:3], _BAR_PHASES[:3]))
        return (v / 3.0 + 1.0) / 2.0
 
    # ── paintEvent ────────────────────────────────────────────────────────────
 
    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHints(
            QPainter.RenderHint.Antialiasing |
            QPainter.RenderHint.SmoothPixmapTransform,
        )
        cx = CX + self._shake_x
        cy = CY + self._shake_y
 
        {
            AssistantState.IDLE:      self._draw_idle,
            AssistantState.LISTENING: self._draw_listening,
            AssistantState.THINKING:  self._draw_thinking,
            AssistantState.SPEAKING:  self._draw_speaking,
            AssistantState.ERROR:     self._draw_error,
        }[self._state](painter, cx, cy)
 
        painter.end()
 
    # ═════════════════════════════════════════════════════════════════════════
    # STATE RENDERERS
    # ═════════════════════════════════════════════════════════════════════════
 
    def _draw_idle(self, p: QPainter, cx: float, cy: float):
        r, g, b = self._pr, self._pg, self._pb
        gr, gg, gb = self._gr, self._gg, self._gb
 
        # Slow breathe — 4 s period
        breathe = 0.5 + 0.5 * math.sin(self._tick * math.pi / 120)
        base_r  = R_CORE - 6 + breathe * 8
 
        # Distant outer whisper halo
        self._glow(p, cx, cy, 90, 14, r, g, b)
        self._glow(p, cx, cy, 60, 22, r, g, b)
 
        # Drifting motes behind core
        for mote in self._idle_motes:
            mp = mote.pos(self._tick)
            a  = mote.alpha(self._tick)
            self._soft_dot(p, mp.x(), mp.y(), mote.dot_r * 3.5, r, g, b, _ci(a * 0.22))
            self._soft_dot(p, mp.x(), mp.y(), mote.dot_r,        r, g, b, a)
 
        # Blob core — soft, no hard edge
        self._blob_core(p, cx, cy, base_r, (r, g, b), (gr, gg, gb),
                        lobes=int(round(self._lobes_f)),
                        amp=self._amp_f, speed=0.6)
 
    def _draw_listening(self, p: QPainter, cx: float, cy: float):
        r, g, b = self._pr, self._pg, self._pb
        gr, gg, gb = self._gr, self._gg, self._gb
        ph = self._ring_phase
 
        # Three sonar rings
        for base_r, speed_mul, alpha_frac in [
            (50, 1.00, 0.20),
            (66, 0.65, 0.12),
            (80, 0.42, 0.07),
        ]:
            ring_r = base_r + 11 * math.sin(ph * speed_mul)
            pen = QPen(_c(r, g, b, _ci(255 * alpha_frac)))
            pen.setWidthF(1.5)
            p.setPen(pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(QPointF(cx, cy), ring_r, ring_r)
 
        # Cardinal accent dots
        dot_d = 46 + 9 * math.sin(ph)
        for angle in (0, math.pi * 0.5, math.pi, math.pi * 1.5):
            dx = cx + math.cos(angle) * dot_d
            dy = cy + math.sin(angle) * dot_d
            da = _ci(150 + 80 * math.sin(ph + angle))
            self._soft_dot(p, dx, dy, 4.2, r, g, b, da)
 
        self._glow(p, cx, cy, 82, 36, r, g, b)
 
        # Faster breathe (1 s period)
        breathe = 0.5 + 0.5 * math.sin(self._tick * math.pi / 30)
        base_r  = R_CORE + breathe * 10
 
        self._blob_core(p, cx, cy, base_r, (r, g, b), (gr, gg, gb),
                        lobes=int(round(self._lobes_f)),
                        amp=self._amp_f, speed=1.1)
 
    def _draw_thinking(self, p: QPainter, cx: float, cy: float):
        r, g, b = self._pr, self._pg, self._pb
        gr, gg, gb = self._gr, self._gg, self._gb
 
        orbit_r = 60.0
        arc_deg = 255
 
        # Plasma arc — 4 layers for depth/glow
        for width, alpha in [(9, 15), (6, 40), (3, 110), (1, 220)]:
            pen = QPen(_c(r, g, b, alpha))
            pen.setWidth(width)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
            start = int((self._think_angle + (360 - arc_deg) / 2) * 16)
            span  = int(arc_deg * 16)
            d = orbit_r
            p.drawArc(QRectF(cx - d, cy - d, d * 2, d * 2), start, span)
 
        # Comet head
        head_rad = math.radians(self._think_angle)
        hx = cx + math.cos(head_rad) * orbit_r
        hy = cy - math.sin(head_rad) * orbit_r
        self._soft_dot(p, hx, hy, 10, r,   g,   b,   55)
        self._soft_dot(p, hx, hy,  5, r,   g,   b,  210)
        self._soft_dot(p, hx, hy,  2, 255, 255, 255, 215)
 
        # Counter-arc
        inner_r = 38.0
        pen2 = QPen(_c(gr, gg, gb, 90))
        pen2.setWidth(2)
        pen2.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen2)
        p.setBrush(Qt.BrushStyle.NoBrush)
        start2 = int((-self._think_angle * 0.55 + 180) * 16)
        p.drawArc(QRectF(cx - inner_r, cy - inner_r, inner_r * 2, inner_r * 2),
                  start2, int(165 * 16))
 
        # Fast computation motes
        for mote in self._think_motes:
            mp = mote.pos(self._tick)
            a  = mote.alpha(self._tick)
            self._soft_dot(p, mp.x(), mp.y(), mote.dot_r * 2.8, r, g, b, _ci(a * 0.22))
            self._soft_dot(p, mp.x(), mp.y(), mote.dot_r,        r, g, b, a)
 
        self._glow(p, cx, cy, 72, 32, r, g, b)
 
        # Static blob (no breathe — focused computation)
        self._blob_core(p, cx, cy, R_CORE - 4, (r, g, b), (gr, gg, gb),
                        lobes=int(round(self._lobes_f)),
                        amp=self._amp_f, speed=2.2)
 
    def _draw_speaking(self, p: QPainter, cx: float, cy: float):
        r, g, b = self._pr, self._pg, self._pb
        gr, gg, gb = self._gr, self._gg, self._gb
        amp = self._speak_amp()
 
        # Radial waveform bars
        for i in range(_BAR_COUNT):
            angle   = (i / _BAR_COUNT) * math.tau
            bar_amp = (math.sin(self._tick * _BAR_FREQS[i] + _BAR_PHASES[i]) + 1) / 2
            inner   = R_CORE + 6
            outer   = inner + 8 + bar_amp * 30
            x1 = cx + math.cos(angle) * inner
            y1 = cy + math.sin(angle) * inner
            x2 = cx + math.cos(angle) * outer
            y2 = cy + math.sin(angle) * outer
            bar_a = _ci(70 + bar_amp * 175)
            pen = QPen(_c(r, g, b, bar_a))
            pen.setWidthF(1.4 + bar_amp * 2.2)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawLine(QPointF(x1, y1), QPointF(x2, y2))
 
        # Expanding ripples — safe clamp before any math
        for rip_r in self._ripples:
            max_r = 92.0
            prog  = _clamp_f((rip_r - R_CORE) / (max_r - R_CORE), 0.0, 1.0)
            fade  = 1.0 - prog           # always in [0,1], safe for all ops
            a = _ci(fade * fade * 95)   # smooth quadratic fade, no pow(frac)
            pen = QPen(_c(r, g, b, a))
            pen.setWidthF(1.4)
            p.setPen(pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(QPointF(cx, cy), rip_r, rip_r)
 
        self._glow(p, cx, cy, _clamp_f(62 + amp * 38), _ci(25 + amp * 48), r, g, b)
 
        base_r = R_CORE - 2 + amp * 22
        self._blob_core(p, cx, cy, base_r, (r, g, b), (gr, gg, gb),
                        lobes=int(round(self._lobes_f)),
                        amp=self._amp_f * (0.6 + amp * 0.9), speed=1.8)
 
        if amp > 0.68:
            flash_a = _ci((amp - 0.68) / 0.32 * 185)
            self._soft_dot(p, cx, cy - base_r * 0.28, 7, 255, 255, 255, flash_a)
 
    def _draw_error(self, p: QPainter, cx: float, cy: float):
        r, g, b = self._pr, self._pg, self._pb
        gr, gg, gb = self._gr, self._gg, self._gb
 
        pulse = 0.5 + 0.5 * math.sin(self._tick * math.pi / 13)
        # Never go negative — no fractional pow on this value
        pulse = _clamp_f(pulse, 0.0, 1.0)
 
        # Warning rings
        for ring_r, ring_a_mul in [
            (54 + pulse * 15, self._flicker * 135),
            (40 + pulse *  8, self._flicker *  65),
        ]:
            pen = QPen(_c(r, g, b, _ci(ring_a_mul)))
            pen.setWidth(2)
            p.setPen(pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(QPointF(cx, cy), ring_r, ring_r)
 
        glow_a = _ci(self._flicker * (36 + pulse * 44))
        self._glow(p, cx, cy, 74, glow_a, r, g, b)
 
        # Flickered colours — multiply, never go negative
        fr  = _clamp_f(r  * self._flicker)
        fg  = _clamp_f(g  * self._flicker)
        fb  = _clamp_f(b  * self._flicker)
        fgr = _clamp_f(gr * self._flicker)
        fgg = _clamp_f(gg * self._flicker)
        fgb = _clamp_f(gb * self._flicker)
 
        base_r = R_CORE - 8 + pulse * 12
        self._blob_core(p, cx, cy, base_r, (fr, fg, fb), (fgr, fgg, fgb),
                        lobes=int(round(self._lobes_f)),
                        amp=self._amp_f * (0.7 + pulse * 0.6), speed=3.5)
 
        if pulse > 0.84:
            spike_a = _ci((pulse - 0.84) / 0.16 * 230)
            self._soft_dot(p, cx, cy, 13, 255, 210, 210, spike_a)
 
    # ═════════════════════════════════════════════════════════════════════════
    # DRAWING PRIMITIVES
    # ═════════════════════════════════════════════════════════════════════════
 
    def _blob_core(self, p: QPainter, cx: float, cy: float,
                   base_r: float, color: tuple, glow_color: tuple,
                   lobes: int, amp: float, speed: float):
        """
        Draws the orb as a morphing blob — multiple translucent layers
        at slightly different sizes and opacities so the edge bleeds
        outward rather than being a hard boundary.
        """
        r, g, b = color
        gr, gg, gb = glow_color
 
        # Layer stack: (scale_mul, center_alpha, edge_alpha)
        # Outermost layers are large + very transparent → glow bleed
        # Inner layers are smaller + more opaque → apparent core
        layers = [
            (1.55, 0,   8),
            (1.30, 0,  18),
            (1.12, 8,  35),
            (1.00, 60, 80),
            (0.82, 90, 50),
        ]
 
        for scale, a_center, a_edge in layers:
            lr = base_r * scale
            if lr < 1:
                continue
 
            path = _blob_path(cx, cy, lr, lobes, amp * scale, self._tick, speed)
 
            # Radial gradient fitted to blob's bounding box (approx circle)
            grad = QRadialGradient(
                cx - lr * 0.25, cy - lr * 0.25,   # focus offset → specular
                lr * 1.4,                           # radius covers full blob
            )
 
            if scale <= 1.0:
                # Core layers: bright specular + colour body
                grad.setColorAt(0.00, _c(min(r + 130, 255),
                                         min(g + 130, 255),
                                         min(b + 130, 255), a_center + 90))
                grad.setColorAt(0.40, _c(r, g, b, a_center + 40))
                grad.setColorAt(0.75, _c(r * 0.6, g * 0.6, b * 0.6, a_edge))
                grad.setColorAt(1.00, _c(gr, gg, gb, 0))
            else:
                # Outer halo layers: pure glow bleed, no hard centre
                grad.setColorAt(0.00, _c(r, g, b, a_center))
                grad.setColorAt(0.50, _c(r, g, b, a_edge // 2))
                grad.setColorAt(1.00, _c(gr, gg, gb, 0))
 
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(grad))
            p.drawPath(path)
 
    def _glow(self, p: QPainter, cx: float, cy: float,
              radius, alpha, r, g, b):
        """Large soft radial bloom — orb 'floats' in its own light."""
        rad = float(radius)
        grad = QRadialGradient(cx, cy, rad)
        grad.setColorAt(0.0, _c(r, g, b, alpha))
        grad.setColorAt(1.0, _c(r, g, b, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(grad))
        p.drawEllipse(QPointF(cx, cy), rad, rad)
 
    def _soft_dot(self, p: QPainter, x: float, y: float,
                  radius: float, r, g, b, alpha: int):
        """Plasma mote — bright core, transparent edge."""
        grad = QRadialGradient(x, y, radius)
        grad.setColorAt(0.0, _c(min(r + 85, 255), min(g + 85, 255), min(b + 85, 255), alpha))
        grad.setColorAt(0.5, _c(r, g, b, _ci(alpha * 0.6)))
        grad.setColorAt(1.0, _c(r, g, b, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(grad))
        p.drawEllipse(QPointF(x, y), radius, radius)
 
    # ═════════════════════════════════════════════════════════════════════════
    # INPUT EVENTS
    # ═════════════════════════════════════════════════════════════════════════
 
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_anchor = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )
 
    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.move(
                event.globalPosition().toPoint()
                - self._drag_anchor
            )


    def mouseDoubleClickEvent(self, event):

        if event.button() == Qt.MouseButton.RightButton:
            self.close()
            return

        states = list(AssistantState)

        cur = self.sm.state

        nxt = states[
            (states.index(cur) + 1) % len(states)
        ]

        self.sm.set_state(nxt)


    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()