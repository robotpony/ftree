use std::collections::HashMap;

use super::family::Family;
use super::individual::Individual;

/// File header metadata.
#[derive(Debug, Clone, Default)]
pub struct Header {
    /// Source application that produced the file.
    pub source: Option<String>,
    /// GEDCOM version string.
    pub gedcom_version: Option<String>,
    /// GEDCOM form (e.g. "LINEAGE-LINKED").
    pub gedcom_form: Option<String>,
    /// Declared character encoding.
    pub encoding: Option<String>,
}

/// A parsed warning collected during parsing.
#[derive(Debug, Clone)]
pub struct ParseWarning {
    /// Line number where the warning occurred (1-based), if known.
    pub line: Option<usize>,
    /// Warning message.
    pub message: String,
}

impl std::fmt::Display for ParseWarning {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self.line {
            Some(line) => write!(f, "line {}: {}", line, self.message),
            None => write!(f, "{}", self.message),
        }
    }
}

/// The central data structure. All parsers produce one, all renderers consume one.
pub struct FamilyTree {
    pub header: Header,
    pub individuals: HashMap<String, Individual>,
    pub families: HashMap<String, Family>,
    pub warnings: Vec<ParseWarning>,
}

impl FamilyTree {
    pub fn new() -> Self {
        FamilyTree {
            header: Header::default(),
            individuals: HashMap::new(),
            families: HashMap::new(),
            warnings: Vec::new(),
        }
    }
}

impl Default for FamilyTree {
    fn default() -> Self {
        Self::new()
    }
}
