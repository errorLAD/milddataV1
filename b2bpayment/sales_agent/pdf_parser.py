import re
import pypdf

def parse_customer_pdf(pdf_file):
    """
    Extracts text from uploaded PDF file using pypdf.
    Returns:
    {
        'is_scanned': bool,
        'rows': [ {'index': 1, 'name': 'Rahul Sharma', 'phone': '9876543210', 'notes': 'Regular buyer'}, ... ],
        'error': str or None
    }
    """
    result = {
        'is_scanned': False,
        'rows': [],
        'error': None
    }

    try:
        reader = pypdf.PdfReader(pdf_file)
        full_text = ""
        for page in reader.pages:
            t = page.extract_text()
            if t:
                full_text += t + "\n"

        full_text = full_text.strip()
        if not full_text:
            result['is_scanned'] = True
            result['error'] = "PDF appears to be scanned or image-only. Automatic OCR is not performed to prevent guessing — please enter customer details manually."
            return result

        lines = [line.strip() for line in full_text.split('\n') if line.strip()]
        
        row_index = 1
        phone_regex = re.compile(r'(?:\+?91[\s\-]?)?([6-9]\d{9})')

        for line in lines:
            # Look for phone number in line
            phone_match = phone_regex.search(line)
            if phone_match:
                phone_num = phone_match.group(1)
                
                # Extract text before phone match as Name, after as Notes
                start, end = phone_match.span()
                part_before = line[:start].strip(' ,-:\t|')
                part_after = line[end:].strip(' ,-:\t|')

                # Clean name
                name = part_before if part_before else "Customer"
                # Remove header labels like "Name:", "Phone:" if present
                name = re.sub(r'^(?:name|customer|sl\.?\s*no\.?|sr\.?\s*no\.?|\d+[\.\-\)]?)\s*[:\-]?\s*', '', name, flags=re.IGNORECASE).strip()
                if not name:
                    name = f"Customer {row_index}"

                notes = part_after if part_after else ""

                result['rows'].append({
                    'index': row_index,
                    'name': name,
                    'phone': phone_num,
                    'notes': notes
                })
                row_index += 1

        if not result['rows']:
            # If text exists but no phone numbers match regex pattern
            result['is_scanned'] = True
            result['error'] = "No valid 10-digit phone numbers detected in PDF text. Please verify formatting or enter details manually."

    except Exception as e:
        result['is_scanned'] = True
        result['error'] = f"Failed to parse PDF file: {str(e)}"

    return result
