from __future__ import annotations

import unittest

import cv2
import numpy as np

from lane_detector import LaneDetector, LaneDetectorConfig, draw_lane_overlay


FRAME_SHAPE = (480, 640, 3)
CYAN_BGR = (220, 220, 35)
GREEN_BGR = (80, 220, 80)


def lane_frame(lines: list[tuple[int, int]], *, color=CYAN_BGR) -> np.ndarray:
    frame = np.zeros(FRAME_SHAPE, dtype=np.uint8)
    frame[:, :] = (22, 22, 24)
    for x_lower, x_upper in lines:
        cv2.line(frame, (x_upper, 180), (x_lower, 440), color, 14, cv2.LINE_AA)
    return frame


def blank_frame() -> np.ndarray:
    frame = np.zeros(FRAME_SHAPE, dtype=np.uint8)
    frame[:, :] = (22, 22, 24)
    return frame


def partial_right_lane_frame() -> np.ndarray:
    frame = blank_frame()
    cv2.line(frame, (-18, 300), (22, 210), CYAN_BGR, 10, cv2.LINE_AA)
    cv2.line(frame, (96, 468), (205, 168), CYAN_BGR, 18, cv2.LINE_AA)
    cv2.line(frame, (692, 440), (542, 168), CYAN_BGR, 16, cv2.LINE_AA)
    return frame


def curved_lane_frame() -> np.ndarray:
    frame = blank_frame()
    ys = np.linspace(178, 442, 18)
    left = np.array([[235 + 0.0018 * (y - 310) ** 2, y] for y in ys], dtype=np.int32)
    right = np.array([[470 + 0.0015 * (y - 310) ** 2, y] for y in ys], dtype=np.int32)
    cv2.polylines(frame, [left], False, CYAN_BGR, 16, cv2.LINE_AA)
    cv2.polylines(frame, [right], False, CYAN_BGR, 16, cv2.LINE_AA)
    return frame


class LaneDetectorTest(unittest.TestCase):
    def config(self) -> LaneDetectorConfig:
        return LaneDetectorConfig(
            smoothing_alpha=1.0,
            min_confidence=0.25,
            stale_sec=0.30,
            expected_lane_width_ratio=0.38,
        )

    def test_centered_lane_has_small_correction(self):
        detector = LaneDetector(self.config())

        guidance = detector.detect(lane_frame([(205, 250), (435, 390)]), now=1.0)

        self.assertTrue(guidance.detected)
        self.assertEqual(guidance.source, "pair")
        self.assertLess(abs(guidance.correction), 0.04)
        self.assertAlmostEqual(guidance.lane_width, 230 / 640, delta=0.08)

    def test_lane_center_to_right_commands_right_correction(self):
        detector = LaneDetector(self.config())

        guidance = detector.detect(lane_frame([(300, 320), (570, 520)]), now=1.0)

        self.assertTrue(guidance.detected)
        self.assertGreater(guidance.center_error, 0.0)
        self.assertLess(guidance.correction, -0.06)

    def test_three_lines_select_corridor_containing_camera_center(self):
        detector = LaneDetector(self.config())

        guidance = detector.detect(lane_frame([(95, 150), (305, 320), (565, 515)]), now=1.0)

        self.assertTrue(guidance.detected)
        self.assertEqual(guidance.source, "pair")
        self.assertGreaterEqual(guidance.line_count, 3)
        self.assertGreater(guidance.lane_center_lower, 0.5)
        self.assertLess(guidance.correction, 0.0)

    def test_partial_edge_lane_selects_current_corridor(self):
        detector = LaneDetector(self.config())

        guidance = detector.detect(partial_right_lane_frame(), now=1.0)

        self.assertTrue(guidance.detected)
        self.assertEqual(guidance.source, "pair")
        self.assertEqual(guidance.reason, "partial-edge-lane-pair")
        self.assertGreaterEqual(guidance.line_count, 3)
        self.assertGreater(guidance.lane_center_lower, 0.5)
        self.assertLess(guidance.correction, 0.0)

    def test_preferred_right_corridor_recovers_from_opposite_lane(self):
        detector = LaneDetector(self.config())

        guidance = detector.detect(lane_frame([(95, 140), (365, 350), (575, 545)]), now=1.0)

        self.assertTrue(guidance.detected)
        self.assertEqual(guidance.reason, "preferred-right-lane-pair")
        self.assertGreater(guidance.lane_center_lower, 0.7)
        self.assertLess(guidance.correction, -0.25)

    def test_curved_lane_stays_detected(self):
        detector = LaneDetector(self.config())

        guidance = detector.detect(curved_lane_frame(), now=1.0)

        self.assertTrue(guidance.detected)
        self.assertEqual(guidance.source, "pair")
        self.assertLess(abs(guidance.center_error), 0.12)
        self.assertLess(abs(guidance.correction), 0.18)

    def test_single_line_uses_recent_lane_width_with_lower_confidence(self):
        detector = LaneDetector(self.config())
        first = detector.detect(lane_frame([(210, 250), (450, 405)]), now=1.0)
        self.assertTrue(first.detected)

        guidance = detector.detect(lane_frame([(450, 405)], color=GREEN_BGR), now=1.1)

        self.assertTrue(guidance.detected)
        self.assertIn(guidance.source, {"single-right", "single-left"})
        self.assertGreater(guidance.confidence, 0.0)
        self.assertLess(guidance.confidence, first.confidence)

    def test_recent_memory_expires_from_original_detection(self):
        detector = LaneDetector(self.config())
        first = detector.detect(lane_frame([(210, 250), (450, 405)]), now=1.0)
        self.assertTrue(first.detected)

        recent = detector.detect(blank_frame(), now=1.1)
        expired = detector.detect(blank_frame(), now=1.31)

        self.assertTrue(recent.detected)
        self.assertEqual(recent.source, "memory")
        self.assertFalse(expired.detected)
        self.assertEqual(expired.source, "none")

    def test_overlay_preserves_frame_shape(self):
        config = self.config()
        detector = LaneDetector(config)
        frame = lane_frame([(205, 250), (435, 390)])
        guidance = detector.detect(frame, now=1.0)

        overlay = draw_lane_overlay(frame, guidance, config)

        self.assertEqual(overlay.shape, frame.shape)


if __name__ == "__main__":
    unittest.main()
