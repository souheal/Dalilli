from typing import List, Dict, Any
import re


class ChunkingService:
    """Service for chunking documents into smaller pieces"""

    def __init__(
        self,
        chunk_size: int = 800,
        chunk_overlap: int = 200,
        enable_semantic_chunking: bool = True
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.enable_semantic_chunking = enable_semantic_chunking

    def chunk_text(
        self,
        text: str,
        metadata: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Chunk text into smaller pieces

        Args:
            text: Text to chunk
            metadata: Metadata to attach to each chunk

        Returns:
            List of chunks with text and metadata
        """
        if metadata is None:
            metadata = {}

        if self.enable_semantic_chunking:
            chunks = self._semantic_chunk(text)
        else:
            chunks = self._fixed_chunk(text)

        # Add metadata to each chunk
        result = []
        for i, chunk_text in enumerate(chunks):
            chunk_metadata = metadata.copy()
            chunk_metadata["chunk_index"] = i
            chunk_metadata["total_chunks"] = len(chunks)

            # Try to determine page number from text
            page_match = re.search(r'\[Page (\d+)\]', chunk_text)
            if page_match:
                chunk_metadata["page"] = int(page_match.group(1))

            result.append({
                "text": chunk_text.strip(),
                "metadata": chunk_metadata
            })

        return result

    def _fixed_chunk(self, text: str) -> List[str]:
        """Split text into fixed-size chunks with overlap"""
        chunks = []
        words = text.split()

        if len(words) <= self.chunk_size:
            return [text]

        start = 0
        while start < len(words):
            end = start + self.chunk_size
            chunk = " ".join(words[start:end])
            chunks.append(chunk)

            # Move start position considering overlap
            start = end - self.chunk_overlap
            if start >= len(words):
                break

        return chunks

    def _semantic_chunk(self, text: str) -> List[str]:
        """
        Split text into semantic chunks based on natural boundaries
        like paragraphs, sections, and sentences
        """
        # Split by double newlines (paragraphs)
        paragraphs = re.split(r'\n\s*\n', text)

        chunks = []
        current_chunk = []
        current_length = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            para_words = len(para.split())

            # If single paragraph is too long, split by sentences
            if para_words > self.chunk_size:
                if current_chunk:
                    chunks.append("\n\n".join(current_chunk))
                    current_chunk = []
                    current_length = 0

                # Split long paragraph by sentences
                sentence_chunks = self._split_by_sentences(para)
                chunks.extend(sentence_chunks)
                continue

            # Check if adding this paragraph exceeds chunk size
            if current_length + para_words > self.chunk_size:
                if current_chunk:
                    chunks.append("\n\n".join(current_chunk))

                # Start new chunk with overlap
                if len(current_chunk) > 0:
                    # Keep last paragraph for overlap
                    overlap_text = current_chunk[-1] if current_chunk else ""
                    overlap_words = len(overlap_text.split())

                    if overlap_words < self.chunk_overlap:
                        current_chunk = [overlap_text, para]
                        current_length = overlap_words + para_words
                    else:
                        current_chunk = [para]
                        current_length = para_words
                else:
                    current_chunk = [para]
                    current_length = para_words
            else:
                current_chunk.append(para)
                current_length += para_words

        # Don't forget the last chunk
        if current_chunk:
            chunks.append("\n\n".join(current_chunk))

        return chunks

    def _split_by_sentences(self, text: str) -> List[str]:
        """Split text by sentences when paragraphs are too long"""
        # Simple sentence splitting
        sentences = re.split(r'(?<=[.!?])\s+', text)

        chunks = []
        current_chunk = []
        current_length = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            sentence_words = len(sentence.split())

            if current_length + sentence_words > self.chunk_size:
                if current_chunk:
                    chunks.append(" ".join(current_chunk))

                # Handle overlap
                if len(current_chunk) > 0:
                    overlap_sentences = []
                    overlap_length = 0
                    for s in reversed(current_chunk):
                        s_len = len(s.split())
                        if overlap_length + s_len <= self.chunk_overlap:
                            overlap_sentences.insert(0, s)
                            overlap_length += s_len
                        else:
                            break
                    current_chunk = overlap_sentences + [sentence]
                    current_length = overlap_length + sentence_words
                else:
                    current_chunk = [sentence]
                    current_length = sentence_words
            else:
                current_chunk.append(sentence)
                current_length += sentence_words

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks
