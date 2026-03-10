use super::individual::Event;

/// A family record linking spouses and children.
#[derive(Debug, Clone)]
pub struct Family {
    /// GEDCOM xref ID, e.g. "@F1@".
    pub xref: String,
    /// Xref to husband INDI record.
    pub husband: Option<String>,
    /// Xref to wife INDI record.
    pub wife: Option<String>,
    /// Xrefs to child INDI records.
    pub children: Vec<String>,
    /// Marriage event.
    pub marriage: Option<Event>,
}

impl Family {
    pub fn new(xref: String) -> Self {
        Family {
            xref,
            husband: None,
            wife: None,
            children: Vec::new(),
            marriage: None,
        }
    }
}
