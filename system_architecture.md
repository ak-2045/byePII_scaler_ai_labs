# System Architecture


## 1. Architectural Overview

The **byePII** system processes documents such as PDF, DOCX, and TXT files to identify and anonymize personally identifiable information (PII). To keep processing fast and efficient, it runs two pipelines in parallel.

The first pipeline focuses on text. It extracts document content, detects sensitive information using regular expressions and NLP models, filters false positives, replaces real values with realistic synthetic data, and rewrites the document.

The second pipeline handles images. It scans document pages and embedded images, detects sensitive identity cards such as Aadhaar and PAN cards along with company logos using OpenCV, then obscures them before the final document is generated.

Think of it as having two coworkers tackling the same document at once. One reads every word while the other inspects every image. They meet at the end, compare notes, and produce a clean, anonymized version.

### High-Level Parallel Pipeline

```mermaid
graph TD
    %% Define Nodes
    Start([Input Document: PDF, DOCX, TXT]) --> Split{Parallel Processing}
    
    %% Left Branch: Text Redaction & Extraction
    Split -->|Branch 1: Text Processing| TextExt[Text Extraction]
    TextExt --> DetectPII[Extraction of Sensitive Info <br> Regex & spaCy / Presidio]
    
    DetectPII --> LLMCheck{LLM False Positive Check <br> <font color="red"><b>(NOT IMPLEMENTED)</b></font>}
    LLMCheck -.->|Fallback due to GenAI Limit| Blacklist[Blacklist Word Template Validation <br> Hardcoded Safeguards]
    
    Blacklist --> MinError[Minimize Error & Merge Entities]
    MinError --> SyntheticMap[Synthetic Data Generation <br> Faker Consistency Mode]
    SyntheticMap --> ApplyRedact[Apply Text Replacement]
    
    %% Right Branch: Image Processing
    Split -->|Branch 2: Image Processing| ImageExt[Page Render & Image Extraction]
    ImageExt --> LogoDetect[Logo & Card Identification]
    LogoDetect --> YOLO{YOLO Object Detection Model <br> <font color="red"><b>(NOT IMPLEMENTED)</b></font>}
    
    YOLO -.->|Alternative Pipeline| OpenCVDirect[OpenCV Direct Similarity Search]
    OpenCVDirect --> ScaleSearch[Multi-Scale Template Matching <br> TM_CCOEFF_NORMED]
    ScaleSearch --> PixelCompare[Direct Pixel Correlation Match <br> 128x128 Comparison]
    PixelCompare --> ApplyBlur[Apply Gaussian Blur / Overlay Mask]
    
    %% Merge & Outputs
    ApplyRedact --> Combine[Consolidate Output Document]
    ApplyBlur --> Combine
    
    Combine --> SaveDoc[Save Anonymized File]
    Combine --> SaveLogs[Generate Reports]
    
    SaveDoc --> OutDoc[Output: redacted_filename.pdf/docx/txt]
    SaveLogs --> OutJSON[Full JSON Audit Log <br> & Texts-Only JSON]
```

---

## 2. Component Pipeline and Libraries Used

### A. Document Routing and Orchestration

The application starts through **`app.py`**, which provides the Streamlit interface, or **`run_cli.py`** for command-line execution.

The main workflow is managed by **`core/pipeline.py`**, which identifies the document type, sends it to the appropriate processing pipeline, and manages the final output. The overall coordination is handled by **`core/orchestrator.py`**, which combines regex and NLP detections, applies blacklist validation, and manages false-positive filtering.

#### Libraries Used

- Streamlit
- pathlib
- json
- re

---

### B. Parallel Pipeline 1: Text Processing and Redaction

#### 1. Text Extraction

Each document is parsed using a format-specific processor.

- **PDF:** Extracted page by page using **PyMuPDF (`fitz`)**
- **DOCX:** Reads paragraphs and tables using **python-docx**
- **TXT:** Loaded directly as plain text

#### 2. Sensitive Information Detection

Detection combines two complementary approaches.

##### Regex Detector (`detectors/regex_detector.py`)

This module quickly identifies structured information such as:

- Email addresses
- Phone numbers
- IFSC, SWIFT, and UPI IDs
- URLs
- IP and MAC addresses
- Credit card numbers
- CIN and DIN numbers
- SEBI registration IDs
- Addresses identified through ZIP code patterns

##### NLP Detector (`detectors/presidio_detector.py`)

Microsoft Presidio, powered by **spaCy (`en_core_web_sm`)**, identifies context-based entities including:

- Person names
- Organizations
- Locations
- Dates

Using both methods together provides better coverage. Regex is excellent at spotting structured patterns, while NLP understands context. Together they make a solid team.

#### 3. False Positive Filtering

