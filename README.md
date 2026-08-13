# OMR Evaluator

A web-based Optical Mark Recognition (OMR) system that scores multiple-choice answer sheets from scanned images. Upload one or more OMR sheet photos and a CSV answer key; the app detects filled bubbles, compares them to the key, and returns per-student scores.

## Features

- Upload multiple answer-sheet images in one batch
- Upload a CSV answer key with per-question marks
- Automatic bubble detection using OpenCV
- Perspective correction for skewed or angled photos
- Score calculation with support for multi-select questions
- Downloadable results CSV

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python, Flask |
| Image processing | OpenCV, NumPy, imutils |
| Data | pandas |
| Frontend | HTML, CSS, JavaScript |

## Project Structure

```
omr_evaluation/
├── app.py              # Flask server and upload/evaluate routes
├── omr.py              # OMR image processing and scoring logic
├── main.html           # Web UI
├── static/
│   ├── main.css        # Page layout and styling
│   ├── upload.css      # Upload panel styling
│   ├── upload.js       # File upload and evaluate flow
│   ├── omr_sheets/     # Uploaded answer-sheet images (temporary)
│   ├── answer_sheet/   # Uploaded answer key CSV (temporary)
│   └── result/         # Generated score CSV files
├── test/               # Sample answer key CSV
├── requirements.txt    # Python dependencies
├── Dockerfile          # Container deployment
└── IMAGE_PROCESSING.md # Detailed image-processing pipeline docs
```

## Prerequisites

- Python 3.11+
- pip

## Installation

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd omr_evaluation
   ```

2. Create and activate a virtual environment (recommended):

   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS / Linux
   source venv/bin/activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Running Locally

Start the Flask server:

```bash
python app.py
```

Open [http://localhost:5000](http://localhost:5000) in your browser.

### Usage

1. **Upload answer sheets** — Select one or more OMR sheet images (PNG, JPG, JPEG) and click **Upload Sheets**.
2. **Upload answer key** — Select a CSV file with the correct answers and click **Upload Key**.
3. **Evaluate** — Click **Evaluate** to run OMR processing and view scores.
4. **Download** — Use the download link to save the results CSV.

## Answer Key CSV Format

The answer key must be a CSV with these columns:

| Column | Description |
|--------|-------------|
| `qno` | Question number |
| `answer` | Correct option(s). Single answer: `2`. Multiple answers: `1,3` |
| `marks` | Points awarded for a fully correct response |

Example (`test/Ques.csv`):

```csv
qno,answer,marks
1,2,5
2,1,5
3,4,5
```

## API Endpoints

| Method | Route | Description |
|--------|-------|-------------|
| `GET` | `/` | Serve the web UI |
| `POST` | `/upload` | Upload images (`file1`) or answer key CSV (`file2`) |
| `GET` | `/load` | Run OMR evaluation and return scores |

## Docker

Build and run with Docker:

```bash
docker build -t omr-evaluator .
docker run -p 5000:5000 omr-evaluator
```

The app listens on port `5000` by default. Override with the `PORT` environment variable.

## How It Works

The OMR pipeline:

1. Detects rectangular sections on the sheet using edge detection and contour analysis
2. Applies a perspective transform to flatten each section
3. Thresholds each section to isolate filled bubbles
4. Compares detected marks against the CSV answer key
5. Writes scores to `static/result/ans_<timestamp>.csv`

For a step-by-step breakdown of each OpenCV operation, see [IMAGE_PROCESSING.md](IMAGE_PROCESSING.md).

## Limitations

- Designed for a specific OMR sheet layout (fixed column positions and section count)
- Works best with clear, well-lit photos and minimal skew
- Sheet sections shorter than 50 px (after warp) are skipped
- Uploaded files are removed after evaluation

## License

See the repository for license details.
