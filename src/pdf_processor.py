## Extract and chunk SOP documents intelligently ##
import re
from pathlib import Path
from typing import List, Dict
import PyPDF2


class SOPProcessor:
    ## Process SOP documents with flexible chunking ##




    def __init__(self):
        self.section_headers = [
            "Purpose", "References", "Scope", "Allowable Exceptions",
            "Procedures", "Roles and Responsibilities", "Details",
            "Training", "Related SOPs", "Background", "Timeline",
            "Agenda", "Goals", "Revision History"
        ]
        self.chunk_size = 1000
        self.chunk_overlap = 200



    def extract_text(self, pdf_path: str) -> str:
        ## extract all text ##
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text



    def extract_metadata(self, text: str, filename: str) -> Dict:
        ## extract SOP metadata ##
        metadata = {
            "filename": filename,
            "sop_number": "",
            "version": "",
            "title": "",
            "effective_date": ""
        }

        ## extract SOP number ##
        sop_match = re.search(r'SOP #:\s*(\d+\.\d+)', text)
        if sop_match:
            metadata["sop_number"] = sop_match.group(1)
        else:
            filename_match = re.match(r'(\d+)[._](\d+)', filename)
            if filename_match:
                metadata["sop_number"] = f"{filename_match.group(1)}.{filename_match.group(2)}"

        ## extract version ##
        version_match = re.search(r'Version:\s*(\d+\.\d+)', text)
        if version_match:
            metadata["version"] = version_match.group(1)

        ## extract title ##
        title_match = re.search(r'Standard Operating Procedures?\s*\n(.+?)(?:\n|Page)', text, re.IGNORECASE)
        if title_match:
            metadata["title"] = title_match.group(1).strip()
        elif not metadata["title"]:
            ## fallback to filename ##
            metadata["title"] = filename.replace('.pdf', '').replace('_', ' ')

        ## extract effective date ##
        date_match = re.search(r'Effective Date[:\s]+(\d{1,2}/\d{1,2}/\d{4})', text)
        if date_match:
            metadata["effective_date"] = date_match.group(1)

        return metadata

    def chunk_by_sections(self, text: str, metadata: Dict) -> List[Dict]:
        ## chunk document by sections ##
        chunks = []

        ## try to find section headers anywhere in text ##
        section_positions = []
        for header in self.section_headers:
            pattern = rf'\b{re.escape(header)}\b'
            for match in re.finditer(pattern, text, re.IGNORECASE):
                section_positions.append((match.start(), header))

        ## sort by position ##
        section_positions.sort()

        ## if we found sections, split by them ##
        if len(section_positions) >= 2:
            context_prefix = f"SOP {metadata['sop_number']}: {metadata['title']}\n\n"

            for i in range(len(section_positions)):
                start_pos = section_positions[i][0]
                section_type = section_positions[i][1]

                ## get end position ##
                if i + 1 < len(section_positions):
                    end_pos = section_positions[i + 1][0]
                else:
                    end_pos = len(text)

                section_text = text[start_pos:end_pos].strip()

                ## CHANGED: accept any section with content ##
                if len(section_text) < 0:
                    continue

                chunk = {
                    "content": context_prefix + section_text,
                    "metadata": {
                        **metadata,
                        "section_type": section_type,
                        "char_count": len(section_text)
                    }
                }
                chunks.append(chunk)

        return chunks

    def chunk_by_size(self, text: str, metadata: Dict) -> List[Dict]:
        ## fallback fixed size chunking with overlap ##
        chunks = []
        context_prefix = f"SOP {metadata['sop_number']}: {metadata['title']}\n\n"

        start = 0
        chunk_num = 1

        while start < len(text):
            end = start + self.chunk_size
            chunk_text = text[start:end].strip()

            ## CHANGED: lower minimum and use continue instead of break ##
            if len(chunk_text) < 0:
                start += (self.chunk_size - self.chunk_overlap)
                continue

            chunk = {
                "content": context_prefix + chunk_text,
                "metadata": {
                    **metadata,
                    "section_type": f"Chunk {chunk_num}",
                    "char_count": len(chunk_text)
                }
            }
            chunks.append(chunk)

            start += (self.chunk_size - self.chunk_overlap)
            chunk_num += 1

        return chunks



    def process_directory(self, pdf_directory: str) -> List[Dict]:
        all_chunks = []
        pdf_path = Path(pdf_directory)

        for pdf_file in pdf_path.glob("*.pdf"):
            print(f"Processing: {pdf_file.name}")

            ## extract text ##
            text = self.extract_text(str(pdf_file))

            ## skip empty documents ##
            if len(text.strip()) < 0:
                print(f"  -> Skipped (too short)")
                continue

            ## extract metadata ##
            metadata = self.extract_metadata(text, pdf_file.name)

            ## try section-based chunking first ##
            chunks = self.chunk_by_sections(text, metadata)

            ## fallback to size-based if no sections found ##
            if len(chunks) == 0:
                chunks = self.chunk_by_size(text, metadata)

            all_chunks.extend(chunks)
            print(f"  -> Created {len(chunks)} chunks")

        return all_chunks