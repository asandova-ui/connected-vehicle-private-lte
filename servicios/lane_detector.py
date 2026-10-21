from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Sequence

import cv2
import numpy as np


@dataclass(frozen=True)
class LaneDetectorConfig:
    enabled: bool = True
    roi_top_ratio: float = 0.34
    roi_bottom_margin_ratio: float = 0.02
    target_center_x: float = 0.50
    lower_sample_y: float = 0.86
    upper_sample_y: float = 0.58
    hsv_lower: tuple[int, int, int] = (42, 45, 55)
    hsv_upper: tuple[int, int, int] = (105, 255, 255)
    road_gray_max: int = 125
    road_context_dilate_px: int = 33
    close_kernel: tuple[int, int] = (7, 19)
    open_kernel: tuple[int, int] = (3, 5)
    min_component_area_ratio: float = 0.00016
    min_line_height_ratio: float = 0.11
    max_fit_error_ratio: float = 0.055
    max_curve_fit_error_ratio: float = 0.12
    cluster_px_ratio: float = 0.055
    min_lane_width_ratio: float = 0.18
    max_lane_width_ratio: float = 0.72
    max_partial_lane_width_ratio: float = 0.92
    expected_lane_width_ratio: float = 0.38
    preferred_corridor: str = "right"
    preferred_corridor_bonus: float = 1.05
    single_line_confidence_scale: float = 0.58
    stale_sec: float = 0.45
    min_confidence: float = 0.34
    steering_gain: float = 2.10
    heading_gain: float = 0.80
    max_correction: float = 0.75
    smoothing_alpha: float = 0.75
    departure_center_error: float = 0.16
    recovery_correction_scale: float = 1.55


@dataclass(frozen=True)
class LaneLine:
    x_lower: float
    x_upper: float
    y_min: float
    y_max: float
    area: float
    height: float
    fit_error: float
    confidence: float

    def to_status(self) -> dict[str, Any]:
        return {
            "x_lower": round(self.x_lower, 4),
            "x_upper": round(self.x_upper, 4),
            "y_min": round(self.y_min, 4),
            "y_max": round(self.y_max, 4),
            "area": round(self.area, 5),
            "height": round(self.height, 4),
            "fit_error": round(self.fit_error, 4),
            "confidence": round(self.confidence, 3),
        }


@dataclass(frozen=True)
class LaneGuidance:
    detected: bool
    confidence: float
    correction: float
    center_error: float
    heading_error: float
    lane_center_lower: float | None
    lane_center_upper: float | None
    lane_width: float | None
    line_count: int
    source: str
    reason: str
    age_sec: float = 0.0
    lines: tuple[LaneLine, ...] = ()

    def is_usable(self, config: LaneDetectorConfig, *, now: float | None = None, detected_at: float | None = None) -> bool:
        age = self.age_sec
        if now is not None and detected_at is not None:
            age = max(0.0, now - detected_at)
        return (
            self.detected
            and age <= config.stale_sec
            and self.confidence >= config.min_confidence
            and abs(self.correction) <= config.max_correction + 0.001
        )

    def with_age(self, age_sec: float) -> LaneGuidance:
        return LaneGuidance(
            detected=self.detected,
            confidence=self.confidence,
            correction=self.correction,
            center_error=self.center_error,
            heading_error=self.heading_error,
            lane_center_lower=self.lane_center_lower,
            lane_center_upper=self.lane_center_upper,
            lane_width=self.lane_width,
            line_count=self.line_count,
            source=self.source,
            reason=self.reason,
            age_sec=age_sec,
            lines=self.lines,
        )

    def to_status(self) -> dict[str, Any]:
        return {
            "detected": self.detected,
            "confidence": round(self.confidence, 3),
            "correction": round(self.correction, 3),
            "center_error": round(self.center_error, 4),
            "heading_error": round(self.heading_error, 4),
            "lane_center_lower": rounded(self.lane_center_lower, 4),
            "lane_center_upper": rounded(self.lane_center_upper, 4),
            "lane_width": rounded(self.lane_width, 4),
            "line_count": self.line_count,
            "source": self.source,
            "reason": self.reason,
            "age_sec": round(self.age_sec, 3),
            "lines": [line.to_status() for line in self.lines[:6]],
        }


