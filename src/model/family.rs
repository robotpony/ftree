use super::individual::Event;
use super::types::NoteRef;

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
    /// Marriage event (MARR).
    pub marriage: Option<Event>,
    /// Divorce event (DIV).
    pub divorce: Option<Event>,
    /// Engagement event (ENGA).
    pub engagement: Option<Event>,
    /// Annulment event (ANUL).
    pub annulment: Option<Event>,
    /// Notes (inline text or pointers to level-0 NOTE records).
    pub notes: Vec<NoteRef>,
}

impl Family {
    pub fn new(xref: String) -> Self {
        Family {
            xref,
            husband: None,
            wife: None,
            children: Vec::new(),
            marriage: None,
            divorce: None,
            engagement: None,
            annulment: None,
            notes: Vec::new(),
        }
    }
}
