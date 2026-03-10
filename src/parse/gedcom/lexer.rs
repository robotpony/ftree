/// A single tokenized GEDCOM line.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Token {
    /// Nesting level (0 = top-level record).
    pub level: u8,
    /// Cross-reference ID (e.g. "@I1@"), if present.
    pub xref: Option<String>,
    /// Tag (e.g. "INDI", "NAME", "DATE").
    pub tag: String,
    /// Value after the tag, if any.
    pub value: Option<String>,
    /// 1-based line number in the source file.
    pub line_number: usize,
}

/// Tokenize a GEDCOM string into a sequence of tokens.
///
/// Handles CONT and CONC continuation lines by merging them
/// into the parent token's value.
pub fn tokenize(input: &str) -> Vec<Token> {
    let mut raw_tokens = Vec::new();

    for (line_idx, line) in input.lines().enumerate() {
        let line = line.trim_end();
        if line.is_empty() {
            continue;
        }

        if let Some(token) = parse_line(line, line_idx + 1) {
            raw_tokens.push(token);
        }
    }

    // Merge CONT and CONC into their parent tokens
    merge_continuations(raw_tokens)
}

/// Parse a single GEDCOM line into a Token.
fn parse_line(line: &str, line_number: usize) -> Option<Token> {
    let line = line.trim_start_matches('\u{feff}'); // strip BOM if present on first line

    let mut parts = line.splitn(2, ' ');
    let level_str = parts.next()?;
    let level: u8 = level_str.parse().ok()?;

    let rest = parts.next()?.trim();
    if rest.is_empty() {
        return Some(Token {
            level,
            xref: None,
            tag: String::new(),
            value: None,
            line_number,
        });
    }

    // Check for xref: starts with @, and is at level 0
    if rest.starts_with('@') {
        // Find end of xref
        if let Some(at_end) = rest[1..].find('@') {
            let xref = rest[..at_end + 2].to_string();
            let after_xref = rest[at_end + 2..].trim();

            // Split remaining into tag and optional value
            let mut tag_parts = after_xref.splitn(2, ' ');
            let tag = tag_parts.next().unwrap_or("").to_uppercase();
            let value = tag_parts.next().map(|v| v.to_string());

            return Some(Token {
                level,
                xref: Some(xref),
                tag,
                value,
                line_number,
            });
        }
    }

    // No xref: split into tag and optional value
    let mut tag_parts = rest.splitn(2, ' ');
    let tag = tag_parts.next().unwrap_or("").to_uppercase();
    let value = tag_parts.next().map(|v| v.to_string());

    Some(Token {
        level,
        xref: None,
        tag,
        value,
        line_number,
    })
}

/// Merge CONT and CONC tokens into their parent token's value.
fn merge_continuations(tokens: Vec<Token>) -> Vec<Token> {
    let mut result: Vec<Token> = Vec::with_capacity(tokens.len());

    for token in tokens {
        match token.tag.as_str() {
            "CONT" => {
                if let Some(parent) = result.last_mut() {
                    let parent_val = parent.value.get_or_insert_with(String::new);
                    parent_val.push('\n');
                    if let Some(ref val) = token.value {
                        parent_val.push_str(val);
                    }
                }
            }
            "CONC" => {
                if let Some(parent) = result.last_mut() {
                    if let Some(ref val) = token.value {
                        let parent_val = parent.value.get_or_insert_with(String::new);
                        parent_val.push_str(val);
                    }
                }
            }
            _ => {
                result.push(token);
            }
        }
    }

    result
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_level0_with_xref() {
        let t = parse_line("0 @I1@ INDI", 1).unwrap();
        assert_eq!(t.level, 0);
        assert_eq!(t.xref, Some("@I1@".to_string()));
        assert_eq!(t.tag, "INDI");
        assert_eq!(t.value, None);
    }

    #[test]
    fn test_parse_level0_no_xref() {
        let t = parse_line("0 HEAD", 1).unwrap();
        assert_eq!(t.level, 0);
        assert_eq!(t.xref, None);
        assert_eq!(t.tag, "HEAD");
        assert_eq!(t.value, None);
    }

    #[test]
    fn test_parse_tag_with_value() {
        let t = parse_line("1 NAME John /Smith/", 5).unwrap();
        assert_eq!(t.level, 1);
        assert_eq!(t.tag, "NAME");
        assert_eq!(t.value, Some("John /Smith/".to_string()));
        assert_eq!(t.line_number, 5);
    }

    #[test]
    fn test_parse_date_value() {
        let t = parse_line("2 DATE 1 Jan 1900", 10).unwrap();
        assert_eq!(t.level, 2);
        assert_eq!(t.tag, "DATE");
        assert_eq!(t.value, Some("1 Jan 1900".to_string()));
    }

    #[test]
    fn test_parse_descriptive_xref() {
        let t = parse_line("0 @Homer_Simpson@ INDI", 1).unwrap();
        assert_eq!(t.xref, Some("@Homer_Simpson@".to_string()));
        assert_eq!(t.tag, "INDI");
    }

    #[test]
    fn test_parse_xref_with_pointer_value() {
        let t = parse_line("1 HUSB @I1@", 1).unwrap();
        assert_eq!(t.level, 1);
        assert_eq!(t.xref, None);
        assert_eq!(t.tag, "HUSB");
        assert_eq!(t.value, Some("@I1@".to_string()));
    }

    #[test]
    fn test_tag_case_normalization() {
        let t = parse_line("1 name John /Smith/", 1).unwrap();
        assert_eq!(t.tag, "NAME");
    }

    #[test]
    fn test_cont_merging() {
        let tokens = tokenize("1 NOTE First line\n2 CONT Second line\n2 CONT Third line");
        assert_eq!(tokens.len(), 1);
        assert_eq!(
            tokens[0].value,
            Some("First line\nSecond line\nThird line".to_string())
        );
    }

    #[test]
    fn test_conc_merging() {
        let tokens = tokenize("1 NOTE Long val\n2 CONC ue here");
        assert_eq!(tokens.len(), 1);
        assert_eq!(tokens[0].value, Some("Long value here".to_string()));
    }

    #[test]
    fn test_tokenize_simple_file() {
        let input = "0 HEAD\n1 GEDC\n2 VERS 5.5\n0 @I1@ INDI\n1 NAME John /Smith/\n0 TRLR";
        let tokens = tokenize(input);
        assert_eq!(tokens.len(), 6);
        assert_eq!(tokens[0].tag, "HEAD");
        assert_eq!(tokens[3].xref, Some("@I1@".to_string()));
        assert_eq!(tokens[5].tag, "TRLR");
    }

    #[test]
    fn test_empty_lines_skipped() {
        let tokens = tokenize("0 HEAD\n\n0 TRLR\n");
        assert_eq!(tokens.len(), 2);
    }
}