class LaneDetector:
    def __init__(self, config: LaneDetectorConfig) -> None:
        self.config = config
        self.last_guidance: LaneGuidance | None = None
        self.last_detected_at: float | None = None
        self.last_lane_width = config.expected_lane_width_ratio
        self.last_correction = 0.0

    def detect(self, frame: np.ndarray, *, now: float | None = None) -> LaneGuidance:
        now = time.time() if now is None else now
        if not self.config.enabled:
            return self._empty("disabled", now)
        if frame is None or frame.ndim < 2:
            return self._empty("invalid-frame", now)

        h, w = frame.shape[:2]
        if h < 80 or w < 80:
            return self._empty("frame-too-small", now)

        mask, roi_top, roi_bottom = build_lane_mask(frame, self.config)
        raw_lines = extract_lane_lines(mask, frame.shape, roi_top, roi_bottom, self.config)
        lines = cluster_lane_lines(raw_lines, frame.shape, self.config)
        guidance = build_guidance(lines, frame.shape, self.config)
        if guidance.detected and guidance.lane_width is not None:
            self.last_lane_width = guidance.lane_width
        elif len(lines) == 1:
            guidance = self._single_line_guidance(lines[0], frame.shape, now)

        reused_memory = False
        if not guidance.detected:
            guidance = self._reuse_recent(now, guidance.reason)
            reused_memory = guidance.detected and guidance.source == "memory"

        if guidance.detected:
            guidance = self._smooth(guidance)
            if not reused_memory:
                self.last_guidance = guidance
                self.last_detected_at = now
        else:
            self.last_correction = move_towards(self.last_correction, 0.0, self.config.max_correction)
        return guidance

    def _single_line_guidance(self, line: LaneLine, frame_shape: Sequence[int], now: float) -> LaneGuidance:
        _h, _w = frame_size(frame_shape)
        width = clamp(self.last_lane_width or self.config.expected_lane_width_ratio, 0.12, 0.80)
        target = self.config.target_center_x
        if line.x_lower <= target:
            center_lower = line.x_lower + width / 2.0
            center_upper = line.x_upper + width / 2.0
            source = "single-left"
        else:
            center_lower = line.x_lower - width / 2.0
            center_upper = line.x_upper - width / 2.0
            source = "single-right"
        center_lower = clamp(center_lower, 0.0, 1.0)
        center_upper = clamp(center_upper, 0.0, 1.0)
        center_error = center_lower - target
        heading_error = center_upper - center_lower
        correction = steering_correction(center_error, heading_error, self.config)
        confidence = clamp(line.confidence * self.config.single_line_confidence_scale, 0.0, 0.74)
        return LaneGuidance(
            detected=confidence >= self.config.min_confidence * 0.75,
            confidence=confidence,
            correction=correction,
            center_error=center_error,
            heading_error=heading_error,
            lane_center_lower=center_lower,
            lane_center_upper=center_upper,
            lane_width=width,
            line_count=1,
            source=source,
            reason="single-line-estimate",
            age_sec=0.0,
            lines=(line,),
        )

    def _reuse_recent(self, now: float, reason: str) -> LaneGuidance:
        if self.last_guidance is None or self.last_detected_at is None:
            return self._empty(reason, now)
        age = max(0.0, now - self.last_detected_at)
        if age > self.config.stale_sec:
            return self._empty(reason, now)
        faded = max(0.0, 1.0 - age / max(self.config.stale_sec, 0.001))
        reused = LaneGuidance(
            detected=True,
            confidence=self.last_guidance.confidence * faded,
            correction=self.last_guidance.correction * faded,
            center_error=self.last_guidance.center_error,
            heading_error=self.last_guidance.heading_error,
            lane_center_lower=self.last_guidance.lane_center_lower,
            lane_center_upper=self.last_guidance.lane_center_upper,
            lane_width=self.last_guidance.lane_width,
            line_count=self.last_guidance.line_count,
            source="memory",
            reason=f"recent-lane-memory:{reason}",
            age_sec=age,
            lines=self.last_guidance.lines,
        )
        return reused

    def _smooth(self, guidance: LaneGuidance) -> LaneGuidance:
        alpha = clamp(self.config.smoothing_alpha, 0.0, 1.0)
        correction = alpha * guidance.correction + (1.0 - alpha) * self.last_correction
        correction = clamp(correction, -self.config.max_correction, self.config.max_correction)
        self.last_correction = correction
        return LaneGuidance(
            detected=guidance.detected,
            confidence=guidance.confidence,
            correction=correction,
            center_error=guidance.center_error,
            heading_error=guidance.heading_error,
            lane_center_lower=guidance.lane_center_lower,
            lane_center_upper=guidance.lane_center_upper,
            lane_width=guidance.lane_width,
            line_count=guidance.line_count,
            source=guidance.source,
            reason=guidance.reason,
            age_sec=guidance.age_sec,
            lines=guidance.lines,
        )

    def _empty(self, reason: str, now: float) -> LaneGuidance:
        if self.last_detected_at is not None:
            age = max(0.0, now - self.last_detected_at)
        else:
            age = 0.0
        return LaneGuidance(
            detected=False,
            confidence=0.0,
            correction=0.0,
            center_error=0.0,
            heading_error=0.0,
            lane_center_lower=None,
            lane_center_upper=None,
            lane_width=None,
            line_count=0,
            source="none",
            reason=reason,
            age_sec=age,
            lines=(),
        )


