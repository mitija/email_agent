import re

def normalize_whitespace(text):
    """Normalize whitespace in text by replacing special Unicode spaces and normalizing empty lines.
    
    Args:
        text (str): The text to normalize
        
    Returns:
        str: The normalized text with standard spaces and normalized empty lines
    """
    # Dictionary of Unicode spaces and their replacements
    UNICODE_SPACES = {
        '\u00A0': ' ',    # NO-BREAK SPACE
        '\u1680': ' ',    # OGHAM SPACE MARK
        '\u2000': ' ',    # EN QUAD
        '\u2001': ' ',    # EM QUAD
        '\u2002': ' ',    # EN SPACE
        '\u2003': ' ',    # EM SPACE
        '\u2004': ' ',    # THREE-PER-EM SPACE
        '\u2005': ' ',    # FOUR-PER-EM SPACE
        '\u2006': ' ',    # SIX-PER-EM SPACE
        '\u2007': ' ',    # FIGURE SPACE
        '\u2008': ' ',    # PUNCTUATION SPACE
        '\u2009': ' ',    # THIN SPACE
        '\u200A': ' ',    # HAIR SPACE
        '\u200B': '',     # ZERO WIDTH SPACE
        '\u200C': '',     # ZERO WIDTH NON-JOINER
        '\u200D': '',     # ZERO WIDTH JOINER
        '\u202F': ' ',    # NARROW NO-BREAK SPACE
        '\u205F': ' ',    # MEDIUM MATHEMATICAL SPACE
        '\u3000': ' ',    # IDEOGRAPHIC SPACE
        '\uFEFF': '',     # ZERO WIDTH NO-BREAK SPACE (BOM)
        '\u180E': '',     # MONGOLIAN VOWEL SEPARATOR
        '&nbsp;': ' ',    # HTML NO-BREAK SPACE
        '\u2028': '\n',   # LINE SEPARATOR
        '\u2029': '\n\n', # PARAGRAPH SEPARATOR
        '\u2060': '',     # WORD JOINER
        '\u2061': '',     # FUNCTION APPLICATION
        '\u2062': '',     # INVISIBLE TIMES
        '\u2063': '',     # INVISIBLE SEPARATOR
        '\u2064': '',     # INVISIBLE PLUS
        '\u206A': '',     # INHIBIT SYMMETRIC SWAPPING
        '\u206B': '',     # ACTIVATE SYMMETRIC SWAPPING
        '\u206C': '',     # INHIBIT ARABIC FORM SHAPING
        '\u206D': '',     # ACTIVATE ARABIC FORM SHAPING
        '\u206E': '',     # NATIONAL DIGIT SHAPES
        '\u206F': '',     # NOMINAL DIGIT SHAPES
        '\u200E': '',     # LEFT-TO-RIGHT MARK
        '\u200F': '',     # RIGHT-TO-LEFT MARK
        '\u202A': '',     # LEFT-TO-RIGHT EMBEDDING
        '\u202B': '',     # RIGHT-TO-LEFT EMBEDDING
        '\u202C': '',     # POP DIRECTIONAL FORMATTING
        '\u202D': '',
        '\u202E': '',     # RIGHT-TO-LEFT OVERRIDE
        '\u034F': '',     # COMBINING GRAPHEME JOINER
    }

    # Replace all special space characters
    for space, replacement in UNICODE_SPACES.items():
        text = text.replace(space, replacement)

    # Replace two or more empty lines with only one empty line
    text = re.sub(r'\n\s*\n', '\n\n', text)
    
    return text 