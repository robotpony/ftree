use std::fmt;

/// Sex of an individual.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Sex {
    Male,
    Female,
    Unknown,
}

impl fmt::Display for Sex {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Sex::Male => write!(f, "M"),
            Sex::Female => write!(f, "F"),
            Sex::Unknown => write!(f, "U"),
        }
    }
}

/// A GEDCOM date value, preserving the original format.
///
/// GEDCOM dates can be exact, partial, modified (ABT, BEF, AFT, etc.),
/// ranges (BET...AND), periods (FROM...TO), or freeform phrases.
/// We store the raw string and parse what we can.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Date {
    /// The raw date string from the GEDCOM file.
    pub raw: String,
    /// Parsed modifier, if any.
    pub modifier: Option<DateModifier>,
    /// Year, if parseable.
    pub year: Option<i32>,
    /// Month (1-12), if parseable.
    pub month: Option<u8>,
    /// Day (1-31), if parseable.
    pub day: Option<u8>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum DateModifier {
    About,
    Calculated,
    Estimated,
    Before,
    After,
    /// BET date1 AND date2 — stores the second date's raw string.
    Between(String),
    /// FROM date1 TO date2 — stores the second date's raw string.
    FromTo(String),
    From,
    To,
    Interpreted,
    Phrase,
}

impl Date {
    /// Parse a GEDCOM date string.
    pub fn parse(raw: &str) -> Self {
        let raw = raw.trim().to_string();

        // Date phrase: enclosed in parentheses
        if raw.starts_with('(') && raw.ends_with(')') {
            return Date {
                raw,
                modifier: Some(DateModifier::Phrase),
                year: None,
                month: None,
                day: None,
            };
        }

        let upper = raw.to_uppercase();

        // BET...AND range
        if upper.starts_with("BET ") {
            if let Some(and_pos) = upper.find(" AND ") {
                let first_part = &raw[4..and_pos];
                let second_part = raw[and_pos + 5..].to_string();
                let (year, month, day) = parse_date_parts(first_part);
                return Date {
                    raw,
                    modifier: Some(DateModifier::Between(second_part)),
                    year,
                    month,
                    day,
                };
            }
        }

        // FROM...TO period
        if upper.starts_with("FROM ") {
            if let Some(to_pos) = upper.find(" TO ") {
                let first_part = &raw[5..to_pos];
                let second_part = raw[to_pos + 4..].to_string();
                let (year, month, day) = parse_date_parts(first_part);
                return Date {
                    raw,
                    modifier: Some(DateModifier::FromTo(second_part)),
                    year,
                    month,
                    day,
                };
            }
            // FROM without TO
            let date_part = &raw[5..];
            let (year, month, day) = parse_date_parts(date_part);
            return Date {
                raw,
                modifier: Some(DateModifier::From),
                year,
                month,
                day,
            };
        }

        // TO (without FROM)
        if upper.starts_with("TO ") {
            let date_part = &raw[3..];
            let (year, month, day) = parse_date_parts(date_part);
            return Date {
                raw,
                modifier: Some(DateModifier::To),
                year,
                month,
                day,
            };
        }

        // INT interpreted date
        if upper.starts_with("INT ") {
            let date_part = if let Some(paren) = raw.find('(') {
                &raw[4..paren]
            } else {
                &raw[4..]
            };
            let (year, month, day) = parse_date_parts(date_part.trim());
            return Date {
                raw,
                modifier: Some(DateModifier::Interpreted),
                year,
                month,
                day,
            };
        }

        // Simple modifier prefixes
        let (modifier, date_part) = if upper.starts_with("ABT ") {
            (Some(DateModifier::About), &raw[4..])
        } else if upper.starts_with("CAL ") {
            (Some(DateModifier::Calculated), &raw[4..])
        } else if upper.starts_with("EST ") {
            (Some(DateModifier::Estimated), &raw[4..])
        } else if upper.starts_with("BEF ") {
            (Some(DateModifier::Before), &raw[4..])
        } else if upper.starts_with("AFT ") {
            (Some(DateModifier::After), &raw[4..])
        } else {
            (None, raw.as_str())
        };

        let (year, month, day) = parse_date_parts(date_part.trim());
        Date {
            raw,
            modifier,
            year,
            month,
            day,
        }
    }
}

impl fmt::Display for Date {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.raw)
    }
}

/// A place value.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Place {
    pub raw: String,
}

impl Place {
    pub fn new(raw: &str) -> Self {
        Place {
            raw: raw.trim().to_string(),
        }
    }
}

impl fmt::Display for Place {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.raw)
    }
}

/// A multimedia reference.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MediaRef {
    pub file: Option<String>,
}

/// A source record (level-0 SOUR).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Source {
    /// GEDCOM xref ID, e.g. "@S1@".
    pub xref: String,
    /// Descriptive title (TITL).
    pub title: Option<String>,
    /// Author/originator (AUTH).
    pub author: Option<String>,
    /// Publication facts (PUBL).
    pub publisher: Option<String>,
    /// Short filed-by entry (ABBR).
    pub abbreviation: Option<String>,
    /// Text from source (TEXT).
    pub text: Option<String>,
    /// Xref to repository record (REPO pointer).
    pub repository_xref: Option<String>,
}

impl Source {
    pub fn new(xref: String) -> Self {
        Source {
            xref,
            title: None,
            author: None,
            publisher: None,
            abbreviation: None,
            text: None,
            repository_xref: None,
        }
    }

    /// Display title, falling back to abbreviation or xref.
    pub fn display_title(&self) -> &str {
        self.title
            .as_deref()
            .or(self.abbreviation.as_deref())
            .unwrap_or(&self.xref)
    }
}

