# Kilo Code OCR to Markdown Workflow

## Standard Instruction Format
When given the instruction: "Convert file: (filename).png to .md format"

Kilo Code will:
1. Fetch the PNG file from the specified path
2. Apply OCR processing using the available OCR engines (PaddleOCR and Tesseract)
3. Convert the OCR'd content to two separate files:
   - `(filename)_OCR.md` - Contains the extracted text content
   - `(filename)_metadata.md` - Contains processing metadata and OCR information
4. Save both files in the same folder as the original PNG file

## Test Task
Convert `C:\_1mybizz\paddle-plugin\Docs\_My Todo\A.0 Mybizz system.png` to .md format

## Implementation Steps
1. Locate the source PNG file
2. Initialize OCR processors (PaddleOCR primary, Tesseract fallback)
3. Process the image with OCR
4. Extract and format text content
5. Generate metadata including:
   - Processing timestamp
   - OCR engine used
   - Image dimensions
   - Processing time
   - Confidence scores
6. Save both output files with UTF-8 encoding
7. Verify file creation and content