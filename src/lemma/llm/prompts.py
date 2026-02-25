"""Reusable prompt templates for LLM interactions."""
from typing import List, Dict, Any


def build_qa_prompt(question: str, context_papers: List[Dict[str, Any]]) -> str:
    """Build a prompt for question answering across papers.

    Args:
        question: User's question
        context_papers: List of paper dictionaries with metadata and text

    Returns:
        Formatted prompt string
    """
    context_parts = []

    for i, paper in enumerate(context_papers, 1):
        title = paper.get("title", "Untitled")
        authors = paper.get("authors", "Unknown")
        year = paper.get("year", "N/A")
        text = paper.get("text", "")

        context_parts.append(
            f"[Paper {i}]\n"
            f"Title: {title}\n"
            f"Authors: {authors}\n"
            f"Year: {year}\n"
            f"Content: {text[:2000]}\n"  # Limit to avoid token overflow
        )

    context = "\n\n".join(context_parts)

    prompt = f"""You are a research assistant helping to answer questions about academic papers.

Based on the following papers, answer the question below. Cite specific papers when relevant.

Papers:
{context}

Question: {question}

Provide a clear, concise answer based on the information in the papers above. If the papers don't contain enough information to answer the question, say so."""

    return prompt


def build_summary_prompt(paper: Dict[str, Any], max_length: int = 200) -> str:
    """Build a prompt for summarizing a paper.

    Args:
        paper: Paper dictionary with metadata and text
        max_length: Maximum words in summary

    Returns:
        Formatted prompt string
    """
    title = paper.get("title", "Untitled")
    text = paper.get("text", "")

    prompt = f"""Summarize the following academic paper in approximately {max_length} words.

Title: {title}

Content:
{text[:5000]}

Provide a concise summary covering:
1. Main contribution/finding
2. Methodology (if applicable)
3. Key results or implications

Summary:"""

    return prompt


def build_citation_extraction_prompt(text: str) -> str:
    """Build a prompt for extracting citations from paper text.

    Args:
        text: Paper text content

    Returns:
        Formatted prompt string
    """
    prompt = f"""Extract all academic citations from the following text.

For each citation, provide:
- Title (if available)
- Authors (if available)
- Year (if available)

Text:
{text[:4000]}

Return citations in a structured format like:
1. Title: "..." | Authors: "..." | Year: XXXX
2. Title: "..." | Authors: "..." | Year: XXXX

Citations:"""

    return prompt


def build_comparison_prompt(paper1: Dict[str, Any], paper2: Dict[str, Any]) -> str:
    """Build a prompt for comparing two papers.

    Args:
        paper1: First paper dictionary
        paper2: Second paper dictionary

    Returns:
        Formatted prompt string
    """

    def format_paper(paper: Dict[str, Any]) -> str:
        return f"""Title: {paper.get('title', 'Untitled')}
Authors: {paper.get('authors', 'Unknown')}
Year: {paper.get('year', 'N/A')}
Abstract: {paper.get('abstract', 'N/A')}
Content: {paper.get('text', '')[:1500]}"""

    prompt = f"""Compare the following two academic papers. Focus on:
1. Research objectives and questions
2. Methodologies
3. Key findings
4. Similarities and differences
5. Complementary insights

Paper 1:
{format_paper(paper1)}

Paper 2:
{format_paper(paper2)}

Provide a structured comparison highlighting similarities, differences, and how they relate to each other.

Comparison:"""

    return prompt


def build_collection_summary_prompt(papers: List[Dict[str, Any]]) -> str:
    """Build a prompt for summarizing a collection of papers.

    Args:
        papers: List of paper dictionaries

    Returns:
        Formatted prompt string
    """
    paper_summaries = []
    for i, paper in enumerate(papers, 1):
        paper_summaries.append(
            f"{i}. {paper.get('title', 'Untitled')} "
            f"({paper.get('year', 'N/A')}) - "
            f"{paper.get('abstract', 'No abstract')[:200]}"
        )

    papers_text = "\n".join(paper_summaries)

    prompt = f"""Summarize the key themes and findings across this collection of {len(papers)} academic papers.

Papers:
{papers_text}

Provide:
1. Common themes and research areas
2. Notable findings or contributions
3. Chronological trends (if apparent)
4. Gaps or future directions

Summary:"""

    return prompt