impl fmt::Display for Source {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.display_title())
    }
}

/// A repository record (level-0 REPO).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Repository {
    /// GEDCOM xref ID, e.g. "@R1@".
    pub xref: String,
    /// Name of the repository (NAME).
    pub name: Option<String>,
}

impl Repository {
    pub fn new(xref: String) -> Self {
        Repository { xref, name: None }
    }
}

impl fmt::Display for Repository {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.name.as_deref().unwrap_or(&self.xref))
    }
}

/// An inline source citation (SOUR @xref@ within INDI/FAM).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SourceCitation {
    /// Xref to the level-0 SOUR record.
    pub source_xref: String,
    /// Page/location within the source (PAGE).
    pub page: Option<String>,
}

/// Parse month abbreviation to 1-12.
fn parse_month(s: &str) -> Option<u8> {
    match s.to_uppercase().as_str() {
        "JAN" => Some(1),
        "FEB" => Some(2),
        "MAR" => Some(3),
        "APR" => Some(4),
        "MAY" => Some(5),
        "JUN" => Some(6),
        "JUL" => Some(7),
        "AUG" => Some(8),
        "SEP" => Some(9),
        "OCT" => Some(10),
        "NOV" => Some(11),
        "DEC" => Some(12),
        _ => None,
    }
}

/// Parse date parts from a string like "1 Jan 1900", "Jan 1900", or "1900".
/// Skips calendar escapes like @#DJULIAN@.
fn parse_date_parts(s: &str) -> (Option<i32>, Option<u8>, Option<u8>) {
    let s = s.trim();

    // Strip calendar escape if present
    let s = if s.starts_with("@#") {
        if let Some(end) = s.find("@ ") {
            s[end + 2..].trim()
        } else {
            s
        }
    } else {
        s
    };

    let parts: Vec<&str> = s.split_whitespace().collect();

    match parts.len() {
        // "1900"
        1 => {
            let year = parts[0].parse::<i32>().ok();
            (year, None, None)
        }
        // "Jan 1900"
        2 => {
            let month = parse_month(parts[0]);
            let year = parts[1].parse::<i32>().ok();
            (year, month, None)
        }
        // "1 Jan 1900"
        3 => {
            let day = parts[0].parse::<u8>().ok();
            let month = parse_month(parts[1]);
            let year = parts[2].parse::<i32>().ok();
            (year, month, day)
        }
        _ => (None, None, None),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_exact_date() {
        let d = Date::parse("1 Jan 1900");
        assert_eq!(d.year, Some(1900));
        assert_eq!(d.month, Some(1));
        assert_eq!(d.day, Some(1));
        assert!(d.modifier.is_none());
    }

    #[test]
    fn test_parse_year_only() {
        let d = Date::parse("1884");
        assert_eq!(d.year, Some(1884));
        assert_eq!(d.month, None);
        assert_eq!(d.day, None);
    }

    #[test]
    fn test_parse_month_year() {
        let d = Date::parse("Dec 1859");
        assert_eq!(d.year, Some(1859));
        assert_eq!(d.month, Some(12));
        assert_eq!(d.day, None);
    }

    #[test]
    fn test_parse_about() {
        let d = Date::parse("ABT 1850");
        assert_eq!(d.modifier, Some(DateModifier::About));
        assert_eq!(d.year, Some(1850));
    }

    #[test]
    fn test_parse_before() {
        let d = Date::parse("BEF 1828");
        assert_eq!(d.modifier, Some(DateModifier::Before));
        assert_eq!(d.year, Some(1828));
    }

    #[test]
    fn test_parse_after() {
        let d = Date::parse("AFT 1776");
        assert_eq!(d.modifier, Some(DateModifier::After));
        assert_eq!(d.year, Some(1776));
    }

    #[test]
    fn test_parse_between() {
        let d = Date::parse("BET 1 JAN 1820 AND 31 DEC 1825");
        assert_eq!(d.modifier, Some(DateModifier::Between("31 DEC 1825".to_string())));
        assert_eq!(d.year, Some(1820));
        assert_eq!(d.month, Some(1));
        assert_eq!(d.day, Some(1));
    }

    #[test]
    fn test_parse_from_to() {
        let d = Date::parse("FROM 1 MAR 1900 TO 15 APR 1900");
        assert_eq!(d.modifier, Some(DateModifier::FromTo("15 APR 1900".to_string())));
        assert_eq!(d.year, Some(1900));
        assert_eq!(d.month, Some(3));
    }

    #[test]
    fn test_parse_from_only() {
        let d = Date::parse("from 1900 to 1905");
        assert_eq!(d.modifier, Some(DateModifier::FromTo("1905".to_string())));
        assert_eq!(d.year, Some(1900));
    }

    #[test]
    fn test_parse_phrase() {
        let d = Date::parse("(Christmas Day)");
        assert_eq!(d.modifier, Some(DateModifier::Phrase));
        assert_eq!(d.year, None);
    }

    #[test]
    fn test_parse_julian_calendar() {
        let d = Date::parse("@#DJULIAN@ 25 DEC 1066");
        assert_eq!(d.year, Some(1066));
        assert_eq!(d.month, Some(12));
        assert_eq!(d.day, Some(25));
    }

    #[test]
    fn test_parse_interpreted() {
        let d = Date::parse("INT 15 JAN 1950 (about the middle of January 1950)");
        assert_eq!(d.modifier, Some(DateModifier::Interpreted));
        assert_eq!(d.year, Some(1950));
        assert_eq!(d.month, Some(1));
        assert_eq!(d.day, Some(15));
    }
}
