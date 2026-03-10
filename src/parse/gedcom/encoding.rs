use encoding_rs::{UTF_16BE, UTF_16LE};

/// Detected encoding from BOM or CHAR declaration.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum DetectedEncoding {
    Utf8,
    Utf16Le,
    Utf16Be,
    Ascii,
    Ansel,
}

/// Result of encoding detection: the decoded UTF-8 string and the detected encoding.
pub struct DecodeResult {
    pub text: String,
    pub encoding: DetectedEncoding,
}

/// Decode raw bytes to a UTF-8 string, detecting encoding from BOM first,
/// then falling back to the CHAR declaration in the header.
pub fn decode(input: &[u8]) -> DecodeResult {
    // Check for BOM
    if input.len() >= 3 && input[0] == 0xEF && input[1] == 0xBB && input[2] == 0xBF {
        // UTF-8 BOM
        return DecodeResult {
            text: String::from_utf8_lossy(&input[3..]).into_owned(),
            encoding: DetectedEncoding::Utf8,
        };
    }

    if input.len() >= 2 && input[0] == 0xFF && input[1] == 0xFE {
        // UTF-16 LE BOM
        let (text, _, _) = UTF_16LE.decode(&input[2..]);
        return DecodeResult {
            text: text.into_owned(),
            encoding: DetectedEncoding::Utf16Le,
        };
    }

    if input.len() >= 2 && input[0] == 0xFE && input[1] == 0xFF {
        // UTF-16 BE BOM
        let (text, _, _) = UTF_16BE.decode(&input[2..]);
        return DecodeResult {
            text: text.into_owned(),
            encoding: DetectedEncoding::Utf16Be,
        };
    }

    // No BOM: check if it looks like UTF-16 by checking for null bytes
    // in the first few bytes (common in UTF-16 encoded ASCII text)
    if input.len() >= 4 {
        // UTF-16 LE: ASCII chars have pattern [byte, 0x00]
        if input[1] == 0x00 && input[3] == 0x00 {
            let (text, _, _) = UTF_16LE.decode(input);
            return DecodeResult {
                text: text.into_owned(),
                encoding: DetectedEncoding::Utf16Le,
            };
        }
        // UTF-16 BE: ASCII chars have pattern [0x00, byte]
        if input[0] == 0x00 && input[2] == 0x00 {
            let (text, _, _) = UTF_16BE.decode(input);
            return DecodeResult {
                text: text.into_owned(),
                encoding: DetectedEncoding::Utf16Be,
            };
        }
    }

    // Default: treat as UTF-8 (which is a superset of ASCII)
    let text = String::from_utf8_lossy(input).into_owned();

    // Try to detect encoding from CHAR declaration
    let encoding = detect_char_declaration(&text);

    DecodeResult {
        text,
        encoding,
    }
}

/// Look for a CHAR declaration in the first few lines.
fn detect_char_declaration(text: &str) -> DetectedEncoding {
    for line in text.lines().take(20) {
        let trimmed = line.trim();
        if let Some(rest) = trimmed.strip_prefix("1 CHAR ") {
            let charset = rest.trim().to_uppercase();
            return match charset.as_str() {
                "UTF-8" => DetectedEncoding::Utf8,
                "ASCII" => DetectedEncoding::Ascii,
                "ANSEL" => DetectedEncoding::Ansel,
                "UNICODE" => DetectedEncoding::Utf8, // ambiguous; already decoded
                "ANSI" => DetectedEncoding::Ascii,   // treat ANSI as ASCII
                _ => DetectedEncoding::Utf8,
            };
        }
    }
    DetectedEncoding::Utf8
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_utf8_no_bom() {
        let input = b"0 HEAD\n1 CHAR UTF-8\n0 TRLR\n";
        let result = decode(input);
        assert_eq!(result.encoding, DetectedEncoding::Utf8);
        assert!(result.text.contains("HEAD"));
    }

    #[test]
    fn test_utf8_with_bom() {
        let mut input = vec![0xEF, 0xBB, 0xBF];
        input.extend_from_slice(b"0 HEAD\n");
        let result = decode(&input);
        assert_eq!(result.encoding, DetectedEncoding::Utf8);
        assert!(result.text.starts_with("0 HEAD"));
    }

    #[test]
    fn test_ascii_char_declaration() {
        let input = b"0 HEAD\n1 CHAR ASCII\n0 TRLR\n";
        let result = decode(input);
        assert_eq!(result.encoding, DetectedEncoding::Ascii);
    }

    #[test]
    fn test_ansi_treated_as_ascii() {
        let input = b"0 HEAD\n1 CHAR ANSI\n0 TRLR\n";
        let result = decode(input);
        assert_eq!(result.encoding, DetectedEncoding::Ascii);
    }

    #[test]
    fn test_utf16_le_with_bom() {
        // "0 HEAD\n" in UTF-16 LE with BOM
        let mut input = vec![0xFF, 0xFE]; // BOM
        for byte in b"0 HEAD\n" {
            input.push(*byte);
            input.push(0x00);
        }
        let result = decode(&input);
        assert_eq!(result.encoding, DetectedEncoding::Utf16Le);
        assert!(result.text.contains("HEAD"));
    }

    #[test]
    fn test_utf16_le_no_bom() {
        // "0 HEAD\n" in UTF-16 LE without BOM
        let mut input = Vec::new();
        for byte in b"0 HEAD\n" {
            input.push(*byte);
            input.push(0x00);
        }
        let result = decode(&input);
        assert_eq!(result.encoding, DetectedEncoding::Utf16Le);
        assert!(result.text.contains("HEAD"));
    }
}