An LLM-based verification stage was originally planned but was not implemented because of GenAI API limitations.

Instead, the project uses a lightweight blacklist validation layer that:

- Normalizes detected text
- Compares results against predefined keywords
- Uses `outputs/false_positive.json` to ignore known non-sensitive terms such as document headers, labels, or repeated template text

#### 4. Entity Merging

The **Entity Merger** (`detectors/merger.py`) combines overlapping or adjacent detections by comparing character spans and bounding boxes. This prevents partial redactions and ensures each sensitive entity is treated as a single unit.

#### 5. Synthetic Data Replacement

The **Faker Mapper** (`replacers/faker_mapper.py`) replaces sensitive information with realistic synthetic values generated using the **Faker** library.

When **Preserve Consistency** is enabled, every occurrence of the same real-world entity is replaced with the same synthetic value throughout the document. A person named "John Smith" remains the same synthetic identity everywhere instead of becoming three different people halfway through the report.

---

### C. Parallel Pipeline 2: Image Processing and Logo Detection

#### 1. Visual Extraction

For PDFs, pages are rendered into images using **PyMuPDF** or embedded images are extracted directly.

For DOCX files, embedded media objects are retrieved and processed individually.

#### 2. Image Detection

A YOLO-based object detection model was considered during the design phase but was not implemented. Instead, the system uses OpenCV-based template matching.

##### OpenCV Similarity Search (`redaction/image_blur.py`)

The pipeline performs two types of matching.

**Direct Similarity Comparison**

- Resizes the candidate region to **128 × 128 pixels**
- Normalizes image contrast
- Compares it with reference templates such as:
  - `aadhar_card.png`
  - `pan_card.png`
  - `icici_logo.png`
  - `mufg_logo.png`

**Multi-Scale Template Matching**

Using `cv2.matchTemplate` with `cv2.TM_CCOEFF_NORMED`, the system searches across approximately fifteen image scales ranging from **0.15× to 3.0×**. This allows it to detect logos and cards even when they appear at different sizes.

#### 3. Image Obfuscation

Once a match is confirmed, the system hides the sensitive region by either:

- Applying a Gaussian Blur using OpenCV or Pillow
- Drawing a solid grey rectangle over the detected area

#### Libraries Used

- OpenCV (`cv2`)
- NumPy
- Pillow (PIL)
- PyMuPDF (`fitz`)

---

### D. Output Generation and Logging

After both pipelines finish, their outputs are merged into the final anonymized document.

The system generates:

#### Anonymized Documents

- PDF
- DOCX
- TXT

#### Audit Reports

- `report_[filename].json` contains detected entities, coordinates, labels, and replacement values.
- `texts_report_[filename].json` contains only the redacted text values for easier auditing.
- `outputs/output.txt` stores the processed text generated during TXT workflows.

#### Libraries Used

- pandas
- json

---

## 3. Directory Structure

```text
SCALER AI LABS - Assignment/
│
├── .streamlit/                   # Streamlit configuration
│   └── config.toml
│
├── assets/                       # UI assets
│   ├── banner.png
│   ├── circular_logo.png
│   ├── logo_no_bg.png
│   └── styles.css
│
├── cache/                        # Cached files
│
├── core/                         # Core orchestration layer
│   ├── orchestrator.py           # Coordinates detectors and validation
│   └── pipeline.py               # Main workflow controller
│
├── detectors/                    # PII detection modules
│   ├── merger.py
│   ├── presidio_detector.py
│   └── regex_detector.py
│
├── image_redact/                 # Reference templates for OpenCV
│   ├── aadhar_card.png
│   ├── icici_logo.png
│   ├── ksh_logo.png
│   ├── mufg_logo.png
│   ├── nuvama_logo.png
│   └── pan_card.png
│
├── outputs/                      # Generated reports
│   ├── false_positive.json
│   └── report_*.json
│
├── processors/                   # File parsers
│   ├── docx_processor.py
│   ├── exporter.py
│   └── pdf_processor.py
│
├── redaction/                    # Redaction engines
│   ├── docx_redactor.py
│   ├── image_blur.py
│   ├── pdf_redactor.py
│   └── text_redactor.py
│
├── reference/                    # Documentation and reference images
│   ├── guide.md
│   └── *.png
│
├── replacers/                    # Synthetic data generation
│   ├── faker_mapper.py
│   └── text_replacer.py
│
├── reports/                      # Report generation
│   └── report_generator.py
│
├── uploads/                      # Temporary uploaded files
│
├── utils/                        # Shared utilities
│   ├── constants.py
│   ├── helpers.py
│   └── regex.py
│
├── app.py                        # Streamlit entry point
├── config.py                     # Global configuration
├── requirements.txt              # Project dependencies
└── run_cli.py                    # CLI entry point
```