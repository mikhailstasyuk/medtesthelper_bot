from io import BytesIO
import pathlib

import cv2
from PIL import Image as PILImage
from img2table.ocr import TesseractOCR
from img2table.document import Image
from img2table.document import PDF
import pandas as pd
import pymupdf4llm

from app.preprocesssing import preprocess


def extract_from_pdf(src):
    """Extract text from a pdf."""
    md_text = pymupdf4llm.to_markdown(src)
    # pathlib.Path("output.md").write_bytes(md_text.encode()) # save as file
    return md_text


def extract_from_image(src):
    """Extract text from an image."""
    ocr = TesseractOCR(n_threads=2, 
                    lang="rus+eng", 
                    psm=11)      
    
    image = preprocess(src)

    _, buffer = cv2.imencode('.png', image)
    img_bytes = BytesIO(buffer.tobytes())

        
    doc = Image(img_bytes)

    # Table extraction
    extracted_tables = doc.extract_tables(ocr=ocr,
                                        implicit_rows=True,
                                        implicit_columns=True,
                                        borderless_tables=True,
                                        min_confidence=50)

    dfs = [table.df for table in extracted_tables]
    return dfs


def save_processed_preview(image, extracted_tables):
    """Save processed image preview to inspect recognition quality."""
    table_img = cv2.imread(image)
    
    for table in extracted_tables:
        for row in table.content.values():
            for cell in row:
                cv2.rectangle(table_img, (cell.bbox.x1, cell.bbox.y1), (cell.bbox.x2, cell.bbox.y2), (255, 0, 0), 2)
                
    outimage = PILImage.fromarray(table_img)
    outimage.save("output_table_image.png")

if __name__ == "__main__":
    extract_from_image('/workspaces/medtesthelper_bot/data/images/analiz.png')