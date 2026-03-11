use super::types::{Date, MediaRef, Place, Sex, SourceCitation};

/// A personal name parsed from GEDCOM.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Name {
    /// The full name string (raw from GEDCOM, with surname slashes removed).
    pub full: String,
    /// Given name(s), from GIVN tag or parsed from NAME.
    pub given: Option<String>,
    /// Surname, from SURN tag or parsed from /Surname/ in NAME.
    pub surname: Option<String>,
}

impl Name {
    /// Parse a GEDCOM NAME value like "John /Smith/" into components.
    pub fn from_gedcom(raw: &str) -> Self {
        let (given, surname) = if let Some(slash_start) = raw.find('/') {
            let before = raw[..slash_start].trim();
            let after_start = slash_start + 1;
            let slash_end = raw[after_start..].find('/').map(|p| after_start + p);
            let surname = match slash_end {
                Some(end) => raw[after_start..end].trim(),
                None => raw[after_start..].trim(),
            };
            (
                if before.is_empty() {
                    None
                } else {
                    Some(before.to_string())
                },
                if surname.is_empty() {
                    None
                } else {
                    Some(surname.to_string())
                },
            )
        } else {
            (Some(raw.trim().to_string()), None)
        };

        // Build full name without slashes
        let full = raw.replace('/', "").split_whitespace().collect::<Vec<_>>().join(" ");

        Name {
            full,
            given,
            surname,
        }
    }
}

impl std::fmt::Display for Name {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", self.full)
    }
}

/// An event (birth, death, marriage, etc.) with optional date and place.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Event {
    pub date: Option<Date>,
    pub place: Option<Place>,
}

/// An individual person record.
#[derive(Debug, Clone)]
pub struct Individual {
    /// GEDCOM xref ID, e.g. "@I1@".
    pub xref: String,
    /// Parsed name.
    pub name: Option<Name>,
    /// Sex.
    pub sex: Option<Sex>,
    /// Birth event.
    pub birth: Option<Event>,
    /// Death event.
    pub death: Option<Event>,
    /// Xrefs to FAM records where this person is a spouse.
    pub family_as_spouse: Vec<String>,
    /// Xrefs to FAM records where this person is a child.
    pub family_as_child: Vec<String>,
    /// Multimedia references.
    pub media: Vec<MediaRef>,
    /// Source citations.
    pub source_citations: Vec<SourceCitation>,
}

impl Individual {
    pub fn new(xref: String) -> Self {
        Individual {
            xref,
            name: None,
            sex: None,
            birth: None,
            death: None,
            family_as_spouse: Vec::new(),
            family_as_child: Vec::new(),
            media: Vec::new(),
            source_citations: Vec::new(),
        }
    }

    /// Display name, falling back to xref if unnamed.
    pub fn display_name(&self) -> &str {
        match &self.name {
            Some(name) => &name.full,
            None => &self.xref,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_name_with_surname() {
        let n = Name::from_gedcom("John /Smith/");
        assert_eq!(n.full, "John Smith");
        assert_eq!(n.given, Some("John".to_string()));
        assert_eq!(n.surname, Some("Smith".to_string()));
    }

    #[test]
    fn test_name_with_middle_name() {
        let n = Name::from_gedcom("Robert Eugene /Williams/");
        assert_eq!(n.full, "Robert Eugene Williams");
        assert_eq!(n.given, Some("Robert Eugene".to_string()));
        assert_eq!(n.surname, Some("Williams".to_string()));
    }

    #[test]
    fn test_name_surname_only() {
        let n = Name::from_gedcom("/Black/");
        assert_eq!(n.full, "Black");
        assert_eq!(n.given, None);
        assert_eq!(n.surname, Some("Black".to_string()));
    }

    #[test]
    fn test_name_no_slashes() {
        let n = Name::from_gedcom("Homer Simpson");
        assert_eq!(n.full, "Homer Simpson");
        assert_eq!(n.given, Some("Homer Simpson".to_string()));
        assert_eq!(n.surname, None);
    }

    #[test]
    fn test_name_complex_with_suffix() {
        // Some GEDCOM files put text after the closing slash
        let n = Name::from_gedcom("Windows /2.0/");
        assert_eq!(n.full, "Windows 2.0");
        assert_eq!(n.given, Some("Windows".to_string()));
        assert_eq!(n.surname, Some("2.0".to_string()));
    }
}
