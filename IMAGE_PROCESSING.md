# Image Processing Pipeline

This document explains how the OMR evaluator processes scanned answer-sheet images. All logic lives in `omr.py` and uses [OpenCV](https://opencv.org/) for computer vision operations.

## Overview

```
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐    ┌──────────────┐
│ Load Image  │───▶│ Preprocess   │───▶│ Find Sections   │───▶│ Read Bubbles │
│  (BGR)      │    │ Gray/Blur/   │    │ Contours +      │    │ Threshold +  │
│             │    │ Edge Detect  │    │ Perspective     │    │ Ratio Check  │
└─────────────┘    └──────────────┘    └─────────────────┘    └──────────────┘
                                                                        │
                                                                        ▼
                                                               ┌──────────────┐
                                                               │ Score vs CSV │
                                                               │  Answer Key  │
                                                               └──────────────┘
```

## Step 1: Load and Preprocess

**Function:** `main(image_path)`

The pipeline starts by loading the image and preparing it for contour detection.

| Step | OpenCV call | Purpose |
|------|-------------|---------|
| Load | `cv2.imread()` | Read the image in BGR color space |
| Grayscale | `cv2.cvtColor(..., COLOR_BGR2GRAY)` | Reduce to one channel for simpler processing |
| Blur | `cv2.GaussianBlur(gray, (3, 3), 0)` | Smooth noise so edges are cleaner |
| Edge detect | `cv2.Canny(blurred, 75, 200)` | Highlight boundaries (sheet edges, section boxes) |

```python
image = cv2.imread(image_path)
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
blurred = cv2.GaussianBlur(gray, (3, 3), 0)
edged = cv2.Canny(blurred, 75, 200)
```

**Why Canny?** Canny edge detection finds strong intensity gradients. OMR sheets have dark borders around each answer block; those borders produce clear edges against the white background.

**Parameters:**
- Gaussian kernel `(3, 3)` — small blur preserves section corners while reducing speckle noise
- Canny thresholds `75` and `200` — lower bound for weak edges, upper bound for strong edges; only strong edges above the high threshold are kept unless connected to a strong edge

---

## Step 2: Find Document Contours

**Function:** `get_main_countours(image)`

This step locates quadrilateral regions on the sheet — each OMR answer block.

```python
cnts = cv2.findContours(image.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
cnts = imutils.grab_contours(cnts)
```

| Flag | Meaning |
|------|---------|
| `RETR_EXTERNAL` | Only outermost contours (ignores holes inside a region) |
| `CHAIN_APPROX_SIMPLE` | Compress contour points to save memory |

**Algorithm:**

1. Sort contours by area (largest first)
2. Compute perimeter with `cv2.arcLength(c, True)`
3. Approximate the contour to a polygon with `cv2.approxPolyDP(c, 0.02 * peri, True)`
4. Keep contours that approximate to **exactly 4 vertices** (rectangles/quadrilaterals)

The `0.02 * peri` epsilon controls approximation tightness: 2% of perimeter allows slight corner rounding while still detecting rectangles.

**Output:** A list of 4-point contours, each representing one answer section on the sheet.

---

## Step 3: Perspective Correction (Bird's-Eye View)

**Function:** `get_bird_eye_view(image, cont)`

Photos are often taken at an angle. A perspective transform flattens each quadrilateral into a front-facing rectangle so bubble positions align with fixed crop coordinates.

### 3a. Order Corner Points

**Function:** `order_points(pts)`

Corner order must be consistent: top-left, top-right, bottom-right, bottom-left.

```python
s = np.sum(pts, axis=1)       # top-left has smallest sum, bottom-right largest
diff = np.diff(pts, axis=1)   # top-right has smallest diff, bottom-left largest
```

### 3b. Four-Point Transform

**Function:** `four_point_transform(image, pts)`

1. Measure width and height from opposite edge pairs
2. Build a destination rectangle `(0,0)` → `(maxWidth, maxHeight)`
3. Compute the homography matrix with `cv2.getPerspectiveTransform(rect, dst)`
4. Warp the image with `cv2.warpPerspective(image, M, (maxWidth, maxHeight))`

**Output:** A rectified section image where bubble rows and columns map to predictable pixel regions.

**Filter:** Sections with height `< 50` pixels after warping are discarded as too small to read reliably.

---

## Step 4: Bubble Detection

The sheet layout splits into two section types, processed by separate functions:

| Function | Source section | Questions per block | Blocks |
|----------|----------------|---------------------|--------|
| `get_marks_section_2()` | `sections[2]` | 5 questions × 4 options | 2 columns |
| `get_marks_section_1()` | `sections[1]` | 2 questions × 4 options | 5 columns |

Section indices come from the order contours are detected on the sheet. The code expects at least three valid sections and uses indices `1` and `2`.

### 4a. Adaptive Thresholding

```python
thresh = cv2.adaptiveThreshold(
    image[55:, :], 255,
    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
    cv2.THRESH_BINARY_INV,
    77, 10
)
```

| Parameter | Value | Role |
|-----------|-------|------|
| Crop offset | `55:` or `30:` | Skip header/margin rows at the top of each section |
| Block size | `77` | Local neighborhood size for threshold computation |
| C | `10` | Constant subtracted from the local mean |
| `THRESH_BINARY_INV` | — | Filled bubbles become **white** (255), background **black** (0) |

Adaptive thresholding handles uneven lighting better than a single global threshold: each pixel is compared to the mean of its local neighborhood.

### 4b. Column Cropping

Each section image is split into fixed horizontal slices (bubble columns). Example for section 2:

```python
thresh1 = thresh[:, 25:110]    # left column block
thresh2 = thresh[:, 165:-30]   # right column block
```

These pixel ranges are tuned to the physical OMR template layout.

### 4c. Per-Question, Per-Option Analysis

**Function:** `get_section_ans(inp)` (nested inside each section handler)

For each question row and each option column:

1. **Crop** the sub-region for that bubble
2. **Erode** with a custom kernel to remove thin lines and isolate solid fills:

   ```python
   erode_kernel = np.array([[1, 0, 1],
                            [1, 0, 1],
                            [1, 0, 1]], dtype=np.uint8)
   t = cv2.erode(t, erode_kernel, iterations=3)
   ```

   The kernel removes vertical guide lines while preserving horizontally filled bubble marks.

3. **Compute fill ratio** — fraction of white pixels in the crop:

   ```python
   filled_ratios.append(np.sum(t / 255.0) / (t.shape[0] * t.shape[1]))
   ```

4. **Normalize** ratios within the question row so the darkest bubble stands out
5. **Mark selected** if normalized ratio `> 0.1` (section 2) or `> 0.1` with raw ratio `> 0.05` (section 1)

**Output format:** A list of lists. Each inner list holds the selected option numbers (1–4) for one question. An empty list means no bubble was marked.

Example:

```python
[[2], [1], [4], [], [3, 4], ...]
#  Q1   Q2   Q3   Q4    Q5 (multi-mark)
```

---

## Step 5: Scoring

After all sections are read, answers are merged and compared to the CSV answer key.

```python
for q, r in zip(ansmarked, answer):
    if len(q) == 0:
        continue  # unanswered — no marks
    if len(q) == len(r):
        # All selected options must match in order
        for c in range(len(q)):
            if ansmarked[curr][c] != answer[curr][c]:
                break
        else:
            score += marks[curr]  # full marks only if every option matches
```

| Rule | Behavior |
|------|----------|
| Unanswered | Skipped, 0 marks |
| Wrong count of selections | No marks (e.g., marked 2 bubbles when key has 1) |
| Partial match on multi-select | No marks — all options must match |
| Full match | Add `marks` for that question |

---

## Data Flow Summary

```
Image file
    │
    ▼
main(image_path)
    ├── get_main_countours(edged)          → list of 4-point contours
    ├── get_bird_eye_view(blurred, cont)   → rectified section images
    ├── get_marks_section_2(sections[2])   → questions from section type A
    ├── get_marks_section_1(sections[1])   → questions from section type B
    └── return { "ans_marked": [...] }
    │
    ▼
omr_calculation()
    ├── Compare ans_marked vs CSV answer key
    ├── Compute per-sheet score
    └── Write static/result/ans_<timestamp>.csv
```

---

## Tuning Guide

If detection accuracy is poor, adjust these values in `omr.py`:

| Parameter | Location | Effect |
|-----------|----------|--------|
| Canny `(75, 200)` | `main()` | Lower values detect more edges (may add noise); higher values miss faint borders |
| `0.02 * peri` | `get_main_countours()` | Increase if rectangles are not detected; decrease if non-rectangles pass |
| Min height `50` | `main()` | Raise to ignore smaller false detections |
| Threshold block size `77`, C `10` | section functions | Larger block size smooths lighting variation; adjust C to shift sensitivity |
| Column crop ranges | `thresh1`, `thresh2`, etc. | Must match your OMR template pixel layout after perspective warp |
| Ratio thresholds `0.1`, `0.05` | `get_section_ans()` | Lower = more sensitive (may pick smudges); higher = stricter |

---

## Debugging Tips

Uncomment the `display()` function inside `main()` to step through preprocessing stages:

```python
cv2.imshow('Original Image', image)
cv2.imshow('Grayscale Image', gray)
cv2.imshow('Blurred Image', blurred)
cv2.imshow('Edge-Detected Image', edged)
cv2.waitKey(0)
```

Uncomment `display2()` in `omr_calculation()` to print detected vs expected answers in the terminal.

For local development, save intermediate threshold crops with `cv2.imwrite()` to verify column alignment after perspective correction.

---

## Dependencies

| Library | Role |
|---------|------|
| **OpenCV (`cv2`)** | Image I/O, filtering, contours, thresholding, warping |
| **NumPy** | Array math for points, ratios, and transforms |
| **imutils** | `grab_contours()` — OpenCV 3/4 compatible contour extraction |
| **pandas** | Read answer key CSV |

---

## Related Files

- `omr.py` — Full implementation of the pipeline described here
- `app.py` — HTTP layer that triggers `omr_calculation()` via `/load`
- `README.md` — Setup, usage, and project overview
