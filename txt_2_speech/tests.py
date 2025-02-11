import textract

# Path to the PDF file
pdf_path = "example.pdf"

# Extract text from the PDF
try:
    # Use textract to process the PDF
    text = textract.process(pdf_path).decode('utf-8')
    
    # Print the extracted text
    print("Extracted Text:")
    print(text)
except Exception as e:
    print(f"Error extracting text from PDF: {e}")