def build_lane_mask(
    frame: np.ndarray,
    config: LaneDetectorConfig,
) -> tuple[np.ndarray, int, int]:
    h, w = frame.shape[:2]
    roi_top = int(round(clamp(config.roi_top_ratio, 0.0, 0.9) * h))
    roi_bottom = int(round((1.0 - clamp(config.roi_bottom_margin_ratio, 0.0, 0.35)) * h))
    roi_bottom = max(roi_top + 1, min(h, roi_bottom))

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    lower = np.array(config.hsv_lower, dtype=np.uint8)
    upper = np.array(config.hsv_upper, dtype=np.uint8)
    color_mask = cv2.inRange(hsv, lower, upper)

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    road_mask = cv2.inRange(gray, 0, int(clamp(config.road_gray_max, 0, 255)))
    dilate_px = max(3, int(config.road_context_dilate_px))
    if dilate_px % 2 == 0:
        dilate_px += 1
    road_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (dilate_px, dilate_px))
    road_context = cv2.dilate(road_mask, road_kernel, iterations=1)

    mask = cv2.bitwise_and(color_mask, road_context)
    roi_mask = np.zeros_like(mask)
    roi_mask[roi_top:roi_bottom, :] = 255
    mask = cv2.bitwise_and(mask, roi_mask)

    close_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, tuple_int(config.close_kernel, (7, 19)))
    open_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, tuple_int(config.open_kernel, (3, 5)))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, close_kernel, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, open_kernel, iterations=1)
    return mask, roi_top, roi_bottom


