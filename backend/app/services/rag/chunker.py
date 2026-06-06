from dataclasses import dataclass

@dataclass
class DocumentChunk:
    text: str

class RecursiveCharacterTextSplitter:
    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 64, separators: list[str] = None):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", " ", ""]

    def split_text(self, text: str) -> list[str]:
        return self._split_text(text, self.separators)

    def _split_text(self, text: str, separators: list[str]) -> list[str]:
        final_chunks = []
        
        # Select the correct separator
        separator = separators[-1] if separators else ""
        new_separators = []
        for i, s in enumerate(separators):
            if s == "":
                separator = s
                break
            if s in text:
                separator = s
                new_separators = separators[i + 1:]
                break
                
        # Split the text
        if separator != "":
            splits = text.split(separator)
        else:
            splits = list(text)
            
        # Now merge splits
        good_splits = []
        for s in splits:
            if s == "":
                continue
            good_splits.append(s)
            
        # Recursively split splits if they are too big
        splits_to_merge = []
        for s in good_splits:
            if len(s) < self.chunk_size:
                splits_to_merge.append(s)
            else:
                if splits_to_merge:
                    merged = self._merge_splits(splits_to_merge, separator)
                    final_chunks.extend(merged)
                    splits_to_merge = []
                # Recursively split the too-big split
                recursive_splits = self._split_text(s, new_separators)
                final_chunks.extend(recursive_splits)
                
        if splits_to_merge:
            merged = self._merge_splits(splits_to_merge, separator)
            final_chunks.extend(merged)
            
        return final_chunks

    def _merge_splits(self, splits: list[str], separator: str) -> list[str]:
        separator_len = len(separator)
        docs = []
        current_doc = []
        total_len = 0
        
        for d in splits:
            d_len = len(d)
            if total_len + d_len + (separator_len if current_doc else 0) <= self.chunk_size:
                current_doc.append(d)
                total_len += d_len + (separator_len if len(current_doc) > 1 else 0)
            else:
                if current_doc:
                    docs.append(separator.join(current_doc))
                
                # Rollback to include overlap
                # We want to keep some elements from current_doc for overlap
                overlap_doc = []
                overlap_len = 0
                for p in reversed(current_doc):
                    p_len = len(p)
                    if overlap_len + p_len + (separator_len if overlap_doc else 0) <= self.chunk_overlap:
                        overlap_doc.insert(0, p)
                        overlap_len += p_len + (separator_len if len(overlap_doc) > 1 else 0)
                    else:
                        break
                
                current_doc = overlap_doc + [d]
                total_len = overlap_len + d_len + (separator_len if len(current_doc) > 1 else 0)
                
        if current_doc:
            docs.append(separator.join(current_doc))
            
        return docs

def chunk_text(text: str, chunk_size: int = 512, overlap: int = 64) -> list[DocumentChunk]:
    """Helper function to split text into DocumentChunk objects."""
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=overlap)
    chunks = splitter.split_text(text)
    return [DocumentChunk(text=c) for c in chunks]