def extract_lane_lines(
    mask: np.ndarray,
    frame_shape: Sequence[int],
    roi_top: int,
    roi_bottom: int,
    config: LaneDetectorConfig,
) -> list[LaneLine]:
    h, w = frame_size(frame_shape)
    if h <= 0 or w <= 0:
        return []

    min_area = max(8.0, config.min_component_area_ratio * h * w)
    min_height = max(12.0, config.min_line_height_ratio * h)
    max_fit_error_px = max(5.0, config.max_fit_error_ratio * w)
    max_curve_fit_error_px = max(max_fit_error_px, config.max_curve_fit_error_ratio * w)
    lower_y = clamp(config.lower_sample_y, 0.0, 1.0) * h
    upper_y = clamp(config.upper_sample_y, 0.0, 1.0) * h

    contours, _hierarchy = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    lines: list[LaneLine] = []
    for contour in contours:
        area = float(cv2.contourArea(contour))
        if area < min_area:
            continue
        x, y, bw, bh = cv2.boundingRect(contour)
        if bh < min_height or bw <= 0:
            continue
        if y + bh < roi_top or y > roi_bottom:
            continue

        points = contour.reshape(-1, 2).astype(np.float64)
        if len(points) < 12:
            continue
        xs = points[:, 0]
        ys = points[:, 1]
        try:
            slope, intercept = np.polyfit(ys, xs, 1)
        except (TypeError, ValueError, np.linalg.LinAlgError):
            continue
        fitted = slope * ys + intercept
        fit_error = float(np.median(np.abs(xs - fitted)))
        if fit_error > max_curve_fit_error_px:
            continue

        x_lower = sample_line_x(points, lower_y, slope, intercept, h, w)
        x_upper = sample_line_x(points, upper_y, slope, intercept, h, w)
        height_ratio = clamp(bh / h, 0.0, 1.0)
        area_ratio = clamp(area / float(h * w), 0.0, 1.0)
        curved_fit = fit_error > max_fit_error_px
        fit_limit = max_curve_fit_error_px if curved_fit else max_fit_error_px
        fit_score = 1.0 - clamp(fit_error / fit_limit, 0.0, 1.0)
        confidence = clamp(0.20 + height_ratio * 1.35 + min(0.25, area_ratio * 35.0) + fit_score * 0.20, 0.0, 1.0)
        if curved_fit:
            confidence = clamp(confidence * 0.78, 0.0, 1.0)
        lines.append(
            LaneLine(
                x_lower=x_lower,
                x_upper=x_upper,
                y_min=clamp(float(np.min(ys)) / h, 0.0, 1.0),
                y_max=clamp(float(np.max(ys)) / h, 0.0, 1.0),
                area=area_ratio,
                height=height_ratio,
                fit_error=fit_error / w,
                confidence=confidence,
            )
        )
    lines.sort(key=lambda item: item.x_lower)
    return lines


def cluster_lane_lines(
    lines: list[LaneLine],
    frame_shape: Sequence[int],
    config: LaneDetectorConfig,
) -> tuple[LaneLine, ...]:
    if not lines:
        return ()
    _h, w = frame_size(frame_shape)
    cluster_distance = max(0.02, config.cluster_px_ratio)
    clusters: list[list[LaneLine]] = []
    for line in sorted(lines, key=lambda item: item.x_lower):
        if not clusters or abs(line.x_lower - clusters[-1][-1].x_lower) > cluster_distance:
            clusters.append([line])
        else:
            clusters[-1].append(line)

    merged: list[LaneLine] = []
    for cluster in clusters:
        total = sum(max(0.001, line.confidence) for line in cluster)
        x_lower = sum(line.x_lower * line.confidence for line in cluster) / total
        x_upper = sum(line.x_upper * line.confidence for line in cluster) / total
        best = max(cluster, key=lambda item: item.confidence)
        merged.append(
            LaneLine(
                x_lower=clamp(x_lower, 0.0, 1.0),
                x_upper=clamp(x_upper, 0.0, 1.0),
                y_min=min(line.y_min for line in cluster),
                y_max=max(line.y_max for line in cluster),
                area=sum(line.area for line in cluster),
                height=max(line.height for line in cluster),
                fit_error=min(line.fit_error for line in cluster),
                confidence=clamp(best.confidence + 0.05 * (len(cluster) - 1), 0.0, 1.0),
            )
        )
    merged.sort(key=lambda item: item.x_lower)
    return tuple(merged[:6])


def build_guidance(
    lines: Sequence[LaneLine],
    frame_shape: Sequence[int],
    config: LaneDetectorConfig,
) -> LaneGuidance:
    if len(lines) < 2:
        return empty_guidance("need-two-lines", tuple(lines))

    target = config.target_center_x
    adjacent_pairs = list(zip(lines, lines[1:]))
    pairs: list[tuple[float, LaneLine, LaneLine, float, str, float, bool]] = []
    for pair_index, (left, right) in enumerate(adjacent_pairs):
        width = right.x_lower - left.x_lower
        if width < config.min_lane_width_ratio:
            continue
        center = (left.x_lower + right.x_lower) / 2.0
        brackets_target = left.x_lower <= target <= right.x_lower
        edge_partial = brackets_target and (
            left.x_lower <= 0.04
            or left.x_upper <= 0.05
            or right.x_lower >= 0.96
            or right.x_upper >= 0.95
        )
        max_width = (
            config.max_partial_lane_width_ratio
            if edge_partial
            else config.max_lane_width_ratio
        )
        if width > max_width:
            continue
        reason = "partial-edge-lane-pair" if width > config.max_lane_width_ratio else "lane-pair"
        bracket_penalty = 0.0 if brackets_target else 0.65
        width_penalty = abs(width - config.expected_lane_width_ratio) * (0.10 if edge_partial else 0.20)
        confidence_bonus = -0.05 * min(left.confidence, right.confidence)
        preference_bonus = corridor_preference_bonus(pair_index, len(adjacent_pairs), config)
        score = bracket_penalty + abs(center - target) + width_penalty + confidence_bonus - preference_bonus
        pairs.append((score, left, right, width, reason, preference_bonus, brackets_target))

    if not pairs:
        return empty_guidance("no-plausible-lane-width", tuple(lines))

    _score, left, right, width, reason, preference_bonus, brackets_target = min(pairs, key=lambda item: item[0])
    if (
        reason == "lane-pair"
        and preference_bonus > 0.0
        and not brackets_target
        and normalize_corridor(config.preferred_corridor) != "auto"
    ):
        reason = f"preferred-{normalize_corridor(config.preferred_corridor)}-lane-pair"
    center_lower = (left.x_lower + right.x_lower) / 2.0
    center_upper = (left.x_upper + right.x_upper) / 2.0
    center_error = center_lower - target
    heading_error = center_upper - center_lower
    correction = steering_correction(center_error, heading_error, config)
    width_score = 1.0 - min(
        1.0,
        abs(width - config.expected_lane_width_ratio)
        / max(config.expected_lane_width_ratio, 0.001),
    )
    confidence = clamp(
        0.16 + (left.confidence + right.confidence) * 0.34 + width_score * 0.16,
        0.0,
        1.0,
    )
    return LaneGuidance(
        detected=confidence >= config.min_confidence * 0.70,
        confidence=confidence,
        correction=correction,
        center_error=center_error,
        heading_error=heading_error,
        lane_center_lower=center_lower,
        lane_center_upper=center_upper,
        lane_width=width,
        line_count=len(lines),
        source="pair",
        reason=reason,
        age_sec=0.0,
        lines=tuple(lines),
    )


def sample_line_x(
    points: np.ndarray,
    sample_y: float,
    slope: float,
    intercept: float,
    frame_h: int,
    frame_w: int,
) -> float:
    if frame_h <= 0 or frame_w <= 0 or len(points) == 0:
        return 0.0

    xs = points[:, 0]
    ys = points[:, 1]
    band = max(6.0, frame_h * 0.025)
    selected = np.abs(ys - sample_y) <= band
    if not np.any(selected):
        nearest_y = ys[int(np.argmin(np.abs(ys - sample_y)))]
        selected = np.abs(ys - nearest_y) <= band
    if np.any(selected):
        return clamp(float(np.median(xs[selected])) / frame_w, 0.0, 1.0)
    return clamp((slope * sample_y + intercept) / frame_w, 0.0, 1.0)


def draw_lane_overlay(
    frame: np.ndarray,
    guidance: LaneGuidance | None,
    config: LaneDetectorConfig,
) -> np.ndarray:
    if guidance is None or not config.enabled:
        return frame
    output = frame.copy()
    h, w = output.shape[:2]
    roi_top = int(round(clamp(config.roi_top_ratio, 0.0, 0.9) * h))
    lower_y = int(round(clamp(config.lower_sample_y, 0.0, 1.0) * h))
    upper_y = int(round(clamp(config.upper_sample_y, 0.0, 1.0) * h))

    cv2.line(output, (0, roi_top), (w - 1, roi_top), (80, 80, 80), 1, cv2.LINE_AA)
    for line in guidance.lines:
        p1 = (int(round(line.x_lower * w)), lower_y)
        p2 = (int(round(line.x_upper * w)), upper_y)
        cv2.line(output, p1, p2, (80, 255, 220), 3, cv2.LINE_AA)
        cv2.circle(output, p1, 4, (30, 180, 255), -1, cv2.LINE_AA)

    target_x = int(round(config.target_center_x * w))
    cv2.line(output, (target_x, lower_y - 28), (target_x, lower_y + 28), (245, 245, 245), 2, cv2.LINE_AA)
    if guidance.lane_center_lower is not None and guidance.lane_center_upper is not None:
        center_lower = (int(round(guidance.lane_center_lower * w)), lower_y)
        center_upper = (int(round(guidance.lane_center_upper * w)), upper_y)
        color = (32, 210, 120) if guidance.detected else (90, 150, 150)
        cv2.line(output, center_lower, center_upper, color, 3, cv2.LINE_AA)
        cv2.circle(output, center_lower, 5, color, -1, cv2.LINE_AA)

    label = (
        f"lane {guidance.source} conf={guidance.confidence:.2f} "
        f"corr={guidance.correction:+.2f}"
    )
    cv2.putText(
        output,
        label[:96],
        (12, min(h - 16, max(24, roi_top + 24))),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.54,
        (20, 20, 20),
        3,
        cv2.LINE_AA,
    )
    cv2.putText(
        output,
        label[:96],
        (12, min(h - 16, max(24, roi_top + 24))),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.54,
        (230, 255, 245),
        1,
        cv2.LINE_AA,
    )
    return output


def steering_correction(center_error: float, heading_error: float, config: LaneDetectorConfig) -> float:
    correction = -config.steering_gain * center_error - config.heading_gain * heading_error
    if abs(center_error) >= config.departure_center_error:
        correction *= max(1.0, config.recovery_correction_scale)
    return clamp(correction, -config.max_correction, config.max_correction)


def corridor_preference_bonus(
    pair_index: int,
    pair_count: int,
    config: LaneDetectorConfig,
) -> float:
    if pair_count < 2:
        return 0.0
    preferred = normalize_corridor(config.preferred_corridor)
    bonus = max(0.0, config.preferred_corridor_bonus)
    scale = max(1, pair_count - 1)
    if preferred == "right":
        return bonus * (pair_index / scale)
    if preferred == "left":
        return bonus * ((pair_count - 1 - pair_index) / scale)
    if preferred == "center":
        middle = (pair_count - 1) / 2.0
        return bonus * (1.0 - min(1.0, abs(pair_index - middle) / max(middle, 1.0)))
    return 0.0


def normalize_corridor(value: str | None) -> str:
    normalized = str(value or "auto").strip().lower()
    if normalized in {"left", "right", "center"}:
        return normalized
    return "auto"


def empty_guidance(reason: str, lines: tuple[LaneLine, ...] = ()) -> LaneGuidance:
    return LaneGuidance(
        detected=False,
        confidence=0.0,
        correction=0.0,
        center_error=0.0,
        heading_error=0.0,
        lane_center_lower=None,
        lane_center_upper=None,
        lane_width=None,
        line_count=len(lines),
        source="none",
        reason=reason,
        age_sec=0.0,
        lines=lines,
    )


def tuple_int(value: tuple[int, int], default: tuple[int, int]) -> tuple[int, int]:
    try:
        a, b = value
        a = max(1, int(a))
        b = max(1, int(b))
        return a, b
    except (TypeError, ValueError):
        return default


def frame_size(frame_shape: Sequence[int] | None) -> tuple[int, int]:
    if frame_shape is None or len(frame_shape) < 2:
        return 0, 0
    try:
        return int(frame_shape[0]), int(frame_shape[1])
    except (TypeError, ValueError):
        return 0, 0


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, float(value)))


def move_towards(current: float, target: float, step: float) -> float:
    if abs(target - current) <= step:
        return target
    return current + step if target > current else current - step


def rounded(value: float | None, digits: int) -> float | None:
    return None if value is None else round(value, digits)
